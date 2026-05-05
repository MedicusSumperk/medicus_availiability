"""Read-only script to inspect existing appointments from OBJOBJ."""

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


def _format_row(row: tuple) -> str:
    return " | ".join(str(value) if value is not None else "" for value in row)


def test_appointments() -> None:
    """Load and print existing appointments for one doctor/day/schedule."""
    connection = None

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        date.fromisoformat(TARGET_DATE)  # Validate TARGET_DATE format.
        cursor.execute(
            f"""
            SELECT *
            FROM OBJOBJ
            WHERE IDPRAC = {IDPRAC}
              AND IDUZI = {DOCTOR_ID}
              AND DATUM = DATE '{TARGET_DATE}'
            ORDER BY CAS
            """
        )

        column_names = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        print(f"Doctor ID: {DOCTOR_ID}")
        print(f"Target date: {TARGET_DATE}")
        print(f"IDPRAC: {IDPRAC}")

        print("\nReturned columns:")
        print(" | ".join(column_names))

        print("\nRows:")
        print(" | ".join(column_names))
        print("-" * 120)
        for row in rows:
            print(_format_row(row))

        cas_index = next((i for i, name in enumerate(column_names) if name.upper() == "CAS"), None)
        typ_index = next((i for i, name in enumerate(column_names) if name.upper() == "TYP"), None)
        rezervace_index = next((i for i, name in enumerate(column_names) if name.upper() == "REZERVACE"), None)
        prisel_index = next((i for i, name in enumerate(column_names) if name.upper() == "PRISEL"), None)

        earliest_cas = None
        latest_cas = None
        if cas_index is not None and rows:
            cas_values = [row[cas_index] for row in rows if row[cas_index] is not None]
            if cas_values:
                earliest_cas = min(cas_values)
                latest_cas = max(cas_values)

        print("\nSummary")
        print(f"Rows found: {len(rows)}")
        print(f"Earliest CAS: {earliest_cas}")
        print(f"Latest CAS: {latest_cas}")

        if typ_index is not None:
            distinct_typ = sorted({row[typ_index] for row in rows if row[typ_index] is not None})
            print(f"Distinct TYP: {distinct_typ}")

        if rezervace_index is not None:
            distinct_rezervace = sorted(
                {row[rezervace_index] for row in rows if row[rezervace_index] is not None}
            )
            print(f"Distinct REZERVACE: {distinct_rezervace}")

        if prisel_index is not None:
            distinct_prisel = sorted({row[prisel_index] for row in rows if row[prisel_index] is not None})
            print(f"Distinct PRISEL: {distinct_prisel}")

    except Exception as error:  # noqa: BLE001
        print(f"Failed to test appointments: {error}")
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Entry point for direct script execution."""
    test_appointments()


if __name__ == "__main__":
    main()
