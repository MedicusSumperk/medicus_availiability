"""Commit-prompt insert test for verifying OBJOBJ.IDCINNOSTI UI behavior.

This Phase 3 diagnostic inserts multiple clearly marked appointment rows with
different IDCINNOSTI values so the client can verify whether Medicus calendar
colors/activities are driven by OBJOBJ.IDCINNOSTI -> CINNOSTI.

Any answer other than the exact commit phrase rolls the transaction back.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPTS_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "activity_insert_test.local.json"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMATS = ("%H:%M", "%H:%M:%S")
COMMIT_PHRASE = "COMMIT ACTIVITY TEST APPOINTMENTS"
DEFAULT_TYPE = 1
DEFAULT_PRISEL = "N"
DEFAULT_CREATED_BY = 10
DEFAULT_SLOT_GAP_MINUTES = 30


DEFAULT_VARIANTS = [
    {
        "label": "skin_default",
        "idcinnosti": None,
        "duration_minutes": 15,
        "info": "AI_ACTIVITY_TEST_SKIN_DEFAULT",
    },
    {
        "label": "derm_scan_1",
        "idcinnosti": 1,
        "duration_minutes": 15,
        "info": "AI_ACTIVITY_TEST_DERM_1",
    },
    {
        "label": "derm_followup",
        "idcinnosti": 2,
        "duration_minutes": 15,
        "info": "AI_ACTIVITY_TEST_DERM_FOLLOWUP",
    },
    {
        "label": "laser_plasma",
        "idcinnosti": 3,
        "duration_minutes": 30,
        "info": "AI_ACTIVITY_TEST_PLAZMA",
    },
    {
        "label": "derm_scan_repeat",
        "idcinnosti": 5,
        "duration_minutes": 15,
        "info": "AI_ACTIVITY_TEST_DERM_REPEAT",
    },
    {
        "label": "derm_reservation",
        "idcinnosti": 6,
        "duration_minutes": 15,
        "info": "AI_ACTIVITY_TEST_DERM_RESERVATION",
    },
]


def _load_config() -> dict[str, Any]:
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


def _build_candidate_rows(
    target_date: date,
    first_start_time: time,
    slot_gap_minutes: int,
    variants: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, variant in enumerate(variants):
        start_time = _add_minutes(first_start_time, index * slot_gap_minutes)
        duration_minutes = int(variant.get("duration_minutes", 15))
        rows.append(
            {
                "label": str(variant["label"]),
                "idcinnosti": variant.get("idcinnosti"),
                "target_date": target_date,
                "start_time": start_time,
                "end_time": _add_minutes(start_time, duration_minutes),
                "duration_minutes": duration_minutes,
                "info": str(variant["info"]),
            }
        )
    return rows


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
            IDCINNOSTI,
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


def _print_rows(headers: list[str], rows) -> None:
    print(" | ".join(headers))
    print("-" * 120)
    for row in rows:
        print(" | ".join("" if value is None else str(value).strip() for value in row))


def _check_all_conflicts(cursor, idprac: int, iduzi: int, candidate_rows: list[dict[str, Any]]) -> bool:
    any_conflicts = False
    for candidate in candidate_rows:
        conflicts, headers = _find_conflicts(
            cursor,
            idprac,
            iduzi,
            candidate["target_date"],
            candidate["start_time"],
            candidate["end_time"],
        )
        if conflicts:
            any_conflicts = True
            print(
                "\nConflicts for "
                f"{candidate['label']} {candidate['target_date'].isoformat()} "
                f"{_format_time(candidate['start_time'])}-{_format_time(candidate['end_time'])}:"
            )
            _print_rows(headers, conflicts)
    return any_conflicts


def _print_candidate_rows(
    idpac: int,
    idprac: int,
    iduzi: int,
    typ: int,
    created_by: int,
    candidate_rows: list[dict[str, Any]],
) -> None:
    print("\nCandidate rows:")
    headers = [
        "label",
        "IDPAC",
        "IDPRAC",
        "IDUZI",
        "DATUM",
        "CAS",
        "CASDO",
        "TYP",
        "IDCINNOSTI",
        "PRISEL",
        "INFO",
        "CREATEDBY",
    ]
    rows = []
    for candidate in candidate_rows:
        rows.append(
            [
                candidate["label"],
                idpac,
                idprac,
                iduzi,
                candidate["target_date"].isoformat(),
                _format_time(candidate["start_time"]),
                _format_time(candidate["end_time"]),
                typ,
                candidate["idcinnosti"],
                DEFAULT_PRISEL,
                candidate["info"],
                created_by,
            ]
        )
    _print_rows(headers, rows)


def _confirm_commit() -> bool:
    print("\nThis is the point of no return for these test rows.")
    print("Type the exact phrase below to COMMIT. Any other input will ROLLBACK.")
    print(COMMIT_PHRASE)
    answer = input("Confirmation: ").strip()
    return answer == COMMIT_PHRASE


def _insert_candidate_rows(
    cursor,
    idpac: int,
    idprac: int,
    iduzi: int,
    typ: int,
    created_by: int,
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    inserted_rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
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
                CREATEDBY,
                IDCINNOSTI
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE, ?, ?)
            RETURNING IDOBJ
            """,
            (
                idpac,
                idprac,
                candidate["target_date"],
                candidate["start_time"],
                typ,
                DEFAULT_PRISEL,
                candidate["info"],
                iduzi,
                candidate["target_date"],
                candidate["end_time"],
                created_by,
                candidate["idcinnosti"],
            ),
        )
        idobj = int(cursor.fetchone()[0])
        inserted_rows.append({**candidate, "idobj": idobj})
    return inserted_rows


