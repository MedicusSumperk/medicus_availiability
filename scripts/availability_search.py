"""Targeted availability search for API/tool calls.

This module returns a short list of bookable options instead of a full agent
context export. It is read-only.
"""

from __future__ import annotations

import json
from calendar import monthrange
import unicodedata
from contextlib import ExitStack
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from agent_context import (
    DEFAULT_CONFIG,
    LOCAL_CONFIG_PATH,
    build_dermatoscope_options,
    build_simple_service_options,
    build_skin_options,
    filter_doctors,
    load_dermatoscope_blockers,
    normalize_config,
    parse_time,
)
from availability_engine import compute_day_availability, load_doctors
from laser_calendar import open_scan_calendar
from clinic_calendar import is_clinic_workday
from business_rules import (
    afternoon_bucket_for_time,
    agent_context_overlay,
    before_time_rule,
    filter_doctors_for_service,
    is_service_in_season,
    load_business_rules,
    service_enabled_for_availability,
)


DEFAULT_DAYS_AHEAD = 30
DEFAULT_LIMIT = 3
MAX_LIMIT = 10


def _clinic_now() -> datetime:
    return datetime.now(ZoneInfo("Europe/Prague"))


def _search_end_date(start: date, request: dict[str, Any]) -> date:
    """Bound a search by six calendar months from the requested start."""
    month_index = start.year * 12 + start.month - 1 + 6
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    horizon = date(year, month, min(start.day, monthrange(year, month)[1]))
    explicit_end = _parse_date(request.get('date_to'))
    if explicit_end is not None:
        if explicit_end < start:
            raise ValueError('date_to must not precede date_from')
        return min(explicit_end, horizon)
    days = int(request.get('days_ahead') or DEFAULT_DAYS_AHEAD)
    if days < 1:
        raise ValueError('days_ahead must be positive')
    if _parse_bool(request.get('ensure_first_available'), True):
        extended = request.get('max_days_ahead')
        if extended is None:
            return horizon
        extended = int(extended)
        if extended < 1:
            raise ValueError('max_days_ahead must be positive')
        days = max(days, extended)
    # Clamp before date arithmetic to avoid overflow from malformed requests.
    return start + timedelta(days=min(days - 1, (horizon - start).days))


def _option_is_future(option: dict[str, Any], target_date: date, now: datetime) -> bool:
    starts = [option["start_time"], _arrival_time(option)]
    if option.get("scan_slot"):
        starts.append(option["scan_slot"]["start_time"])
    return all(datetime.combine(target_date, parse_time(value), tzinfo=now.tzinfo) > now for value in starts)


def _arrival_time(option: dict[str, Any]) -> str:
    """Earliest required presence, not merely the doctor's technical slot."""
    times = [str(option.get("spoken_time_label") or option["start_time"])]
    if option.get("scan_slot"):
        times.append(str(option["scan_slot"]["start_time"]))
    return min(times, key=parse_time)


def _rank_options(options):
    ranked = sorted(options, key=lambda o: (
        o["date"], parse_time(_arrival_time(o)), parse_time(o["start_time"]),
        int(o["doctor_id"]), int(o["idprac"])))
    seen = set()
    result = []
    for option in ranked:
        key = (option["date"], option["service"], option["doctor_id"], _arrival_time(option))
        if key not in seen:
            seen.add(key)
            result.append(option)
    return result


WEEKDAY_NAMES_CS = {
    1: "pondělí",
    2: "úterý",
    3: "středa",
    4: "čtvrtek",
    5: "pátek",
    6: "sobota",
    7: "neděle",
}


def _parse_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _parse_time(value: str | time | None) -> time | None:
    if value is None or value == "":
        return None
    if isinstance(value, time):
        return value
    return parse_time(str(value))


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _parse_weekdays(value: Any) -> set[int]:
    if value is None or value == "":
        return set()
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, int):
        values = [value]
    else:
        values = value

    try:
        weekdays = {int(str(item).strip()) for item in values if str(item).strip() != ""}
    except (TypeError, ValueError) as error:
        raise ValueError("weekdays must contain ISO weekday numbers 1..7") from error

    invalid = sorted(day for day in weekdays if day < 1 or day > 7)
    if invalid:
        raise ValueError("weekdays must contain ISO weekday numbers 1..7")
    return weekdays


