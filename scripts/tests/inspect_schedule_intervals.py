"""Read-only diagnostic for doctor schedule slot intervals.

Use this to verify whether a doctor has 10-minute or 15-minute schedule blocks
and to identify doctors with mixed or unexpected schedule intervals.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from availability_engine import (  # noqa: E402
    find_schedule_contexts,
    format_time,
    load_doctors,
    load_schedule_blocks,
    schedule_interval_values,
    to_time,
)
from db import connect_to_db  # noqa: E402


DATE_FORMAT = "%Y-%m-%d"


def _read_date(prompt: str, default: date) -> date:
    raw_value = input(f"{prompt} [{default.isoformat()}]: ").strip()
    if not raw_value:
        return default
    return datetime.strptime(raw_value, DATE_FORMAT).date()


def _read_int(prompt: str, default: int) -> int:
    raw_value = input(f"{prompt} [{default}]: ").strip()
    if not raw_value:
        return default
    return int(raw_value)


def _interval_label(values: list[int]) -> str:
    return ",".join(str(value) for value in values) if values else "unknown"


def _first_start(schedule_blocks) -> str:
    starts = [to_time(row[0]) for row in schedule_blocks if row[0] is not None]
    if not starts:
        return ""
    return format_time(min(starts))


def _total_minutes(schedule_blocks) -> int:
    return sum(int(row[1]) for row in schedule_blocks if row[1] is not None)


def _print_section(title: str) -> None:
    print("\n" + "=" * 120)
    print(title)
    print("=" * 120)


def _print_rows(headers: list[str], rows: list[list[Any]]) -> None:
    print(" | ".join(headers))
    print("-" * 120)
    for row in rows:
        print(" | ".join("" if value is None else str(value) for value in row))


def _collect_rows(cursor, start_date: date, days: int) -> list[dict[str, Any]]:
    doctors = load_doctors(cursor)
    rows: list[dict[str, Any]] = []

    for offset in range(days):
        target_date = start_date + timedelta(days=offset)
        for doctor in doctors:
            doctor_id = int(doctor["doctor_id"])
            contexts = find_schedule_contexts(cursor, doctor_id, target_date)
            for context in contexts:
                idprac = int(context["idprac"])
                typtyd = int(context["typtyd"])
                dentyd = int(context["dentyd"])
                schedule_blocks = load_schedule_blocks(cursor, target_date, typtyd, dentyd, idprac, doctor_id)
                interval_values = schedule_interval_values(schedule_blocks)
                if not schedule_blocks:
                    continue
                rows.append(
                    {
                        "date": target_date.isoformat(),
                        "weekday": target_date.strftime("%A"),
                        "doctor_id": doctor_id,
                        "doctor_name": doctor["doctor_name"],
                        "idprac": idprac,
                        "typtyd": typtyd,
                        "dentyd": dentyd,
                        "intervals": interval_values,
                        "schedule_block_count": len(schedule_blocks),
                        "total_minutes": _total_minutes(schedule_blocks),
                        "first_start": _first_start(schedule_blocks),
                    }
                )

    return rows


def _print_summary(rows: list[dict[str, Any]]) -> None:
    _print_section("Summary by doctor and interval")
    grouped: dict[tuple[int, str, str], dict[str, Any]] = defaultdict(
        lambda: {"days": 0, "contexts": 0, "idprac": set(), "first_date": None, "last_date": None}
    )

    for row in rows:
        label = _interval_label(row["intervals"])
        key = (row["doctor_id"], row["doctor_name"], label)
        group = grouped[key]
        group["contexts"] += 1
        group["idprac"].add(row["idprac"])
        group["first_date"] = row["date"] if group["first_date"] is None else min(group["first_date"], row["date"])
        group["last_date"] = row["date"] if group["last_date"] is None else max(group["last_date"], row["date"])

    seen_days: dict[tuple[int, str, str], set[str]] = defaultdict(set)
    for row in rows:
        seen_days[(row["doctor_id"], row["doctor_name"], _interval_label(row["intervals"]))].add(row["date"])

    printable_rows: list[list[Any]] = []
    for key, group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][2])):
        doctor_id, doctor_name, interval_label = key
        printable_rows.append(
            [
                doctor_id,
                doctor_name,
                interval_label,
                len(seen_days[key]),
                group["contexts"],
                ",".join(str(value) for value in sorted(group["idprac"])),
                group["first_date"],
                group["last_date"],
            ]
        )

    _print_rows(
        ["IDUZI", "doctor", "interval_min", "days", "contexts", "IDPRAC", "first_date", "last_date"],
        printable_rows,
    )


def _print_detail(rows: list[dict[str, Any]]) -> None:
    _print_section("Context detail")
    printable_rows = [
        [
            row["date"],
            row["weekday"],
            row["doctor_id"],
            row["doctor_name"],
            row["idprac"],
            row["typtyd"],
            row["dentyd"],
            _interval_label(row["intervals"]),
            row["schedule_block_count"],
            row["total_minutes"],
            row["first_start"],
        ]
        for row in rows
    ]
    _print_rows(
        ["date", "weekday", "IDUZI", "doctor", "IDPRAC", "TYPTYD", "DENTYD", "interval_min", "blocks", "minutes", "first_start"],
        printable_rows,
    )


def main() -> None:
    connection = None
    try:
        default_start = date.today()
        start_date = _read_date("Start date", default_start)
        days = _read_int("Days to inspect", 14)

        connection = connect_to_db()
        cursor = connection.cursor()
        rows = _collect_rows(cursor, start_date, days)

        print(f"Inspected range: {start_date.isoformat()} to {(start_date + timedelta(days=days - 1)).isoformat()}")
        print(f"Scheduled contexts found: {len(rows)}")
        print("No database writes were performed.")

        if not rows:
            print("No scheduled contexts found for this range.")
            return

        _print_summary(rows)
        _print_detail(rows)

        print("\nCheck IDUZI=6 / Rostislav Bednar first, then any other rows with interval_min=10 or mixed intervals.")

    except Exception as error:  # noqa: BLE001
        print(f"Schedule interval inspection failed: {error}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
