"""Read-only appointment type inspection for mapping Medicus UI colors to DB values.

This script is intended for client-assisted verification. Run it for a date
where Medicus UI contains known examples of skin examination, dermatoscope,
plasma, reservations, and regular-check variants. Compare the printed rows
against what the client sees in the UI.

No database writes are performed.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


DATE_FORMAT = "%Y-%m-%d"
TARGET_TABLE = "OBJOBJ"

CORE_COLUMNS = [
    "IDOBJ",
    "IDPAC",
    "IDPRAC",
    "IDUZI",
    "DATUM",
    "CAS",
    "CASDO",
    "DATUMDO",
    "TYP",
    "PRISEL",
    "REZERVACE",
    "INFO",
    "POZNAMKA",
    "POZN",
    "DRUH",
    "BARVA",
    "SKUPINA",
    "CEKATEL",
    "ES_RESYNC_NEEDED",
    "CREATEDBY",
    "CREATED",
    "CHANGED",
]

TYPE_LOOKUP_KEYWORDS = ("TYP", "OBJ", "OBJED", "DRUH", "BARVA", "KALENDAR")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _read_date() -> date:
    while True:
        raw_value = input(f"Target date ({DATE_FORMAT}): ").strip()
        try:
            return datetime.strptime(raw_value, DATE_FORMAT).date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")


def _print_section(title: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def _print_rows(headers: list[str], rows: list[list[Any]]) -> None:
    print(" | ".join(headers))
    print("-" * 120)
    for row in rows:
        print(" | ".join(_clean(value) for value in row))


def _load_columns(cursor, table_name: str) -> list[str]:
    cursor.execute(
        """
        SELECT RDB$FIELD_NAME
        FROM RDB$RELATION_FIELDS
        WHERE RDB$RELATION_NAME = ?
        ORDER BY RDB$FIELD_POSITION
        """,
        (table_name,),
    )
    return [_clean(row[0]).upper() for row in cursor.fetchall()]


def _load_doctor_map(cursor) -> dict[int, str]:
    cursor.execute(
        """
        SELECT IDUZI, JMENO, PRIJMENI
        FROM UZIVATEL
        ORDER BY IDUZI
        """
    )
    doctors: dict[int, str] = {}
    for doctor_id, first_name, last_name in cursor.fetchall():
        first_name_text = _clean(first_name)
        last_name_text = _clean(last_name)
        display_name = f"{first_name_text} {last_name_text}".strip() or "<no name>"
        doctors[int(doctor_id)] = display_name
    return doctors


def _duration_minutes(row: dict[str, Any]) -> int | None:
    start = row.get("CAS")
    end = row.get("CASDO")
    if not isinstance(start, time) or not isinstance(end, time):
        return None
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    if end_minutes < start_minutes:
        return None
    return end_minutes - start_minutes


def _load_appointments(cursor, target_date: date, available_columns: list[str]) -> tuple[list[str], list[dict[str, Any]]]:
    selected_columns = [column for column in CORE_COLUMNS if column in available_columns]
    if "DATUM" not in selected_columns:
        raise ValueError("OBJOBJ.DATUM was not found; cannot inspect appointments by date")

    query = f"""
        SELECT {", ".join(selected_columns)}
        FROM {TARGET_TABLE}
        WHERE DATUM = ?
        ORDER BY IDUZI, IDPRAC, CAS, IDOBJ
    """
    cursor.execute(query, (target_date,))

    rows: list[dict[str, Any]] = []
    for values in cursor.fetchall():
        rows.append(dict(zip(selected_columns, values)))

    return selected_columns, rows


def _print_appointment_rows(columns: list[str], rows: list[dict[str, Any]], doctors: dict[int, str]) -> None:
    _print_section("Appointment rows for UI comparison")
    headers = columns.copy()
    if "IDUZI" in columns:
        headers.insert(columns.index("IDUZI") + 1, "DOCTOR_NAME")

    printable_rows: list[list[Any]] = []
    for row in rows:
        printable_row: list[Any] = []
        for column in columns:
            printable_row.append(row.get(column))
            if column == "IDUZI":
                doctor_id = row.get("IDUZI")
                printable_row.append(doctors.get(int(doctor_id), "") if doctor_id is not None else "")
        printable_rows.append(printable_row)

    if printable_rows:
        _print_rows(headers, printable_rows)
    else:
        print("No appointment rows found for this date.")


def _print_type_summary(rows: list[dict[str, Any]], doctors: dict[int, str]) -> None:
    _print_section("Summary by OBJOBJ.TYP")
    if not rows:
        print("No rows to summarize.")
        return

    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row.get("TYP")].append(row)

    summary_rows: list[list[Any]] = []
    for typ_value, group_rows in sorted(groups.items(), key=lambda item: _clean(item[0])):
        doctors_seen = sorted(
            {
                doctors.get(int(row["IDUZI"]), f"IDUZI={row['IDUZI']}")
                for row in group_rows
                if row.get("IDUZI") is not None
            }
        )
        durations = sorted(
            {duration for row in group_rows if (duration := _duration_minutes(row)) is not None}
        )
        first_time = min((_clean(row.get("CAS")) for row in group_rows if row.get("CAS") is not None), default="")
        last_time = max((_clean(row.get("CAS")) for row in group_rows if row.get("CAS") is not None), default="")
        infos = sorted({_clean(row.get("INFO")) for row in group_rows if _clean(row.get("INFO"))})

        summary_rows.append(
            [
                typ_value,
                len(group_rows),
                ", ".join(str(duration) for duration in durations),
                first_time,
                last_time,
                "; ".join(doctors_seen),
                " / ".join(infos[:5]),
            ]
        )

    _print_rows(
        ["TYP", "count", "durations_min", "first_CAS", "last_CAS", "doctors", "sample_INFO"],
        summary_rows,
    )


def _print_non_empty_columns(rows: list[dict[str, Any]]) -> None:
    _print_section("Non-empty inspected columns")
    if not rows:
        print("No rows to inspect.")
        return

    counts: dict[str, int] = defaultdict(int)
    samples: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        for column, value in row.items():
            cleaned = _clean(value)
            if cleaned:
                counts[column] += 1
                if len(samples[column]) < 5:
                    samples[column].add(cleaned)

    summary_rows = [
        [column, counts[column], " / ".join(sorted(samples[column]))]
        for column in sorted(counts)
    ]
    _print_rows(["column", "non_empty_count", "sample_values"], summary_rows)


def _print_candidate_lookup_tables(cursor) -> None:
    _print_section("Candidate appointment type lookup tables/procedures")
    cursor.execute(
        """
        SELECT RDB$RELATION_NAME
        FROM RDB$RELATIONS
        WHERE COALESCE(RDB$SYSTEM_FLAG, 0) = 0
          AND RDB$VIEW_BLR IS NULL
        ORDER BY RDB$RELATION_NAME
        """
    )
    table_names = [_clean(row[0]).upper() for row in cursor.fetchall()]
    matching_tables = [
        table_name
        for table_name in table_names
        if any(keyword in table_name for keyword in TYPE_LOOKUP_KEYWORDS)
    ]

    cursor.execute(
        """
        SELECT RDB$PROCEDURE_NAME
        FROM RDB$PROCEDURES
        ORDER BY RDB$PROCEDURE_NAME
        """
    )
    procedure_names = [_clean(row[0]).upper() for row in cursor.fetchall()]
    matching_procedures = [
        procedure_name
        for procedure_name in procedure_names
        if any(keyword in procedure_name for keyword in TYPE_LOOKUP_KEYWORDS)
    ]

    print("Tables:")
    for table_name in matching_tables[:100]:
        print(f"- {table_name}")
    if len(matching_tables) > 100:
        print(f"... {len(matching_tables) - 100} more")

    print("\nProcedures:")
    for procedure_name in matching_procedures[:100]:
        print(f"- {procedure_name}")
    if len(matching_procedures) > 100:
        print(f"... {len(matching_procedures) - 100} more")


def main() -> None:
    connection = None
    try:
        target_date = _read_date()
        connection = connect_to_db()
        cursor = connection.cursor()

        doctors = _load_doctor_map(cursor)
        available_columns = _load_columns(cursor, TARGET_TABLE)
        selected_columns, rows = _load_appointments(cursor, target_date, available_columns)

        print(f"Target date: {target_date.isoformat()}")
        print(f"Rows found: {len(rows)}")
        print("No database writes were performed.")

        _print_appointment_rows(selected_columns, rows, doctors)
        _print_type_summary(rows, doctors)
        _print_non_empty_columns(rows)
        _print_candidate_lookup_tables(cursor)

        print("\nNext step: compare the rows above with Medicus UI colors for the same date.")
        print("Record which TYP values correspond to skin, dermatoscope, plasma, reservations, red, and green.")

    except Exception as error:  # noqa: BLE001
        print(f"Appointment type inspection failed: {error}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
