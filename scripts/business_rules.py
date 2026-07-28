"""Business rule config loader for production availability/write behavior."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULES_PATH = PROJECT_ROOT / "config" / "business_rules.example.json"
LOCAL_RULES_PATH = PROJECT_ROOT / "config" / "business_rules.local.json"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as config_file:
        return json.load(config_file)


def load_business_rules(path: str | Path | None = None, *, validate: bool = True) -> dict[str, Any]:
    """Load example rules and overlay local or explicitly supplied rules."""
    if not DEFAULT_RULES_PATH.exists():
        rules: dict[str, Any] = {}
    else:
        rules = _load_json(DEFAULT_RULES_PATH)

    selected_path = Path(path) if path is not None else LOCAL_RULES_PATH
    if selected_path.exists():
        rules = _deep_merge(rules, _load_json(selected_path))

    if validate:
        errors = validate_business_rules(rules)
        if errors:
            raise ValueError("invalid business rules config: " + "; ".join(errors))
    return rules


def _as_int_set(values: Any) -> set[int]:
    if not values:
        return set()
    return {int(value) for value in values}


def known_doctor_ids(rules: dict[str, Any]) -> set[int]:
    return {
        int(doctor["id"])
        for doctor in rules.get("doctors", {}).get("known", [])
        if doctor.get("id") is not None
    }


def validate_business_rules(rules: dict[str, Any]) -> list[str]:
    """Return human-readable validation errors."""
    errors: list[str] = []
    known_ids = known_doctor_ids(rules)
    globally_excluded = _as_int_set(rules.get("doctors", {}).get("globally_excluded_doctor_ids", []))

    for service_key, service in rules.get("services", {}).items():
        if "write" not in service:
            errors.append(f"service {service_key} has no write strategy")

        referenced_ids = _as_int_set(service.get("allowed_doctor_ids", [])) | _as_int_set(
            service.get("excluded_doctor_ids", [])
        )
        unknown = sorted(referenced_ids - known_ids)
        if unknown:
            errors.append(f"service {service_key} references unknown doctor IDs: {unknown}")

        conflict = sorted(_as_int_set(service.get("allowed_doctor_ids", [])) & globally_excluded)
        if conflict:
            errors.append(f"service {service_key} allows globally excluded doctor IDs: {conflict}")

        seasonality = service.get("seasonality", {})
        if seasonality.get("enabled"):
            start = str(seasonality.get("start") or "")
            end = str(seasonality.get("end") or "")
            if not start or not end or start > end:
                errors.append(f"service {service_key} has invalid seasonality range")

    before_time = rules.get("operational_rules", {}).get("before_time_requires_emergency", {})
    if before_time.get("enabled") and not before_time.get("before"):
        errors.append("before_time_requires_emergency.enabled requires before")

    for index, bucket in enumerate(rules.get("operational_rules", {}).get("afternoon_arrival_buckets", [])):
        weekdays = bucket.get("weekdays", [])
        if weekdays:
            try:
                normalized_weekdays = [int(value) for value in weekdays]
            except (TypeError, ValueError):
                errors.append(f"afternoon_arrival_buckets[{index}].weekdays must contain ISO weekday numbers")
                continue
            invalid_weekdays = [value for value in normalized_weekdays if value < 1 or value > 7]
            if invalid_weekdays:
                errors.append(
                    f"afternoon_arrival_buckets[{index}].weekdays must contain ISO weekday numbers 1..7"
                )
        if bucket.get("enabled", True):
            if not bucket.get("time_from") or not bucket.get("time_to"):
                errors.append(f"afternoon_arrival_buckets[{index}] requires time_from and time_to")
            if not bucket.get("spoken_time_label"):
                errors.append(f"afternoon_arrival_buckets[{index}] requires spoken_time_label")

    return errors


def agent_context_overlay(rules: dict[str, Any]) -> dict[str, Any]:
    """Translate production business rules into the existing agent_context config shape."""
    doctors = rules.get("doctors", {})
    overlay: dict[str, Any] = {
        "allowed_doctor_ids": doctors.get("globally_allowed_doctor_ids", []),
        "system_excluded_doctor_ids": doctors.get("globally_excluded_doctor_ids", []),
        "dermatoscope_blocking_idcinnosti": rules.get("shared_resources", {})
        .get("dermatoscope", {})
        .get("blocking_idcinnosti", [1, 2, 5, 6]),
        "services": {},
    }

    for service_key, service in rules.get("services", {}).items():
        duration = service.get("duration", {})
        followup = service.get("followup", {})
        overlay["services"][service_key] = {
            "label": service.get("label", service_key),
            "idcinnosti": service.get("idcinnosti"),
            "info_marker": service.get("info_marker"),
            "use_schedule_interval": duration.get("mode") == "schedule_interval",
            "appointment_duration_minutes": duration.get("minutes"),
            "create_followup_dermatoscope": followup.get("create", False),
            "followup_dermatoscope_minutes": followup.get("duration", {}).get("minutes"),
            "allowed_doctor_ids": service.get("allowed_doctor_ids", []),
            "excluded_doctor_ids": service.get("excluded_doctor_ids", []),
        }
    return overlay


def filter_doctors_for_service(
    doctors: list[dict[str, Any]],
    rules: dict[str, Any],
    service_key: str,
) -> list[dict[str, Any]]:
    service = rules.get("services", {}).get(service_key, {})
    allowed_ids = _as_int_set(service.get("allowed_doctor_ids", []))
    excluded_ids = _as_int_set(service.get("excluded_doctor_ids", []))
    if not allowed_ids and not excluded_ids:
        return doctors

    filtered: list[dict[str, Any]] = []
    for doctor in doctors:
        doctor_id = int(doctor["doctor_id"])
        if allowed_ids and doctor_id not in allowed_ids:
            continue
        if doctor_id in excluded_ids:
            continue
        filtered.append(doctor)
    return filtered


def service_enabled_for_availability(rules: dict[str, Any], service_key: str) -> bool:
    service = rules.get("services", {}).get(service_key, {})
    return bool(service.get("agent_can_offer_availability", True))


def service_enabled_for_booking(rules: dict[str, Any], service_key: str) -> bool:
    service = rules.get("services", {}).get(service_key, {})
    return bool(service.get("agent_can_book_finally", True))


def service_followup_enabled(rules: dict[str, Any], service_key: str) -> bool:
    followup = rules.get("services", {}).get(service_key, {}).get("followup", {})
    return bool(followup.get("create", False))


def agent_capabilities(rules: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return agent-facing service capabilities derived from business rules."""
    rules = rules if rules is not None else load_business_rules()
    bookable_services: list[dict[str, Any]] = []
    handoff_services: list[dict[str, Any]] = []

    for service_key, service in rules.get("services", {}).items():
        service_payload = {
            "key": service_key,
            "label": service.get("label", service_key),
            "agent_can_offer_availability": service_enabled_for_availability(rules, service_key),
            "agent_can_book_finally": service_enabled_for_booking(rules, service_key),
            "followup_enabled": service_followup_enabled(rules, service_key),
            "handoff_reason": "outside_first_production_scope",
        }
        if service_payload["agent_can_offer_availability"] and service_payload["agent_can_book_finally"]:
            bookable_services.append(service_payload)
        else:
            handoff_services.append(service_payload)

    return {
        "ok": True,
        "rules_version": rules.get("version", "unknown"),
        "bookable_services": bookable_services,
        "handoff_services": handoff_services,
        "voice_answer_cs": _capabilities_voice_answer_cs(bookable_services, handoff_services),
    }