def _effective_weekdays(include_weekends: bool, weekdays: set[int]) -> list[int]:
    if weekdays:
        return sorted(weekdays)
    if include_weekends:
        return [1, 2, 3, 4, 5, 6, 7]
    return [1, 2, 3, 4, 5]


def _weekday_payload(target_date: date) -> dict[str, Any]:
    weekday_iso = target_date.isoweekday()
    return {
        "weekday": target_date.strftime("%A"),
        "weekday_iso": weekday_iso,
        "weekday_cs": WEEKDAY_NAMES_CS[weekday_iso],
    }


def _iter_dates(
    start_date: date,
    end_date: date,
    include_weekends: bool,
    weekdays: set[int],
):
    current = start_date
    while current <= end_date:
        weekday = current.isoweekday()
        if (include_weekends or weekday < 6) and (not weekdays or weekday in weekdays):
            yield current
        current += timedelta(days=1)


def _option_matches_time(option: dict[str, Any], time_from: time | None, time_to: time | None) -> bool:
    start_time = parse_time(_arrival_time(option))
    if time_from is not None and start_time < time_from:
        return False
    if time_to is not None and start_time > time_to:
        return False
    return True


def _filtered_doctors(doctors: list[dict[str, Any]], doctor_id: int | None) -> list[dict[str, Any]]:
    if doctor_id is None:
        return doctors
    return [doctor for doctor in doctors if int(doctor["doctor_id"]) == doctor_id]


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key == "services" and isinstance(value, dict):
            services = dict(merged.get("services", {}))
            for service_key, service_value in value.items():
                service = dict(services.get(service_key, {}))
                service.update(service_value)
                services[service_key] = service
            merged["services"] = services
        else:
            merged[key] = value
    return merged


def _normalize_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.lower())
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    title_words = {"dr", "mudr", "doktor", "doktorka", "pan", "pani"}
    parts = ascii_text.replace(".", " ").replace(",", " ").split()
    return " ".join(part for part in parts if part not in title_words)


