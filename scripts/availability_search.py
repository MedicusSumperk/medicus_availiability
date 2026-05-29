"""Targeted availability search for API/tool calls.

This module returns a short list of bookable options instead of a full agent
context export. It is read-only.
"""

from __future__ import annotations

import json
import unicodedata
from datetime import date, datetime, time, timedelta
from typing import Any

from agent_context import (
    DEFAULT_CONFIG,
    LOCAL_CONFIG_PATH,
    build_simple_service_options,
    build_skin_options,
    filter_doctors,
    load_dermatoscope_blockers,
    normalize_config,
    parse_time,
)
from availability_engine import compute_day_availability, load_doctors


DEFAULT_DAYS_AHEAD = 30
DEFAULT_LIMIT = 3
MAX_LIMIT = 10


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
    start_time = parse_time(option["start_time"])
    if time_from is not None and start_time < time_from:
        return False
    if time_to is not None and start_time > time_to:
        return False
    return True


def _filtered_doctors(doctors: list[dict[str, Any]], doctor_id: int | None) -> list[dict[str, Any]]:
    if doctor_id is None:
        return doctors
    return [doctor for doctor in doctors if int(doctor["doctor_id"]) == doctor_id]


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
            return filtered, {"doctor_id": doctor_id, "doctor_name": filtered[0]["doctor_name"], "match_type": "doctor_id"}, notes
        notes.append(f"Doctor ID {doctor_id} was not found; returning general availability.")
        return doctors, {"doctor_id": doctor_id, "doctor_name": doctor_name, "match_type": "not_found"}, notes

    if not doctor_name:
        return doctors, {"doctor_id": None, "doctor_name": None, "match_type": "none"}, notes

    requested = _normalize_name(str(doctor_name))
    if not requested:
        return doctors, {"doctor_id": None, "doctor_name": doctor_name, "match_type": "empty"}, notes

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
            f"Doctor name '{doctor_name}' matched multiple doctors ({match_names}); returning general availability."
        )
        return doctors, {"doctor_id": None, "doctor_name": doctor_name, "match_type": "ambiguous"}, notes

    notes.append(f"Doctor name '{doctor_name}' was not found; returning general availability.")
    return doctors, {"doctor_id": None, "doctor_name": doctor_name, "match_type": "not_found"}, notes


def load_search_config() -> dict[str, Any]:
    """Load the same local rule config used by the agent context builder."""
    if LOCAL_CONFIG_PATH.exists():
        with LOCAL_CONFIG_PATH.open("r", encoding="utf-8-sig") as config_file:
            return normalize_config(json.load(config_file))
    return normalize_config(DEFAULT_CONFIG)


def search_availability(cursor, request: dict[str, Any] | None = None, base_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the first matching service options for a compact tool response."""
    request = request or {}
    config = normalize_config(base_config) if base_config is not None else load_search_config()

    service = str(request.get("service") or "skin").strip().lower()
    if service not in {"skin", "plasma"}:
        raise ValueError("service must be one of: skin, plasma")

    today = date.today()
    date_from = _parse_date(request.get("date_from")) or today
    explicit_date_to = _parse_date(request.get("date_to"))
    days_ahead = int(request.get("days_ahead") or DEFAULT_DAYS_AHEAD)
    date_to = explicit_date_to or (date_from + timedelta(days=days_ahead - 1))

    include_weekends = bool(request.get("include_weekends", False))
    weekdays = {int(value) for value in request.get("weekdays", [])}
    time_from = _parse_time(request.get("time_from"))
    time_to = _parse_time(request.get("time_to"))
    doctor_id = int(request["doctor_id"]) if request.get("doctor_id") is not None else None
    doctor_name = str(request.get("doctor_name") or "").strip() or None
    limit = min(max(int(request.get("limit") or DEFAULT_LIMIT), 1), int(request.get("max_limit") or MAX_LIMIT))

    fallback_slot_interval_minutes = int(config.get("slot_interval_minutes", 15))
    blocking_idcinnosti = [int(value) for value in config.get("dermatoscope_blocking_idcinnosti", [1, 2, 5, 6])]
    services = config.get("services", DEFAULT_CONFIG["services"])
    all_doctors = filter_doctors(load_doctors(cursor), config)
    doctors, doctor_filter, agent_notes = _resolve_doctor_filter(all_doctors, doctor_id, doctor_name)

    options: list[dict[str, Any]] = []
    scanned_days = 0
    scanned_contexts = 0

    for target_date in _iter_dates(date_from, date_to, include_weekends, weekdays):
        scanned_days += 1
        blockers = load_dermatoscope_blockers(cursor, target_date, blocking_idcinnosti)

        for doctor in doctors:
            availability = compute_day_availability(cursor, doctor, target_date)
            if not availability["has_schedule"]:
                continue

            for context in availability.get("contexts", []):
                scanned_contexts += 1
                if service == "skin":
                    context_options, _rejections = build_skin_options(
                        context,
                        blockers,
                        services["skin"],
                        fallback_slot_interval_minutes,
                        limit,
                    )
                else:
                    context_options, _rejections = build_simple_service_options(
                        context,
                        services["plasma"],
                        fallback_slot_interval_minutes,
                        limit,
                    )

                for option in context_options:
                    if not _option_matches_time(option, time_from, time_to):
                        continue
                    options.append(
                        {
                            "date": target_date.isoformat(),
                            "weekday": target_date.strftime("%A"),
                            "service": service,
                            "start_time": option["start_time"],
                            "end_time": option["end_time"],
                            "duration_minutes": option.get("duration_minutes"),
                            "slot_interval_minutes": option.get("slot_interval_minutes"),
                            "doctor_id": doctor["doctor_id"],
                            "doctor_name": doctor["doctor_name"],
                            "idprac": option.get("idprac"),
                            "idcinnosti": option.get("idcinnosti"),
                            "info_marker": option.get("info_marker"),
                            "followup_dermatoscope_slot": option.get("followup_dermatoscope_slot"),
                        }
                    )
                    if len(options) >= limit:
                        return {
                            "ok": True,
                            "service": service,
                            "date_range": {
                                "date_from": date_from.isoformat(),
                                "date_to": date_to.isoformat(),
                            },
                            "filters": {
                                "weekdays": sorted(weekdays),
                                "time_from": time_from.strftime("%H:%M") if time_from else None,
                                "time_to": time_to.strftime("%H:%M") if time_to else None,
                                "doctor": doctor_filter,
                            },
                            "agent_notes": agent_notes,
                            "options": options,
                            "scanned": {
                                "days": scanned_days,
                                "contexts": scanned_contexts,
                            },
                        }

    return {
        "ok": True,
        "service": service,
        "date_range": {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
        "filters": {
            "weekdays": sorted(weekdays),
            "time_from": time_from.strftime("%H:%M") if time_from else None,
            "time_to": time_to.strftime("%H:%M") if time_to else None,
            "doctor": doctor_filter,
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
    return {
        "ok": response["ok"],
        "service": response["service"],
        "filters": response.get("filters", {}),
        "agent_notes": response.get("agent_notes", []),
        "options": [
            {
                "date": option["date"],
                "time": option["start_time"],
                "doctor_name": option["doctor_name"],
            }
            for option in response["options"]
        ],
    }
