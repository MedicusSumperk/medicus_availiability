"""Rollback-only test insert for mapping OBJOBJ booking writes.

This Phase 3 script intentionally does not commit. It inserts a clearly marked
appointment row into OBJOBJ, reads it back in the same transaction, and then
rolls the transaction back so the database is not permanently changed.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMATS = ("%H:%M", "%H:%M:%S")
MARKER = "AI_RECEPTION_TEST_ROLLBACK"
DEFAULT_TYPE = 1
DEFAULT_PRISEL = "N"
DEFAULT_CREATED_BY = 10
DEFAULT_DURATION_MINUTES = 15


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


def _read_date(prompt: str) -> date:
    while True:
        raw_value = input(f"{prompt} ({DATE_FORMAT}): ").strip()
        try:
            return datetime.strptime(raw_value, DATE_FORMAT).date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")


def _read_time(prompt: str) -> time:
    while True:
        raw_value = input(f"{prompt} (HH:MM): ").strip()
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


def _confirm_insert() -> bool:
    print("\nThis script will run a test INSERT inside one transaction and then ROLLBACK.")
    print("No permanent database change should remain after rollback.")
    print(f"Marker used in OBJOBJ.INFO: {MARKER}")
    answer = input("Type INSERT to run the rollback-only test: ").strip()
    return answer == "INSERT"


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


def _verify_rolled_back(cursor, idobj: int) -> None:
    cursor.execute("SELECT COUNT(*) FROM OBJOBJ WHERE IDOBJ = ?", (idobj,))
    count = cursor.fetchone()[0]
    if count == 0:
        print("Rollback verification: inserted row is gone.")
    else:
        print(f"Rollback verification warning: row still visible, count={count}.")


def main() -> None:
    connection = None
    inserted_idobj = None

    try:
        print("Rollback-only OBJOBJ booking insert test")
        print("Use a known safe test patient and a slot agreed with the client.")

        idpac = _read_int("Patient IDPAC")
        idprac = _read_int("Workplace IDPRAC")
        iduzi = _read_int("Doctor IDUZI")
        target_date = _read_date("Appointment date")
        start_time = _read_time("Appointment start time")
        duration_minutes = _read_int("Duration minutes", DEFAULT_DURATION_MINUTES)
        end_time = _add_minutes(start_time, duration_minutes)
        typ = _read_int("OBJOBJ.TYP", DEFAULT_TYPE)
        created_by = _read_int("CREATEDBY", DEFAULT_CREATED_BY)

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

        if not _confirm_insert():
            print("Aborted before insert.")
            connection.rollback()
            return

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

        print("\nRolling back transaction now...")
        connection.rollback()
        _verify_rolled_back(cursor, inserted_idobj)
        print("Done. No commit was performed.")

    except Exception as error:  # noqa: BLE001
        print(f"Rollback insert test failed: {error}")
        if connection is not None:
            print("Rolling back after error...")
            connection.rollback()
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
