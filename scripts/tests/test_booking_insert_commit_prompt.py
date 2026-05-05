"""Commit-prompt test insert for verifying Medicus UI visibility.

This Phase 3 script inserts a clearly marked appointment row into OBJOBJ,
reads it back in the same transaction, then asks for an explicit confirmation
phrase before committing. Any other answer rolls the transaction back.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPTS_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "booking_insert_test.local.json"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMATS = ("%H:%M", "%H:%M:%S")
MARKER = "AI_RECEPTION_TEST_COMMIT"
COMMIT_PHRASE = "COMMIT TEST APPOINTMENT"
DEFAULT_TYPE = 1
DEFAULT_PRISEL = "N"
DEFAULT_CREATED_BY = 10
DEFAULT_DURATION_MINUTES = 15


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    print(f"Loaded defaults from {CONFIG_PATH}")
    return config


def _read_int(prompt: str, default: int | None = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw_value = input(f"{prompt}{suffix}: ").strip()
        if not raw_value and default is not None:
            return default
        try:
            return int(raw_value)
        except ValueError:
            print("Enter a whole number.")


def _read_date(prompt: str, default: str | None = None) -> date:
    while True:
        suffix = f" [{default}]" if default else ""
        raw_value = input(f"{prompt} ({DATE_FORMAT}){suffix}: ").strip()
        if not raw_value and default:
            raw_value = default
        try:
            return datetime.strptime(raw_value, DATE_FORMAT).date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")


def _read_time(prompt: str, default: str | None = None) -> time:
    while True:
        suffix = f" [{default}]" if default else ""
        raw_value = input(f"{prompt} (HH:MM){suffix}: ").strip()
        if not raw_value and default:
            raw_value = default
        for time_format in TIME_FORMATS:
            try:
                return datetime.strptime(raw_value, time_format).time()
            except ValueError:
                continue
        print("Invalid time format. Use HH:MM.")


def _add_minutes(value: time, minutes: int) -> time:
    base_date = date(2000, 1, 1)
    return (datetime.combine(base_date, value) + timedelta(minutes=minutes)).time()


def _format_time(value: time) -> str:
    return value.strftime("%H:%M:%S")


def _find_conflicts(cursor, idprac: int, iduzi: int, target_date: date, start_time: time, end_time: time):
    cursor.execute(
        """
        SELECT
            IDOBJ,
            IDPAC,
            IDPRAC,
            IDUZI,
            DATUM,
            CAS,
            CASDO,
            TYP,
            PRISEL,
            INFO
        FROM OBJOBJ
        WHERE IDPRAC = ?
          AND IDUZI = ?
          AND DATUM = ?
          AND CAS < ?
          AND CASDO > ?
        ORDER BY CAS
        """,
        (idprac, iduzi, target_date, end_time, start_time),
    )
    return cursor.fetchall(), [description[0] for description in cursor.description]


def _print_conflicts(headers: list[str], rows) -> None:
    print("\nConflicting appointment rows found. Insert will not run.")
    print(" | ".join(headers))
    print("-" * 100)
    for row in rows:
        print(" | ".join("" if value is None else str(value).strip() for value in row))


def _print_row(cursor, idobj: int) -> None:
    cursor.execute(
        """
        SELECT
            IDOBJ,
            IDPAC,
            IDPRAC,
            DATUM,
            CAS,
            CASDO,
            TYP,
            PRISEL,
            INFO,
            IDUZI,
            DATUMDO,
            DATZAPIS,
            CREATEDBY,
            CREATED,
            CHANGED,
            GUID,
            CEKATEL,
            ES_RESYNC_NEEDED
        FROM OBJOBJ
        WHERE IDOBJ = ?
        """,
        (idobj,),
    )
    row = cursor.fetchone()
    if not row:
        print("Inserted row was not found in the current transaction.")
        return

    column_names = [description[0] for description in cursor.description]
    print("\nInserted row visible inside current transaction:")
    for column_name, value in zip(column_names, row):
        print(f"{column_name}: {value}")


def _verify_after_commit(connection, idobj: int) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT IDOBJ, IDPAC, IDPRAC, IDUZI, DATUM, CAS, CASDO, INFO
        FROM OBJOBJ
        WHERE IDOBJ = ?
        """,
        (idobj,),
    )
    row = cursor.fetchone()
    if row:
        print("\nCommit verification: row is visible after commit.")
        print(" | ".join(description[0] for description in cursor.description))
        print(" | ".join("" if value is None else str(value).strip() for value in row))
    else:
        print("\nCommit verification warning: row was not found after commit.")


