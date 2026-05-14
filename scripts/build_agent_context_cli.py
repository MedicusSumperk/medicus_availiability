"""CLI for building compact pre-call context for the AI receptionist."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))

from agent_context import LOCAL_CONFIG_PATH, DEFAULT_CONFIG, build_agent_context, normalize_config
from db import connect_to_db


OUTPUT_DIR_FALLBACK = PROJECT_ROOT / "data" / "agent_context"


def _load_config() -> dict[str, Any]:
    if LOCAL_CONFIG_PATH.exists():
        with LOCAL_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
        print(f"Loaded config from {LOCAL_CONFIG_PATH}")
        return normalize_config(config)

    print(f"Local config not found, using defaults. Create {LOCAL_CONFIG_PATH} to override.")
    return normalize_config(DEFAULT_CONFIG)


def _service_count(day: dict[str, Any], service_key: str) -> int:
    return sum(len(doctor["services"].get(service_key, [])) for doctor in day["doctors"])


def _write_json(context: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_markdown(context: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Agent Pre-call Context",
        "",
        f"Generated: {context['generated_at']}",
        f"Range: {context['date_range']['start_date']} to {context['date_range']['end_date']}",
        "",
        "## Rules",
        "",
        f"- Skin: {context['rules']['skin']}",
        f"- Plasma: {context['rules']['plasma']}",
        f"- Dermatoscope blockers: {context['rules']['dermatoscope_blockers']}",
        "",
        "## Daily Summary",
        "",
        "| Date | Doctors with schedule | Skin options | Plasma options | Derm blockers |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for day in context["days"]:
        doctors_with_schedule = sum(1 for doctor in day["doctors"] if doctor["has_schedule"])
        lines.append(
            "| "
            f"{day['date']} {day['weekday']} | "
            f"{doctors_with_schedule} | "
            f"{_service_count(day, 'skin')} | "
            f"{_service_count(day, 'plasma')} | "
            f"{day['dermatoscope_blocker_count']} |"
        )

    lines.extend(["", "## First Available Options", ""])
    for day in context["days"]:
        day_lines: list[str] = []
        for doctor in day["doctors"]:
            skin_options = doctor["services"].get("skin", [])
            plasma_options = doctor["services"].get("plasma", [])
            if not skin_options and not plasma_options:
                continue
            skin_text = ", ".join(option["start_time"] for option in skin_options[:3]) or "-"
            plasma_text = ", ".join(option["start_time"] for option in plasma_options[:3]) or "-"
            day_lines.append(
                f"- {doctor['doctor_name']} (IDUZI={doctor['doctor_id']}): "
                f"skin {skin_text}; plasma {plasma_text}"
            )
        if day_lines:
            lines.append(f"### {day['date']} {day['weekday']}")
            lines.extend(day_lines)
            lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_outputs(context: dict[str, Any], config: dict[str, Any]) -> list[Path]:
    output_dir = PROJECT_ROOT / config.get("output_dir", "data/agent_context")
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"agent_context_{timestamp}.json"
    markdown_path = output_dir / f"agent_context_{timestamp}.md"
    latest_json_path = output_dir / "agent_context_latest.json"
    latest_markdown_path = output_dir / "agent_context_latest.md"

    _write_json(context, json_path)
    _write_markdown(context, markdown_path)
    _write_json(context, latest_json_path)
    _write_markdown(context, latest_markdown_path)

    return [json_path, markdown_path, latest_json_path, latest_markdown_path]


def main() -> None:
    connection = None
    try:
        config = _load_config()
        connection = connect_to_db()
        cursor = connection.cursor()

        print("Building read-only pre-call agent context...")
        context = build_agent_context(cursor, config)
        output_paths = _write_outputs(context, config)

        print("\nOutput files:")
        for output_path in output_paths:
            print(f"- {output_path}")

        print("\nSummary:")
        print(f"Days: {len(context['days'])}")
        print(f"Range: {context['date_range']['start_date']} to {context['date_range']['end_date']}")
        print("Done. No database writes were performed.")

    except Exception as error:  # noqa: BLE001
        print(f"Agent context build failed: {error}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
