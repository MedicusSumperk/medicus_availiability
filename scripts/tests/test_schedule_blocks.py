"""Read-only script to inspect OBSDNE_PRAVODLIS_SEL daily schedule blocks."""

import sys
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


DOCTOR_ID = 1
TARGET_DATE = "2026-04-10"
IDPRAC = 1
TYPTYD = 4
DENTYD = 5


def _format_row(row: tuple) -> str:
    return " | ".join(str(value) if value is not None else "" for value in row)


def test_schedule_blocks() -> None:
    """Call OBSDNE_PRAVODLIS_SEL and print read-only inspection output."""
    connection = None

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        target_date = date.fromisoformat(TARGET_DATE)
        cursor.execute(
            """
            SELECT *
            FROM OBSDNE_PRAVODLIS_SEL(?, ?, ?, ?)
            WHERE IDUZI = ?
            ORDER BY CAS
            """,
            (target_date, TYPTYD, DENTYD, IDPRAC, DOCTOR_ID),
        )

        column_names = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        print(f"Doctor ID: {DOCTOR_ID}")
        print(f"Target date: {TARGET_DATE}")
        print(f"IDPRAC: {IDPRAC}")
        print(f"TYPTYD: {TYPTYD}")
        print(f"DENTYD: {DENTYD}")

        print("\nReturned columns:")
        print(" | ".join(column_names))

        print("\nRows:")
        print(" | ".join(column_names))
        print("-" * 120)
        for row in rows:
            print(_format_row(row))

        doba_index = next((i for i, name in enumerate(column_names) if name.upper() == "DOBA"), None)
        interval_index = next((i for i, name in enumerate(column_names) if name.upper() == "INTERVAL"), None)

        total_theoretical_slots = 0.0
        if doba_index is not None and interval_index is not None:
            for row in rows:
                doba = row[doba_index]
                interval = row[interval_index]
                if doba and interval:
                    total_theoretical_slots += float(doba) / float(interval)

        print("\nSummary")
        print(f"Rows found: {len(rows)}")
        print(f"Total theoretical slots (sum(DOBA / INTERVAL)): {total_theoretical_slots}")

    except Exception as error:  # noqa: BLE001
        print(f"Failed to test OBSDNE_PRAVODLIS_SEL: {error}")
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Entry point for direct script execution."""
    test_schedule_blocks()


if __name__ == "__main__":
    main()
