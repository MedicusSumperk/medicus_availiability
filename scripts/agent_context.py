"""Build compact pre-call booking context for the AI receptionist.

This module is read-only. It turns raw Medicus availability into service-specific
booking options for the current V1 scope: skin examination and plasma.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from math import ceil
from pathlib import Path
from typing import Any

from availability_engine import compute_day_availability, format_time, load_doctors


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "agent_context.local.example.json"
LOCAL_CONFIG_PATH = PROJECT_ROOT / "config" / "agent_context.local.json"


DEFAULT_CONFIG: dict[str, Any] = {
    "start_date": None,
    "days_ahead": 14,
    "include_weekends": False,
    "include_unscheduled_doctors": False,
    "max_options_per_service_per_doctor_day": 6,
    "slot_interval_minutes": 15,
    "services": {
        "skin": {
            "label": "Kozni vysetreni",
            "appointment_duration_minutes": 15,
            "followup_dermatoscope_minutes": 15,
            "idcinnosti": None,
        },
        "plasma": {
            "label": "Plazma",
            "appointment_duration_minutes": 30,
            "idcinnosti": 3,
            "info_marker": "plazma",
        },
    },
    "dermatoscope_blocking_idcinnosti": [1, 2, 5, 6],
    "allowed_doctor_ids": [],
    "excluded_doctor_ids": [],
    "output_dir": "data/agent_context",
}


def parse_time(value: str) -> time:
    """Parse HH:MM or HH:MM:SS into time."""
    text = value.strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Unsupported time value: {value!r}")


def add_minutes(value: time, minutes: int) -> time:
    """Return a time shifted by minutes on an arbitrary base day."""
    base_day = date(2000, 1, 1)
    return (datetime.combine(base_day, value) + timedelta(minutes=minutes)).time()


def time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def time_interval_overlaps(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    """Return whether two same-day half-open time intervals overlap."""
    return time_to_minutes(start_a) < time_to_minutes(end_b) and time_to_minutes(end_a) > time_to_minutes(start_b)


def normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """Merge a possibly partial config over DEFAULT_CONFIG."""
    merged = DEFAULT_CONFIG.copy()
    if not config:
        return merged

    for key, value in config.items():
        if key == "services" and isinstance(value, dict):
            services = dict(DEFAULT_CONFIG["services"])
            for service_key, service_value in value.items():
                base_service = dict(services.get(service_key, {}))
                base_service.update(service_value)
                services[service_key] = base_service
            merged["services"] = services
        else:
            merged[key] = value
    return merged


def date_window(config: dict[str, Any]) -> list[date]:
    """Return target dates for context generation."""
    start_raw = config.get("start_date")
    if start_raw:
        start_date = date.fromisoformat(str(start_raw))
    else:
        start_date = date.today()

    days_ahead = int(config.get("days_ahead", 14))
    include_weekends = bool(config.get("include_weekends", False))

    days: list[date] = []
    current = start_date
    while len(days) < days_ahead:
        if include_weekends or current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def filter_doctors(doctors: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply optional allow/exclude doctor filters."""
    allowed_ids = {int(value) for value in config.get("allowed_doctor_ids", [])}
    excluded_ids = {int(value) for value in config.get("excluded_doctor_ids", [])}

    filtered: list[dict[str, Any]] = []
    for doctor in doctors:
        doctor_id = int(doctor["doctor_id"])
        if allowed_ids and doctor_id not in allowed_ids:
            continue
        if doctor_id in excluded_ids:
            continue
        filtered.append(doctor)
    return filtered


