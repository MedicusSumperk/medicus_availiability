"""Interactive CLI for weekly read-only availability across all doctors."""

from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from availability_engine import compute_week_availability
from db import connect_to_db


DATE_FORMAT = "%Y-%m-%d"
PROJECT_ROOT = CURRENT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "availability"


def _week_start(day: date) -> date:
    """Return Monday for the week containing day."""
    return day - timedelta(days=day.weekday())


def _format_week_label(start_date: date, end_date: date) -> str:
    iso_year, iso_week, _ = start_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d} ({start_date.isoformat()} to {end_date.isoformat()})"


def _select_week() -> tuple[date, date]:
    """Prompt user to select a Monday-Friday week window."""
    current_week_start = _week_start(date.today())
    options = []
    for offset in range(3):
        start_date = current_week_start + timedelta(weeks=offset)
        end_date = start_date + timedelta(days=4)
        options.append((start_date, end_date))

    print("Select week for availability check:")
    for index, (start_date, end_date) in enumerate(options, start=1):
        print(f"{index}. {_format_week_label(start_date, end_date)}")
    print("4. More - enter any date in the target week")

    while True:
        raw_value = input("Choose option: ").strip()
        if raw_value in {"1", "2", "3"}:
            return options[int(raw_value) - 1]

        if raw_value == "4":
            while True:
                raw_date = input("Enter date in target week (YYYY-MM-DD): ").strip()
                try:
                    selected_day = datetime.strptime(raw_date, DATE_FORMAT).date()
                    start_date = _week_start(selected_day)
                    return start_date, start_date + timedelta(days=4)
                except ValueError:
                    print("Invalid date format. Use YYYY-MM-DD.")

        print("Invalid option. Choose 1, 2, 3, or 4.")


def _iso_week_slug(week_start: date) -> str:
    iso_year, iso_week, _ = week_start.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _print_console_summary(result: dict[str, Any]) -> None:
    """Print a readable weekly availability summary."""
    print("\nWeekly availability")
    print(f"Week: {result['week_start']} to {result['week_end']} (Monday-Friday)")
    print(f"Doctors: {result['doctor_count']}")

    for doctor in result["doctors"]:
        print("\n" + "=" * 80)
        print(
            f"{doctor['doctor_name']} (IDUZI={doctor['doctor_id']}) - "
            f"free {doctor['free_slots_count']} / total {doctor['total_slots']}"
        )

        for day in doctor["days"]:
            if not day["has_schedule"]:
                print(f"  {day['date']} {day['weekday']}: no schedule")
                continue

            if day["free_slots"]:
                print(
                    f"  {day['date']} {day['weekday']}: "
                    f"{day['free_slots_count']} free - {', '.join(day['free_slots'])}"
                )
            else:
                print(
                    f"  {day['date']} {day['weekday']}: "
                    f"0 free / {day['total_slots']} total"
                )


def _write_json(result: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(result: dict[str, Any], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "week_start",
                "week_end",
                "doctor_id",
                "doctor_name",
                "date",
                "weekday",
                "has_schedule",
                "idprac",
                "typtyd",
                "dentyd",
                "total_slots",
                "occupied_slots_count",
                "free_slots_count",
                "free_slots",
            ]
        )

        for doctor in result["doctors"]:
            for day in doctor["days"]:
                if day["contexts"]:
                    for context in day["contexts"]:
                        writer.writerow(
                            [
                                result["week_start"],
                                result["week_end"],
                                doctor["doctor_id"],
                                doctor["doctor_name"],
                                day["date"],
                                day["weekday"],
                                day["has_schedule"],
                                context["idprac"],
                                context["typtyd"],
                                context["dentyd"],
                                context["total_slots"],
                                context["occupied_slots_count"],
                                context["free_slots_count"],
                                ", ".join(context["free_slots"]),
                            ]
                        )
                else:
                    writer.writerow(
                        [
                            result["week_start"],
                            result["week_end"],
                            doctor["doctor_id"],
                            doctor["doctor_name"],
                            day["date"],
                            day["weekday"],
                            day["has_schedule"],
                            "",
                            "",
                            "",
                            day["total_slots"],
                            day["occupied_slots_count"],
                            day["free_slots_count"],
                            "",
                        ]
                    )


def _write_markdown(result: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Weekly Availability Report",
        "",
        f"Week: {result['week_start']} to {result['week_end']} (Monday-Friday)",
        "",
        "| Doctor | Date | Status | Free slots |",
        "| --- | --- | --- | --- |",
    ]

    for doctor in result["doctors"]:
        doctor_label = f"{doctor['doctor_name']} (IDUZI={doctor['doctor_id']})"
        for day in doctor["days"]:
            date_label = f"{day['date']} {day['weekday']}"
            if not day["has_schedule"]:
                status = "No schedule"
                free_slots = ""
            elif day["free_slots"]:
                status = f"{day['free_slots_count']} free / {day['total_slots']} total"
                free_slots = ", ".join(day["free_slots"])
            else:
                status = f"0 free / {day['total_slots']} total"
                free_slots = ""

            lines.append(f"| {doctor_label} | {date_label} | {status} | {free_slots} |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_outputs(result: dict[str, Any], week_start: date) -> list[Path]:
    """Write JSON, CSV, and Markdown reports to data/availability."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = _iso_week_slug(week_start)

    json_path = OUTPUT_DIR / f"availability_{slug}.json"
    csv_path = OUTPUT_DIR / f"availability_{slug}.csv"
    markdown_path = OUTPUT_DIR / f"availability_{slug}.md"

    _write_json(result, json_path)
    _write_csv(result, csv_path)
    _write_markdown(result, markdown_path)

    return [json_path, csv_path, markdown_path]


def main() -> None:
    """Run weekly availability lookup for all doctors."""
    connection = None

    try:
        week_start, week_end = _select_week()
        connection = connect_to_db()
        cursor = connection.cursor()

        print("\nComputing read-only availability for all doctors...")
        result = compute_week_availability(cursor, week_start, week_end)

        _print_console_summary(result)
        output_paths = _write_outputs(result, week_start)

        print("\nOutput files:")
        for output_path in output_paths:
            print(f"- {output_path}")

    except Exception as error:  # noqa: BLE001
        print(f"Error: {error}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
