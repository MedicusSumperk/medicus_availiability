"""Render production business rules JSON into a human-readable Markdown summary."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from business_rules import load_business_rules, validate_business_rules


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "docs" / "current_business_rules.md"


def _list_or_all(values: list[Any] | None) -> str:
    if not values:
        return "all unless excluded"
    return ", ".join(str(value) for value in values)


def _enabled(value: Any) -> str:
    return "enabled" if bool(value) else "disabled"


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
            "| Bucket | Service | Technical time range | Spoken label | Status |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for index, bucket in enumerate(buckets, start=1):
        lines.append(
            f"| {index} | {bucket.get('service', 'all')} | {bucket.get('time_from')} - {bucket.get('time_to')} | {bucket.get('spoken_time_label')} | {_enabled(bucket.get('enabled', True))} |"
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
        if service.get("dermatoscope", {}).get("requires_shared_capacity"):
            lines.append("- Requires shared dermatoscope capacity: `true`")
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
