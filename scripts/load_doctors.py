"""Load and print a sample doctor directory from the database."""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


def load_doctors(limit: int = 50) -> None:
    """Query doctor-like user records and print IDUZI with full name."""
    connection = None
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT FIRST {int(limit)}
                IDUZI,
                JMENO,
                PRIJMENI
            FROM UZIVATEL
            ORDER BY IDUZI
            """
        )

        print("IDUZI | Full Name")
        print("-" * 40)

        for iduzi, jmeno, prijmeni in cursor.fetchall():
            first_name = (jmeno or "").strip()
            last_name = (prijmeni or "").strip()
            full_name = f"{first_name} {last_name}".strip() or "<no name>"
            print(f"{iduzi} | {full_name}")

    except Exception as error:  # noqa: BLE001
        print(f"Failed to load doctors: {error}")
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Entry point for loading doctor data preview."""
    load_doctors(limit=50)


if __name__ == "__main__":
    main()