def load_dermatoscope_blockers(cursor, target_date: date, blocking_idcinnosti: list[int]) -> list[dict[str, Any]]:
    """Load existing appointments that block shared dermatoscope capacity."""
    if not blocking_idcinnosti:
        return []

    placeholders = ", ".join("?" for _ in blocking_idcinnosti)
    cursor.execute(
        f"""
        SELECT IDOBJ, IDUZI, IDPRAC, CAS, CASDO, IDCINNOSTI, INFO
        FROM OBJOBJ
        WHERE DATUM = ?
          AND IDCINNOSTI IN ({placeholders})
        ORDER BY CAS, CASDO, IDUZI, IDOBJ
        """,
        (target_date, *blocking_idcinnosti),
    )

    blockers: list[dict[str, Any]] = []
    for idobj, iduzi, idprac, cas, casdo, idcinnosti, info in cursor.fetchall():
        blockers.append(
            {
                "idobj": int(idobj),
                "doctor_id": int(iduzi) if iduzi is not None else None,
                "idprac": int(idprac) if idprac is not None else None,
                "start_time": cas,
                "end_time": casdo,
                "idcinnosti": int(idcinnosti),
                "info": (info or "").strip(),
            }
        )
    return blockers


def has_required_consecutive_slots(
    free_slots: set[time],
    start_time: time,
    duration_minutes: int,
    slot_interval_minutes: int,
) -> bool:
    """Return whether start_time has enough consecutive free slots."""
    required_slots = ceil(duration_minutes / slot_interval_minutes)
    for slot_index in range(required_slots):
        required_time = add_minutes(start_time, slot_index * slot_interval_minutes)
        if required_time not in free_slots:
            return False
    return True


def dermatoscope_conflict(
    blockers: list[dict[str, Any]],
    follow_start: time,
    follow_end: time,
) -> dict[str, Any] | None:
    """Return the first existing dermatoscope blocker overlapping the follow-up window."""
    for blocker in blockers:
        blocker_start = blocker["start_time"]
        blocker_end = blocker["end_time"]
        if not isinstance(blocker_start, time) or not isinstance(blocker_end, time):
            continue
        if time_interval_overlaps(follow_start, follow_end, blocker_start, blocker_end):
            return {
                "reason": "shared_dermatoscope_conflict",
                "conflicting_idobj": blocker["idobj"],
                "conflicting_doctor_id": blocker["doctor_id"],
                "conflicting_start_time": format_time(blocker_start),
                "conflicting_end_time": format_time(blocker_end),
                "conflicting_idcinnosti": blocker["idcinnosti"],
            }
    return None


