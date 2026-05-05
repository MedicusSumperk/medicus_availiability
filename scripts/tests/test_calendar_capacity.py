"""Read-only script to inspect aggregated calendar capacity via SP_OBJ_KALENDAR."""

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
IDPAC = None


def _format_row(row: tuple) -> str:
    return " | ".join(str(value) if value is not None else "" for value in row)


def test_calendar_capacity() -> None:
    """Call SP_OBJ_KALENDAR and print aggregate capacity indicators."""
    connection = None

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        target_date = date.fromisoformat(TARGET_DATE)
        cursor.execute(
            """
            SELECT *
            FROM SP_OBJ_KALENDAR(?, ?, ?, ?, ?, ?, ?)
            """,
            (DOCTOR_ID, IDPRAC, target_date, target_date, TYPTYD, DENTYD, IDPAC),
        )

        column_names = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        print(f"Doctor ID: {DOCTOR_ID}")
        print(f"Target date: {TARGET_DATE}")
        print(f"IDPRAC: {IDPRAC}")
        print(f"TYPTYD: {TYPTYD}")
        print(f"DENTYD: {DENTYD}")
        print(f"IDPAC: {IDPAC}")

        print("\nReturned columns:")
        print(" | ".join(column_names))

        print("\nRows:")
        print(" | ".join(column_names))
        print("-" * 120)
        for row in rows:
            print(_format_row(row))

        dop_index = next((i for i, name in enumerate(column_names) if name.upper() == "DOP"), None)
        odp_index = next((i for i, name in enumerate(column_names) if name.upper() == "ODP"), None)

        dop_value = 0.0
        odp_value = 0.0

        if dop_index is not None:
            dop_value = sum(float(row[dop_index]) for row in rows if row[dop_index] is not None)

        if odp_index is not None:
            odp_value = sum(float(row[odp_index]) for row in rows if row[odp_index] is not None)

        total_available_capacity = dop_value + odp_value

        print("\nSummary")
        print(f"DOP value: {dop_value}")
        print(f"ODP value: {odp_value}")
        print(f"Total available capacity (DOP + ODP): {total_available_capacity}")

    except Exception as error:  # noqa: BLE001
        print(f"Failed to test SP_OBJ_KALENDAR: {error}")
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Entry point for direct script execution."""
    test_calendar_capacity()


if __name__ == "__main__":
    main()