def _capabilities_voice_answer_cs(
    bookable_services: list[dict[str, Any]],
    handoff_services: list[dict[str, Any]],
) -> str:
    bookable_labels = [str(service["label"]) for service in bookable_services]
    handoff_labels = [str(service["label"]) for service in handoff_services]
    parts: list[str] = []
    if bookable_labels:
        parts.append("Přímo vám mohu pomoci s objednáním na " + ", ".join(bookable_labels) + ".")
    if handoff_labels:
        parts.append(
            "U dalších služeb, například "
            + ", ".join(handoff_labels[:4])
            + ", požadavek předám personálu."
        )
    return " ".join(parts).strip()


def is_service_in_season(rules: dict[str, Any], service_key: str, month_day: str) -> bool:
    seasonality = rules.get("services", {}).get(service_key, {}).get("seasonality", {})
    if not seasonality.get("enabled"):
        return True
    return str(seasonality.get("start")) <= month_day <= str(seasonality.get("end"))


def before_time_rule(rules: dict[str, Any]) -> dict[str, Any]:
    return rules.get("operational_rules", {}).get("before_time_requires_emergency", {})


def afternoon_bucket_for_time(
    rules: dict[str, Any],
    service_key: str,
    start_time: str,
    weekday_iso: int | None = None,
) -> dict[str, Any] | None:
    for bucket in rules.get("operational_rules", {}).get("afternoon_arrival_buckets", []):
        if not bucket.get("enabled", True):
            continue
        if bucket.get("service") not in (None, "", service_key):
            continue
        weekdays = bucket.get("weekdays", [])
        if weekdays and weekday_iso is not None and weekday_iso not in {int(value) for value in weekdays}:
            continue
        if str(bucket.get("time_from")) <= start_time <= str(bucket.get("time_to")):
            return bucket
    return None