def build_skin_options(
    context: dict[str, Any],
    blockers: list[dict[str, Any]],
    service_config: dict[str, Any],
    slot_interval_minutes: int,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build bookable skin options for one doctor/day/context."""
    followup_minutes = int(service_config.get("followup_dermatoscope_minutes", slot_interval_minutes))
    duration_minutes = int(service_config.get("appointment_duration_minutes", slot_interval_minutes))
    free_slots = {parse_time(slot) for slot in context.get("free_slots", [])}

    options: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for start_time in sorted(free_slots):
        if not has_required_consecutive_slots(free_slots, start_time, duration_minutes, slot_interval_minutes):
            rejected.append({"start_time": format_time(start_time), "reason": "skin_slot_not_free_for_duration"})
            continue

        follow_start = add_minutes(start_time, duration_minutes)
        follow_end = add_minutes(follow_start, followup_minutes)
        if follow_start not in free_slots:
            rejected.append({"start_time": format_time(start_time), "reason": "missing_followup_dermatoscope_slot"})
            continue

        blocker = dermatoscope_conflict(blockers, follow_start, follow_end)
        if blocker:
            rejected.append({"start_time": format_time(start_time), **blocker})
            continue

        options.append(
            {
                "start_time": format_time(start_time),
                "end_time": format_time(add_minutes(start_time, duration_minutes)),
                "idprac": context["idprac"],
                "idcinnosti": service_config.get("idcinnosti"),
                "followup_dermatoscope_slot": {
                    "start_time": format_time(follow_start),
                    "end_time": format_time(follow_end),
                    "written_in_v1": False,
                },
            }
        )
        if len(options) >= limit:
            break

    return options, rejected[:limit]


def build_simple_service_options(
    context: dict[str, Any],
    service_config: dict[str, Any],
    slot_interval_minutes: int,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build options for a service needing only consecutive raw-free slots."""
    duration_minutes = int(service_config.get("appointment_duration_minutes", slot_interval_minutes))
    free_slots = {parse_time(slot) for slot in context.get("free_slots", [])}

    options: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for start_time in sorted(free_slots):
        if not has_required_consecutive_slots(free_slots, start_time, duration_minutes, slot_interval_minutes):
            rejected.append({"start_time": format_time(start_time), "reason": "not_enough_consecutive_free_slots"})
            continue

        options.append(
            {
                "start_time": format_time(start_time),
                "end_time": format_time(add_minutes(start_time, duration_minutes)),
                "idprac": context["idprac"],
                "idcinnosti": service_config.get("idcinnosti"),
                "info_marker": service_config.get("info_marker"),
            }
        )
        if len(options) >= limit:
            break

    return options, rejected[:limit]


def build_agent_context(cursor, config: dict[str, Any]) -> dict[str, Any]:
    """Build compact service-specific booking context for the configured date window."""
    config = normalize_config(config)
    days = date_window(config)
    doctors = filter_doctors(load_doctors(cursor), config)
    include_unscheduled_doctors = bool(config.get("include_unscheduled_doctors", False))
    slot_interval_minutes = int(config.get("slot_interval_minutes", 15))
    limit = int(config.get("max_options_per_service_per_doctor_day", 6))
    blocking_idcinnosti = [int(value) for value in config.get("dermatoscope_blocking_idcinnosti", [1, 2, 5, 6])]
    services = config.get("services", DEFAULT_CONFIG["services"])

    result_days: list[dict[str, Any]] = []
    for target_date in days:
        blockers = load_dermatoscope_blockers(cursor, target_date, blocking_idcinnosti)
        day_entry: dict[str, Any] = {
            "date": target_date.isoformat(),
            "weekday": target_date.strftime("%A"),
            "dermatoscope_blocker_count": len(blockers),
            "doctors": [],
        }

        for doctor in doctors:
            availability = compute_day_availability(cursor, doctor, target_date)
            if not availability["has_schedule"] and not include_unscheduled_doctors:
                continue

            doctor_entry: dict[str, Any] = {
                "doctor_id": doctor["doctor_id"],
                "doctor_name": doctor["doctor_name"],
                "has_schedule": availability["has_schedule"],
                "raw_free_slots_count": availability["free_slots_count"],
                "services": {
                    "skin": [],
                    "plasma": [],
                },
                "limited_rejections": {
                    "skin": [],
                    "plasma": [],
                },
            }

            if not availability["has_schedule"]:
                day_entry["doctors"].append(doctor_entry)
                continue

            for context in availability.get("contexts", []):
                skin_options, skin_rejections = build_skin_options(
                    context,
                    blockers,
                    services["skin"],
                    slot_interval_minutes,
                    limit,
                )
                plasma_options, plasma_rejections = build_simple_service_options(
                    context,
                    services["plasma"],
                    slot_interval_minutes,
                    limit,
                )

                doctor_entry["services"]["skin"].extend(skin_options)
                doctor_entry["services"]["plasma"].extend(plasma_options)
                doctor_entry["limited_rejections"]["skin"].extend(skin_rejections)
                doctor_entry["limited_rejections"]["plasma"].extend(plasma_rejections)

            doctor_entry["services"]["skin"] = doctor_entry["services"]["skin"][:limit]
            doctor_entry["services"]["plasma"] = doctor_entry["services"]["plasma"][:limit]
            doctor_entry["limited_rejections"]["skin"] = doctor_entry["limited_rejections"]["skin"][:limit]
            doctor_entry["limited_rejections"]["plasma"] = doctor_entry["limited_rejections"]["plasma"][:limit]

            day_entry["doctors"].append(doctor_entry)

        result_days.append(day_entry)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date_range": {
            "start_date": days[0].isoformat() if days else None,
            "end_date": days[-1].isoformat() if days else None,
            "days_included": [day.isoformat() for day in days],
        },
        "rules_version": "v1-precall-context",
        "rules": {
            "skin": "Book as TYP=1 and IDCINNOSTI=NULL; require immediate free follow-up dermatoscope slot and no shared dermatoscope conflict.",
            "plasma": "Book as TYP=1 and IDCINNOSTI=3 with plasma marker in INFO; requires consecutive free slots for configured duration.",
            "dermatoscope_blockers": blocking_idcinnosti,
        },
        "days": result_days,
    }