def _confirm_commit() -> bool:
    print("\nThis is the point of no return for this test row.")
    print("Type the exact phrase below to COMMIT. Any other input will ROLLBACK.")
    print(COMMIT_PHRASE)
    answer = input("Confirmation: ").strip()
    return answer == COMMIT_PHRASE


def main() -> None:
    connection = None
    inserted_idobj = None

    try:
        config = _load_config()

        print("Commit-prompt OBJOBJ booking insert test")
        print("Use only client-approved test data and a safe test slot.")
        print(f"Marker used in OBJOBJ.INFO: {MARKER}")

        idpac = _read_int("Patient IDPAC", config.get("idpac"))
        idprac = _read_int("Workplace IDPRAC", config.get("idprac"))
        iduzi = _read_int("Doctor IDUZI", config.get("iduzi"))
        target_date = _read_date("Appointment date", config.get("date"))
        start_time = _read_time("Appointment start time", config.get("start_time"))
        duration_minutes = _read_int("Duration minutes", config.get("duration_minutes", DEFAULT_DURATION_MINUTES))
        end_time = _add_minutes(start_time, duration_minutes)
        typ = _read_int("OBJOBJ.TYP", config.get("typ", DEFAULT_TYPE))
        created_by = _read_int("CREATEDBY", config.get("created_by", DEFAULT_CREATED_BY))

        print("\nCandidate row:")
        print(f"IDPAC: {idpac}")
        print(f"IDPRAC: {idprac}")
        print(f"IDUZI: {iduzi}")
        print(f"DATUM: {target_date.isoformat()}")
        print(f"CAS: {_format_time(start_time)}")
        print(f"CASDO: {_format_time(end_time)}")
        print(f"TYP: {typ}")
        print(f"PRISEL: {DEFAULT_PRISEL}")
        print(f"INFO: {MARKER}")
        print(f"DATUMDO: {target_date.isoformat()}")
        print(f"DATZAPIS: CURRENT_DATE")
        print(f"CREATEDBY: {created_by}")

        connection = connect_to_db()
        cursor = connection.cursor()

        conflicts, conflict_headers = _find_conflicts(cursor, idprac, iduzi, target_date, start_time, end_time)
        if conflicts:
            _print_conflicts(conflict_headers, conflicts)
            connection.rollback()
            return

        print("\nConflict check passed: no overlapping OBJOBJ rows found for this doctor/workplace/time.")

        cursor.execute(
            """
            INSERT INTO OBJOBJ (
                IDPAC,
                IDPRAC,
                DATUM,
                CAS,
                TYP,
                PRISEL,
                INFO,
                IDUZI,
                DATUMDO,
                CASDO,
                DATZAPIS,
                CREATEDBY
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE, ?)
            RETURNING IDOBJ
            """,
            (
                idpac,
                idprac,
                target_date,
                start_time,
                typ,
                DEFAULT_PRISEL,
                MARKER,
                iduzi,
                target_date,
                end_time,
                created_by,
            ),
        )
        inserted_idobj = int(cursor.fetchone()[0])
        print(f"\nInserted IDOBJ inside transaction: {inserted_idobj}")

        _print_row(cursor, inserted_idobj)

        if _confirm_commit():
            connection.commit()
            print("\nCommit complete.")
            _verify_after_commit(connection, inserted_idobj)
            print("Use this IDOBJ/marker to verify visibility in Medicus UI.")
        else:
            connection.rollback()
            print("\nRolled back. No commit was performed.")

    except Exception as error:  # noqa: BLE001
        print(f"Commit-prompt insert test failed: {error}")
        if connection is not None:
            print("Rolling back after error...")
            connection.rollback()
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