def _resolve_doctor_filter(
    doctors: list[dict[str, Any]],
    doctor_id: int | None,
    doctor_name: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    notes: list[str] = []
    if doctor_id is not None:
        filtered = _filtered_doctors(doctors, doctor_id)
        if filtered:
            if doctor_name:
                named, _, _ = _resolve_doctor_filter(doctors, None, doctor_name)
                if len(named) != 1 or int(named[0]["doctor_id"]) != doctor_id:
                    return [], {"doctor_id": doctor_id, "doctor_name": doctor_name, "match_type": "conflict"}, ["Doctor ID and name do not identify the same unique doctor; clarify the request."]
            return filtered, {"doctor_id": doctor_id, "doctor_name": filtered[0]["doctor_name"], "match_type": "doctor_id"}, notes
        notes.append(f"Doctor ID {doctor_id} was not found; no options returned; clarify the requested doctor.")
        return [], {"doctor_id": doctor_id, "doctor_name": doctor_name, "match_type": "not_found"}, notes

    if not doctor_name:
        return doctors, {"doctor_id": None, "doctor_name": None, "match_type": "none"}, notes

    requested = _normalize_name(str(doctor_name))
    if not requested:
        return [], {"doctor_id": None, "doctor_name": doctor_name, "match_type": "empty"}, notes

    exact_matches: list[dict[str, Any]] = []
    partial_matches: list[dict[str, Any]] = []
    requested_parts = set(requested.split())

    for doctor in doctors:
        normalized = _normalize_name(str(doctor["doctor_name"]))
        normalized_parts = set(normalized.split())
        if requested == normalized:
            exact_matches.append(doctor)
        elif requested in normalized or requested_parts.issubset(normalized_parts):
            partial_matches.append(doctor)

    matches = exact_matches or partial_matches
    if len(matches) == 1:
        matched = matches[0]
        return (
            [matched],
            {
                "doctor_id": matched["doctor_id"],
                "doctor_name": matched["doctor_name"],
                "requested_doctor_name": doctor_name,
                "match_type": "exact" if exact_matches else "partial",
            },
            notes,
        )

    if len(matches) > 1:
        match_names = ", ".join(str(match["doctor_name"]) for match in matches[:5])
        notes.append(
            f"Doctor name '{doctor_name}' matched multiple doctors ({match_names}); no options returned; clarify the requested doctor."
        )
        return [], {"doctor_id": None, "doctor_name": doctor_name, "match_type": "ambiguous"}, notes

    notes.append(f"Doctor name '{doctor_name}' was not found; no options returned; clarify the requested doctor.")
    return [], {"doctor_id": None, "doctor_name": doctor_name, "match_type": "not_found"}, notes


def load_search_config() -> dict[str, Any]:
    """Load the same local rule config used by the agent context builder."""
    if LOCAL_CONFIG_PATH.exists():
        with LOCAL_CONFIG_PATH.open("r", encoding="utf-8-sig") as config_file:
            config = normalize_config(json.load(config_file))
    else:
        config = normalize_config(DEFAULT_CONFIG)

    rules = load_business_rules()
    return normalize_config(_merge_config(config, agent_context_overlay(rules)))


def _option_allowed_by_operational_rules(
    option: dict[str, Any],
    service: str,
    rules: dict[str, Any],
    emergency: bool,
) -> bool:
    before_rule = before_time_rule(rules)
    if before_rule.get("enabled"):
        before = _parse_time(before_rule.get("before"))
        if before is not None and parse_time(_arrival_time(option)) < before:
            return False
    return True


def _apply_spoken_time(
    option: dict[str, Any],
    service: str,
    rules: dict[str, Any],
    weekday_iso: int | None = None,
) -> dict[str, Any]:
    start_time = str(option["start_time"])
    bucket = afternoon_bucket_for_time(rules, service, start_time, weekday_iso)
    if not bucket:
        option["spoken_time_label"] = start_time
        option["technical_start_time"] = start_time
        return option

    option["spoken_time_label"] = str(bucket.get("spoken_time_label") or start_time)
    option["technical_start_time"] = start_time
    option["communication_note"] = bucket.get("note")
    return option


def search_availability(cursor, request: dict[str, Any] | None = None, base_config: dict[str, Any] | None = None, *, call_started_at: datetime | None = None) -> dict[str, Any]:
    with ExitStack() as resources:
        return _search_availability(cursor, request, base_config, resources, call_started_at)


def _search_availability(cursor, request, base_config, resources, call_started_at=None):
    """Return the first matching service options for a compact tool response."""
    request = request or {}
    rules = load_business_rules()
    if base_config is not None:
        config = normalize_config(_merge_config(normalize_config(base_config), agent_context_overlay(rules)))
    else:
        config = load_search_config()

    service = str(request.get("service") or "skin").strip().lower()
    services = config.get("services", DEFAULT_CONFIG["services"])
    if service not in services:
        raise ValueError(f"service must be one of: {', '.join(sorted(services))}")
    if not service_enabled_for_availability(rules, service):
        raise ValueError(f"service is not agent-facing for availability: {service}")

    now = _clinic_now()
    call_started_at = call_started_at or now
    if call_started_at.tzinfo is None or call_started_at > now:
        raise ValueError('Invalid trusted call start')
    earliest_arrival = call_started_at + timedelta(hours=1)
    today = now.date()
    date_from = _parse_date(request.get("date_from")) or today
    date_to = _search_end_date(date_from, request)
    effective_days_ahead = (date_to - date_from).days + 1

    # Clinic policy is not caller-overridable, even when a DB schedule exists.
    include_weekends = False
    weekdays = _parse_weekdays(request.get("weekdays", request.get("weekday", [])))
    effective_weekdays = [day for day in _effective_weekdays(False, weekdays) if day < 6]
    time_from = _parse_time(request.get("time_from"))
    time_to = _parse_time(request.get("time_to"))
    exact_start = _parse_time(request.get("technical_start_time"))
    emergency_rule = before_time_rule(rules)
    emergency_flag = str(emergency_rule.get("request_flag") or "emergency")
    emergency = _parse_bool(request.get(emergency_flag), False)
    if emergency:
        return {
            "ok": True,
            "service": service,
            "filters": {"emergency": True},
            "next_action": "handoff_to_staff",
            "reason": "emergency_requires_staff",
            "agent_notes": [
                "Offer immediate transfer to staff. Do not offer or promise an emergency appointment."
            ],
            "options": [],
            "scanned": {"days": 0, "contexts": 0},
        }
    doctor_id = int(request["doctor_id"]) if request.get("doctor_id") is not None else None
    doctor_name = str(request.get("doctor_name") or "").strip() or None
    limit = min(max(int(request.get("limit") or DEFAULT_LIMIT), 1), int(request.get("max_limit") or MAX_LIMIT))

    fallback_slot_interval_minutes = int(config.get("slot_interval_minutes", 15))
    blocking_idcinnosti = [int(value) for value in config.get("dermatoscope_blocking_idcinnosti", [1, 2, 5, 6])]
    all_doctors = filter_doctors(load_doctors(cursor), config)
    service_doctors = filter_doctors_for_service(all_doctors, rules, service)
    doctors, doctor_filter, agent_notes = _resolve_doctor_filter(service_doctors, doctor_id, doctor_name)
    if emergency_rule.get("enabled") and not emergency:
        agent_notes.append(
            f"Arrivals before {emergency_rule.get('before')} are reserved for staff; emergency requests require transfer."
        )

    options: list[dict[str, Any]] = []
    scanned_days = 0
    scanned_contexts = 0
    scan_calendar = None
    context_candidate_limit = limit
    if time_from is not None or time_to is not None or (emergency_rule.get("enabled") and not emergency):
        context_candidate_limit = max(
            limit,
            int(request.get("availability_max_limit") or request.get("max_limit") or MAX_LIMIT),
            50,
        )

    for target_date in _iter_dates(max(date_from, today), date_to, include_weekends, weekdays):
        if not is_clinic_workday(target_date):
            continue
        if not is_service_in_season(rules, service, target_date.strftime("%m-%d")):
            continue
        scanned_days += 1
        blockers = load_dermatoscope_blockers(cursor, target_date, blocking_idcinnosti)

        for doctor in doctors:
            availability = compute_day_availability(cursor, doctor, target_date)
            if not availability["has_schedule"]:
                continue

            for context in availability.get("contexts", []):
                # Filter before builders apply their candidate limit, so earlier
                # times today cannot hide later, still-bookable appointments.
                context = dict(context)
                context["free_slots"] = [slot for slot in context.get("free_slots", [])
                    if datetime.combine(target_date, parse_time(slot), tzinfo=now.tzinfo) > now]
                scanned_contexts += 1
                # Arrival filters and deduplication run after construction.
                # Never let an arbitrary candidate cap hide later valid slots.
                context_candidate_limit = max(limit, len(context.get("free_slots", [])))
                if service == "skin":
                    context_options, _rejections = build_skin_options(
                        context,
                        blockers,
                        services["skin"],
                        fallback_slot_interval_minutes,
                        context_candidate_limit,
                    )
                elif service == "dermatoscope_first":
                    context_options, _rejections = build_dermatoscope_options(
                        context,
                        blockers,
                        services["dermatoscope_first"],
                        fallback_slot_interval_minutes,
                        max(context_candidate_limit, len(context.get('free_slots', []))),
                    )
                else:
                    context_options, _rejections = build_simple_service_options(
                        context,
                        services[service],
                        fallback_slot_interval_minutes,
                        context_candidate_limit,
                    )

                for option in context_options:
                    if exact_start is not None and parse_time(option["start_time"]) != exact_start:
                        continue
                    weekday_payload = _weekday_payload(target_date)
                    option = _apply_spoken_time(option, service, rules, weekday_payload["weekday_iso"])
                    if not _option_is_future(option, target_date, now):
                        continue
                    if datetime.combine(target_date, parse_time(_arrival_time(option)), tzinfo=now.tzinfo) < earliest_arrival:
                        continue
                    if not _option_allowed_by_operational_rules(option, service, rules, emergency):
                        continue
                    if not _option_matches_time(option, time_from, time_to):
                        continue
                    if service == 'dermatoscope_first':
                        if scan_calendar is None:
                            scan_calendar = resources.enter_context(open_scan_calendar())
                        scan = option['scan_slot']
                        if not scan_calendar.is_available(target_date, scan['start_time'], scan['end_time']):
                            continue
                        scan['inferred_from_main_db'] = False
                        scan['verified_in_laser_calendar'] = True
                    options.append(
                        {
                            "date": target_date.isoformat(),
                            **weekday_payload,
                            "service": service,
                            "start_time": option["start_time"],
                            "technical_start_time": option.get("technical_start_time", option["start_time"]),
                            "spoken_time_label": option.get("spoken_time_label", option["start_time"]),
                            "end_time": option["end_time"],
                            "duration_minutes": option.get("duration_minutes"),
                            "slot_interval_minutes": option.get("slot_interval_minutes"),
                            "doctor_id": doctor["doctor_id"],
                            "doctor_name": doctor["doctor_name"],
                            "idprac": option.get("idprac"),
                            "idcinnosti": option.get("idcinnosti"),
                            "info_marker": option.get("info_marker"),
                            "followup_dermatoscope_slot": option.get("followup_dermatoscope_slot"),
                            "scan_slot": option.get("scan_slot"),
                            "communication_note": option.get("communication_note"),
                        }
                    )
        # Rank all doctors/contexts for a day before applying the voice limit.
        options = _rank_options(options)
        if len(options) >= limit:
            break

    options = options[:limit]

    return {
        "ok": True,
        "service": service,
        "date_range": {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "searched_days_ahead": effective_days_ahead,
        },
        "filters": {
            "minimum_arrival_at": earliest_arrival.isoformat(),
            "weekdays": sorted(weekdays),
            "effective_weekdays": effective_weekdays,
            "include_weekends": include_weekends,
            "time_from": time_from.strftime("%H:%M") if time_from else None,
            "time_to": time_to.strftime("%H:%M") if time_to else None,
            "doctor": doctor_filter,
            "emergency": emergency,
        },
        "agent_notes": agent_notes,
        "options": options,
        "scanned": {
            "days": scanned_days,
            "contexts": scanned_contexts,
        },
    }


def compact_options(response: dict[str, Any]) -> dict[str, Any]:
    """Return the smallest shape useful for a voice-agent tool."""
    options = [
        {
            "date": option["date"],
            "weekday": option.get("weekday"),
            "weekday_iso": option.get("weekday_iso"),
            "weekday_cs": option.get("weekday_cs"),
            "time": option.get("spoken_time_label", option["start_time"]),
            "start_time": option["start_time"],
            "technical_start_time": option.get("technical_start_time", option["start_time"]),
            "spoken_time_label": option.get("spoken_time_label", option["start_time"]),
            "arrival_time": _arrival_time(option),
            "scan_start_time": (option.get("scan_slot") or {}).get("start_time"),
            "scan_end_time": (option.get("scan_slot") or {}).get("end_time"),
            "communication_note": option.get("communication_note"),
            "doctor_name": option["doctor_name"],
            **({'offer_token': option['offer_token']} if option.get('offer_token') else {}),
        }
        for option in response["options"]
    ]
    return {
        "ok": response["ok"],
        "service": response["service"],
        "filters": response.get("filters", {}),
        "agent_notes": response.get("agent_notes", []),
        **({"next_action": response["next_action"], "reason": response["reason"]}
           if response.get("next_action") else {}),
        "options": options,
        "options_json": json.dumps(options, ensure_ascii=False, separators=(",", ":")),
    }
