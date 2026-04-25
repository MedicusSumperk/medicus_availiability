"""Read-only deterministic inspection script for OBSPRAC scheduling records."""

import sys
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


DOCTOR_ID = 1
TARGET_DATE = "2026-04-10"

COLUMNS = [
    "IDPRAC",
    "IDUZI",
    "CAS",
    "DOBA",
    "INTERVAL",
    "TYPTYD",
    "DENTYD",
    "PLATIOD",
    "PLATIDO",
    "OBJED",
]


def _format_row(row: tuple) -> str:
    return " | ".join(str(value) if value is not None else "" for value in row)


def _compute_dentyd(target_date: date) -> int:
    """Map Python weekday to DENTYD where Monday=1 ... Sunday=7."""
    return target_date.weekday() + 1


def inspect_obsprac() -> None:
    """Print scheduling rows valid for a single doctor and exact target day."""
    target_date = date.fromisoformat(TARGET_DATE)
    target_dentyd = _compute_dentyd(target_date)
    connection = None

    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                IDPRAC,
                IDUZI,
                CAS,
                DOBA,
                INTERVAL,
                TYPTYD,
                DENTYD,
                PLATIOD,
                PLATIDO,
                OBJED
            FROM OBSPRAC
            WHERE IDUZI = ?
              AND OBJED = 'A'
              AND DENTYD = ?
              AND PLATIOD <= ?
              AND (PLATIDO >= ? OR PLATIDO IS NULL)
            ORDER BY IDPRAC, CAS
            """,
            (DOCTOR_ID, target_dentyd, target_date, target_date),
        )
        rows = cursor.fetchall()

        print(f"Doctor ID: {DOCTOR_ID}")
        print(f"Target date: {TARGET_DATE}")
        print(f"Computed DENTYD: {target_dentyd}")
        print(" | ".join(COLUMNS))
        print("-" * 120)
        for row in rows:
            print(_format_row(row))

        distinct_idprac = sorted({row[0] for row in rows if row[0] is not None})
        distinct_typtyd = sorted({row[5] for row in rows if row[5] is not None})

        print("\nSummary")
        print(f"Rows found: {len(rows)}")
        print(f"Distinct IDPRAC: {distinct_idprac}")
        print(f"Distinct TYPTYD: {distinct_typtyd}")

    except Exception as error:  # noqa: BLE001
        print(f"Failed to inspect OBSPRAC: {error}")
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Entry point for direct script execution."""
    inspect_obsprac()


if __name__ == "__main__":
    main()
