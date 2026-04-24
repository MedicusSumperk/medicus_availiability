"""Read-only inspection script for appointment-enabled scheduling records."""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


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


def inspect_obsprac(limit: int = 100) -> None:
    """Print a preview of appointment-enabled rows from OBSPRAC."""
    connection = None
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT FIRST {int(limit)}
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
            WHERE OBJED = 'A'
            ORDER BY IDUZI, IDPRAC, PLATIDO DESC, DENTYD, CAS
            """
        )
        rows = cursor.fetchall()

        print(" | ".join(COLUMNS))
        print("-" * 120)
        for row in rows:
            print(_format_row(row))

        print(f"\nDisplayed {len(rows)} records (max {limit}).")

    except Exception as error:  # noqa: BLE001
        print(f"Failed to inspect OBSPRAC: {error}")
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Entry point for direct script execution."""
    inspect_obsprac(limit=100)


if __name__ == "__main__":
    main()
