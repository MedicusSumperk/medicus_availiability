"""Render production business rules JSON into a human-readable Markdown summary."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from business_rules import load_business_rules, validate_business_rules


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "docs" / "current_business_rules.md"


def _list_or_all(values: list[Any] | None) -> str:
    if not values:
        return "all unless excluded"
    return ", ".join(str(value) for value in values)


def _enabled(value: Any) -> str:
    return "enabled" if bool(value) else "disabled"


def _markdown_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _cell(value: Any) -> str:
    return _markdown_value(value).replace("|", "\\|").replace("\n", " ")


def _rule_matrix_rows(rules: dict[str, Any]) -> list[tuple[str, str, Any, str]]:
    rows: list[tuple[str, str, Any, str]] = []
    rows.extend(
        [
            (
                "Globally allowed doctors",
                "doctors.globally_allowed_doctor_ids",
                rules.get("doctors", {}).get("globally_allowed_doctor_ids", []),
                "Empty means all known doctors are allowed unless excluded.",
            ),
            (
                "Globally excluded doctors",
                "doctors.globally_excluded_doctor_ids",
                rules.get("doctors", {}).get("globally_excluded_doctor_ids", []),
                "These IDUZI values are never offered by availability.",
            ),
            (
                "Shared dermatoscope blockers",
                "shared_resources.dermatoscope.blocking_idcinnosti",
                rules.get("shared_resources", {}).get("dermatoscope", {}).get("blocking_idcinnosti", []),
                "Appointments with these IDCINNOSTI values block shared dermatoscope capacity.",
            ),
            (
                "Shared dermatoscope capacity",
                "shared_resources.dermatoscope.capacity",
                rules.get("shared_resources", {}).get("dermatoscope", {}).get("capacity", 1),
                "Current production assumption is one shared dermatoscope.",
            ),
        ]
    )

    before = rules.get("operational_rules", {}).get("before_time_requires_emergency", {})
    rows.extend(
        [
            (
                "Before-time emergency gate enabled",
                "operational_rules.before_time_requires_emergency.enabled",
                before.get("enabled"),
                "If true, ordinary availability hides slots before the configured time.",
            ),
            (
                "Before-time emergency cutoff",
                "operational_rules.before_time_requires_emergency.before",
                before.get("before"),
                "Slots before this time require the emergency request flag.",
            ),
            (
                "Emergency request flag",
                "operational_rules.before_time_requires_emergency.request_flag",
                before.get("request_flag", "emergency"),
                "The availability request field that unlocks emergency-only slots.",
            ),
        ]
    )

    for index, bucket in enumerate(rules.get("operational_rules", {}).get("afternoon_arrival_buckets", [])):
        prefix = f"operational_rules.afternoon_arrival_buckets[{index}]"
        rows.extend(
            [
                (
                    f"Afternoon bucket {index + 1} enabled",
                    f"{prefix}.enabled",
                    bucket.get("enabled", True),
                    "If enabled, matching technical slots get a separate spoken time label.",
                ),
                (
                    f"Afternoon bucket {index + 1} service",
                    f"{prefix}.service",
                    bucket.get("service"),
                    "Only this service uses the bucket; empty would mean all services.",
                ),
                (
                    f"Afternoon bucket {index + 1} weekdays",
                    f"{prefix}.weekdays",
                    bucket.get("weekdays", []),
                    "Empty means every weekday; otherwise ISO weekdays 1=Monday through 7=Sunday.",
                ),
                (
                    f"Afternoon bucket {index + 1} technical range",
                    f"{prefix}.time_from / {prefix}.time_to",
                    f"{bucket.get('time_from')} - {bucket.get('time_to')}",
                    "Technical start_time values in this range are still used for write.",
                ),
                (
                    f"Afternoon bucket {index + 1} spoken label",
                    f"{prefix}.spoken_time_label",
                    bucket.get("spoken_time_label"),
                    "This is the time the agent should say to the caller.",
                ),
            ]
        )

    for service_key, service in rules.get("services", {}).items():
        prefix = f"services.{service_key}"
        rows.extend(
            [
                (
                    f"{service_key}: agent may offer availability",
                    f"{prefix}.agent_can_offer_availability",
                    service.get("agent_can_offer_availability", True),
                    "If false, the service is not accepted by doctor_availability.",
                ),
                (
                    f"{service_key}: agent may book",
                    f"{prefix}.agent_can_book_finally",
                    service.get("agent_can_book_finally", True),
                    "If false, appointment_write rejects this service.",
                ),
                (
                    f"{service_key}: main IDCINNOSTI",
                    f"{prefix}.idcinnosti",
                    service.get("idcinnosti"),
                    "Value written into the main appointment row; null means default skin row.",
                ),
                (
                    f"{service_key}: duration mode",
                    f"{prefix}.duration.mode",
                    service.get("duration", {}).get("mode"),
                    "schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes.",
                ),
                (
                    f"{service_key}: duration minutes",
                    f"{prefix}.duration.minutes",
                    service.get("duration", {}).get("minutes"),
                    "Used only when duration mode needs a fixed minute value.",
                ),
                (
                    f"{service_key}: allowed doctors",
                    f"{prefix}.allowed_doctor_ids",
                    service.get("allowed_doctor_ids", []),
                    "Empty means all globally allowed doctors unless service-excluded.",
                ),
                (
                    f"{service_key}: excluded doctors",
                    f"{prefix}.excluded_doctor_ids",
                    service.get("excluded_doctor_ids", []),
                    "Doctor IDs excluded only for this service.",
                ),
                (
                    f"{service_key}: seasonality enabled",
                    f"{prefix}.seasonality.enabled",
                    service.get("seasonality", {}).get("enabled"),
                    "If true, availability outside the date range is hidden.",
                ),
                (
                    f"{service_key}: seasonality range",
                    f"{prefix}.seasonality.start / {prefix}.seasonality.end",
                    f"{service.get('seasonality', {}).get('start')} - {service.get('seasonality', {}).get('end')}",
                    "Month-day range when the service is bookable.",
                ),
                (
                    f"{service_key}: write strategy",
                    f"{prefix}.write.strategy",
                    service.get("write", {}).get("strategy"),
                    "Controls whether write creates one row or related rows.",
                ),
            ]
        )
        followup = service.get("followup", {})
        if followup:
            rows.extend(
                [
                    (
                        f"{service_key}: follow-up enabled",
                        f"{prefix}.followup.create",
                        followup.get("create", False),
                        "If true, write creates a related follow-up row.",
                    ),
                    (
                        f"{service_key}: follow-up IDCINNOSTI",
                        f"{prefix}.followup.idcinnosti",
                        followup.get("idcinnosti"),
                        "IDCINNOSTI written into the related follow-up row.",
                    ),
                    (
                        f"{service_key}: follow-up duration mode",
                        f"{prefix}.followup.duration.mode",
                        followup.get("duration", {}).get("mode"),
                        "How the follow-up duration is computed.",
                    ),
                ]
            )
        dermatoscope = service.get("dermatoscope", {})
        if dermatoscope:
            rows.append(
                (
                    f"{service_key}: requires scan capacity",
                    f"{prefix}.dermatoscope.requires_shared_capacity",
                    dermatoscope.get("requires_shared_capacity", False),
                    "If true, availability checks the shared scan room before offering this service.",
                )
            )
            if "scan_before_minutes" in dermatoscope:
                rows.extend(
                    [
                    (
                        f"{service_key}: scan before minutes",
                        f"{prefix}.dermatoscope.scan_before_minutes",
                        dermatoscope.get("scan_before_minutes"),
                        "Minutes before the doctor appointment when the patient should arrive for scan.",
                    ),
                    (
                        f"{service_key}: scan duration minutes",
                        f"{prefix}.dermatoscope.scan_duration_minutes",
                        dermatoscope.get("scan_duration_minutes"),
                        "Shared scan room duration used for conflict checks.",
                    ),
                ]
            )
    return rows


def _change_action(config_path: str) -> str:
    if "globally_allowed_doctor_ids" in config_path:
        return "Add IDs to restrict all services to a fixed global allow-list; leave empty to allow all non-excluded doctors."
    if "globally_excluded_doctor_ids" in config_path:
        return "Add or remove IDUZI values to globally hide or restore doctors for every backend rule."
    if "blocking_idcinnosti" in config_path:
        return "Add IDCINNOSTI values that consume dermatoscope capacity; remove values only after DB/client confirmation."
    if "dermatoscope.capacity" in config_path:
        return "Change only if the clinic has more or fewer shared dermatoscope devices."
    if "before_time_requires_emergency.enabled" in config_path:
        return "Set false to return early slots normally; keep true for production emergency-only behavior."
    if "before_time_requires_emergency.before" in config_path:
        return "Edit the HH:MM cutoff; availability before that time requires the emergency flag."
    if "before_time_requires_emergency.request_flag" in config_path:
        return "Rename only if the API/tool request field is changed at the same time."
    if "afternoon_arrival_buckets" in config_path and ".enabled" in config_path:
        return "Set false to disable this spoken-time bucket without deleting it."
    if "afternoon_arrival_buckets" in config_path and ".service" in config_path:
        return "Change the service key or leave empty/null to apply this bucket to all services."
    if "afternoon_arrival_buckets" in config_path and ".weekdays" in config_path:
        return "Use ISO weekdays, e.g. [1,2,3] for Monday-Wednesday; leave empty for all days."
    if "afternoon_arrival_buckets" in config_path and "time_from" in config_path:
        return "Edit the technical slot range; writes still use the exact technical start_time."
    if "afternoon_arrival_buckets" in config_path and "spoken_time_label" in config_path:
        return "Edit what the agent should say to the caller for matching technical slots."
    if ".agent_can_offer_availability" in config_path:
        return "Set false to make doctor_availability reject this service."
    if ".agent_can_book_finally" in config_path:
        return "Set false to make appointment_write reject final booking for this service."
    if ".idcinnosti" in config_path:
        return "Change only after confirming the Medicus IDCINNOSTI mapping and write shape."
    if ".duration.mode" in config_path:
        return "Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes."
    if ".duration.minutes" in config_path:
        return "Set the fixed duration in minutes; ignored when mode follows schedule_interval."
    if ".allowed_doctor_ids" in config_path:
        return "Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors."
    if ".excluded_doctor_ids" in config_path:
        return "Add IDs to block doctors only for this service."
    if ".seasonality.enabled" in config_path:
        return "Set true to enforce the configured month-day range."
    if ".seasonality.start" in config_path:
        return "Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability."
    if ".write.strategy" in config_path:
        return "Change only with matching appointment_write implementation and tests."
    if ".followup.create" in config_path:
        return "Set false to stop creating related follow-up rows for this service."
    if ".followup.idcinnosti" in config_path:
        return "Change the related row IDCINNOSTI only after confirming Medicus mapping."
    if ".followup.duration.mode" in config_path:
        return "Keep aligned with follow-up capacity rules and appointment_write behavior."
    return "Edit this config value, regenerate docs/current_business_rules.md, and run the relevant tests."


def render_business_rules(rules: dict[str, Any]) -> str:
    errors = validate_business_rules(rules)
    lines: list[str] = [
        "# Current Business Rules",
        "",
        "<!-- Generated from config/business_rules*.json. Do not edit by hand. -->",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Rules version: `{rules.get('version', 'unknown')}`",
        "",
        "## Validation",
        "",
    ]

    if errors:
        lines.extend([f"- ERROR: {error}" for error in errors])
    else:
        lines.append("- OK: config is structurally valid.")

    lines.extend(
        [
            "",
            "## Rule Matrix",
            "",
            "| Rule | Config path | Current value | Effect | How to change |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for description, config_path, value, effect in _rule_matrix_rows(rules):
        lines.append(
            f"| {_cell(description)} | `{_cell(config_path)}` | `{_cell(value)}` | {_cell(effect)} | {_cell(_change_action(config_path))} |"
        )

    doctors = rules.get("doctors", {})
    lines.extend(
        [
            "",
            "## Doctors",
            "",
            f"- Globally allowed doctor IDs: `{_list_or_all(doctors.get('globally_allowed_doctor_ids'))}`",
            f"- Globally excluded doctor IDs: `{_list_or_all(doctors.get('globally_excluded_doctor_ids'))}`",
            "",
            "| IDUZI | Name | Status | Note |",
            "| --- | --- | --- | --- |",
        ]
    )
    for doctor in doctors.get("known", []):
        lines.append(
            f"| {doctor.get('id')} | {doctor.get('name', '')} | {doctor.get('status', '')} | {doctor.get('note', '')} |"
        )

    shared = rules.get("shared_resources", {}).get("dermatoscope", {})
    before = rules.get("operational_rules", {}).get("before_time_requires_emergency", {})
    buckets = rules.get("operational_rules", {}).get("afternoon_arrival_buckets", [])
    lines.extend(
        [
            "",
            "## Operational Rules",
            "",
            f"- Dermatoscope blocking IDCINNOSTI: `{_list_or_all(shared.get('blocking_idcinnosti'))}`",
            f"- Dermatoscope shared capacity: `{shared.get('capacity', 1)}`",
            f"- Before-time emergency gate: `{_enabled(before.get('enabled'))}` before `{before.get('before')}` using request flag `{before.get('request_flag', 'emergency')}`",
            "",
            "| Bucket | Service | Weekdays | Technical time range | Spoken label | Status |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for index, bucket in enumerate(buckets, start=1):
        lines.append(
            f"| {index} | {bucket.get('service', 'all')} | {_list_or_all(bucket.get('weekdays'))} | {bucket.get('time_from')} - {bucket.get('time_to')} | {bucket.get('spoken_time_label')} | {_enabled(bucket.get('enabled', True))} |"
        )

    lines.extend(["", "## Services", ""])
    for service_key, service in rules.get("services", {}).items():
        duration = service.get("duration", {})
        followup = service.get("followup", {})
        seasonality = service.get("seasonality", {})
        lines.extend(
            [
                f"### {service_key}",
                "",
                f"- Label: {service.get('label', service_key)}",
                f"- Agent may offer availability: `{bool(service.get('agent_can_offer_availability', True))}`",
                f"- Agent may book finally: `{bool(service.get('agent_can_book_finally', True))}`",
                f"- Main IDCINNOSTI: `{service.get('idcinnosti')}`",
                f"- Duration: `{duration.get('mode')}`"
                + (f" / `{duration.get('minutes')}` minutes" if duration.get("minutes") else ""),
                f"- Allowed doctor IDs: `{_list_or_all(service.get('allowed_doctor_ids'))}`",
                f"- Excluded doctor IDs: `{_list_or_all(service.get('excluded_doctor_ids'))}`",
                f"- Seasonality: `{_enabled(seasonality.get('enabled'))}` `{seasonality.get('start')}` to `{seasonality.get('end')}`",
                f"- Write strategy: `{service.get('write', {}).get('strategy')}`",
            ]
        )
        if followup.get("create"):
            followup_duration = followup.get("duration", {})
            lines.extend(
                [
                    f"- Follow-up: `{followup.get('kind')}` with IDCINNOSTI `{followup.get('idcinnosti')}`",
                    f"- Follow-up duration: `{followup_duration.get('mode')}`"
                    + (
                        f" / `{followup_duration.get('minutes')}` minutes"
                        if followup_duration.get("minutes")
                        else ""
                    ),
                ]
            )
        dermatoscope = service.get("dermatoscope", {})
        if dermatoscope:
            lines.append(
                f"- Requires shared scan capacity: `{bool(dermatoscope.get('requires_shared_capacity'))}`"
            )
            if dermatoscope.get("scan_before_minutes"):
                lines.append(
                    f"- Scan timing: `{dermatoscope.get('scan_duration_minutes')}` minutes, starts `{dermatoscope.get('scan_before_minutes')}` minutes before doctor time"
                )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Optional business rules JSON file to overlay on the example config.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Markdown output path.")
    parser.add_argument("--check", action="store_true", help="Validate only; do not write Markdown.")
    args = parser.parse_args()

    rules = load_business_rules(args.config, validate=False)
    errors = validate_business_rules(rules)
    if args.check:
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("OK: business rules config is valid.")
        return 0

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_business_rules(rules), encoding="utf-8")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