def _print_inserted_rows(cursor, inserted_rows: list[dict[str, Any]]) -> None:
    if not inserted_rows:
        print("No inserted rows to print.")
        return

    ids = [row["idobj"] for row in inserted_rows]
    placeholders = ", ".join("?" for _ in ids)
    cursor.execute(
        f"""
        SELECT
            o.IDOBJ,
            o.DATUM,
            o.CAS,
            o.CASDO,
            o.IDPAC,
            o.IDPRAC,
            o.IDUZI,
            o.TYP,
            o.IDCINNOSTI,
            c.NAZEV,
            c.BARVA,
            o.INFO,
            o.CREATEDBY,
            o.CREATED,
            o.CHANGED
        FROM OBJOBJ o
        LEFT JOIN CINNOSTI c ON c.ID = o.IDCINNOSTI
        WHERE o.IDOBJ IN ({placeholders})
        ORDER BY o.CAS, o.IDOBJ
        """,
        tuple(ids),
    )
    print("\nInserted rows visible inside current transaction:")
    _print_rows([description[0] for description in cursor.description], cursor.fetchall())


def _verify_after_commit(connection, inserted_rows: list[dict[str, Any]]) -> None:
    cursor = connection.cursor()
    ids = [row["idobj"] for row in inserted_rows]
    placeholders = ", ".join("?" for _ in ids)
    cursor.execute(
        f"""
        SELECT
            o.IDOBJ,
            o.DATUM,
            o.CAS,
            o.CASDO,
            o.IDPAC,
            o.IDPRAC,
            o.IDUZI,
            o.TYP,
            o.IDCINNOSTI,
            c.NAZEV,
            c.BARVA,
            o.INFO
        FROM OBJOBJ o
        LEFT JOIN CINNOSTI c ON c.ID = o.IDCINNOSTI
        WHERE o.IDOBJ IN ({placeholders})
        ORDER BY o.CAS, o.IDOBJ
        """,
        tuple(ids),
    )
    rows = cursor.fetchall()
    print("\nCommit verification rows:")
    _print_rows([description[0] for description in cursor.description], rows)
    if len(rows) != len(ids):
        print(f"Warning: expected {len(ids)} rows after commit, found {len(rows)}.")


def main() -> None:
    connection = None

    try:
        config = _load_config()
        variants = config.get("variants", DEFAULT_VARIANTS)

        print("Commit-prompt OBJOBJ.IDCINNOSTI activity insert test")
        print("Use only client-approved test data and safe test slots.")
        print("This script can insert multiple rows and should be used only during a controlled UI verification call.")

        idpac = _read_int("Patient IDPAC", config.get("idpac"))
        idprac = _read_int("Workplace IDPRAC", config.get("idprac"))
        iduzi = _read_int("Doctor IDUZI", config.get("iduzi"))
        target_date = _read_date("Appointment date", config.get("date"))
        first_start_time = _read_time("First appointment start time", config.get("start_time"))
        slot_gap_minutes = _read_int(
            "Gap between test starts in minutes",
            config.get("slot_gap_minutes", DEFAULT_SLOT_GAP_MINUTES),
        )
        typ = _read_int("OBJOBJ.TYP", config.get("typ", DEFAULT_TYPE))
        created_by = _read_int("CREATEDBY", config.get("created_by", DEFAULT_CREATED_BY))

        candidate_rows = _build_candidate_rows(target_date, first_start_time, slot_gap_minutes, variants)
        _print_candidate_rows(idpac, idprac, iduzi, typ, created_by, candidate_rows)

        connection = connect_to_db()
        cursor = connection.cursor()

        if _check_all_conflicts(cursor, idprac, iduzi, candidate_rows):
            print("\nAt least one conflict was found. No inserts were run.")
            connection.rollback()
            return

        print("\nConflict check passed for all candidate rows.")

        inserted_rows = _insert_candidate_rows(
            cursor,
            idpac,
            idprac,
            iduzi,
            typ,
            created_by,
            candidate_rows,
        )
        _print_inserted_rows(cursor, inserted_rows)

        if _confirm_commit():
            connection.commit()
            print("\nCommit complete.")
            _verify_after_commit(connection, inserted_rows)
            print("Use the IDOBJ values above to verify Medicus UI colors/activities and to clean up test rows.")
        else:
            connection.rollback()
            print("\nRolled back. No commit was performed.")

    except Exception as error:  # noqa: BLE001
        print(f"Activity insert test failed: {error}")
        if connection is not None:
            print("Rolling back after error...")
            connection.rollback()
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
