"""Read-only inspection script for mapping appointment booking writes.

This script does not write to the database. It inspects OBJOBJ metadata,
related triggers, indexes, generators, and stored procedures so Phase 3 can
prepare a safe transaction/rollback insert test.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


TARGET_TABLE = "OBJOBJ"
PROCEDURE_KEYWORDS = ("OBJOBJ", "OBJED", "KALENDAR", "PAC", "OBJ")
GENERATOR_KEYWORDS = ("OBJ", "OBJED", "OBJOBJ", "PAC")

FIELD_TYPE_NAMES = {
    7: "SMALLINT",
    8: "INTEGER",
    10: "FLOAT",
    12: "DATE",
    13: "TIME",
    14: "CHAR",
    16: "BIGINT/NUMERIC/DECIMAL",
    27: "DOUBLE PRECISION",
    35: "TIMESTAMP",
    37: "VARCHAR",
    40: "CSTRING",
    261: "BLOB",
}


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _print_section(title: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def _print_rows(headers: list[str], rows) -> None:
    print(" | ".join(headers))
    print("-" * 100)
    for row in rows:
        print(" | ".join(_clean(value) for value in row))


def inspect_columns(cursor) -> None:
    _print_section(f"{TARGET_TABLE} columns")
    cursor.execute(
        """
        SELECT
            rf.RDB$FIELD_POSITION,
            rf.RDB$FIELD_NAME,
            f.RDB$FIELD_TYPE,
            f.RDB$FIELD_SUB_TYPE,
            f.RDB$FIELD_LENGTH,
            f.RDB$FIELD_PRECISION,
            f.RDB$FIELD_SCALE,
            rf.RDB$NULL_FLAG,
            rf.RDB$DEFAULT_SOURCE,
            f.RDB$DEFAULT_SOURCE,
            rf.RDB$DESCRIPTION
        FROM RDB$RELATION_FIELDS rf
        JOIN RDB$FIELDS f ON f.RDB$FIELD_NAME = rf.RDB$FIELD_SOURCE
        WHERE rf.RDB$RELATION_NAME = ?
        ORDER BY rf.RDB$FIELD_POSITION
        """,
        (TARGET_TABLE,),
    )
    rows = cursor.fetchall()

    headers = [
        "pos",
        "column",
        "type",
        "subtype",
        "length",
        "precision",
        "scale",
        "not_null",
        "relation_default",
        "field_default",
        "description",
    ]

    normalized_rows = []
    for row in rows:
        field_type = row[2]
        type_name = FIELD_TYPE_NAMES.get(field_type, f"UNKNOWN({field_type})")
        normalized_rows.append(
            (
                row[0],
                row[1],
                type_name,
                row[3],
                row[4],
                row[5],
                row[6],
                "YES" if row[7] else "NO",
                row[8],
                row[9],
                row[10],
            )
        )

    _print_rows(headers, normalized_rows)


def inspect_constraints(cursor) -> None:
    _print_section(f"{TARGET_TABLE} constraints")
    cursor.execute(
        """
        SELECT
            rc.RDB$CONSTRAINT_TYPE,
            rc.RDB$CONSTRAINT_NAME,
            rc.RDB$INDEX_NAME,
            iseg.RDB$FIELD_NAME,
            iseg.RDB$FIELD_POSITION
        FROM RDB$RELATION_CONSTRAINTS rc
        LEFT JOIN RDB$INDEX_SEGMENTS iseg ON iseg.RDB$INDEX_NAME = rc.RDB$INDEX_NAME
        WHERE rc.RDB$RELATION_NAME = ?
        ORDER BY rc.RDB$CONSTRAINT_TYPE, rc.RDB$CONSTRAINT_NAME, iseg.RDB$FIELD_POSITION
        """,
        (TARGET_TABLE,),
    )
    _print_rows(
        ["constraint_type", "constraint_name", "index_name", "field", "field_position"],
        cursor.fetchall(),
    )


def inspect_indexes(cursor) -> None:
    _print_section(f"{TARGET_TABLE} indexes")
    cursor.execute(
        """
        SELECT
            idx.RDB$INDEX_NAME,
            idx.RDB$UNIQUE_FLAG,
            idx.RDB$INDEX_INACTIVE,
            idx.RDB$FOREIGN_KEY,
            iseg.RDB$FIELD_NAME,
            iseg.RDB$FIELD_POSITION
        FROM RDB$INDICES idx
        LEFT JOIN RDB$INDEX_SEGMENTS iseg ON iseg.RDB$INDEX_NAME = idx.RDB$INDEX_NAME
        WHERE idx.RDB$RELATION_NAME = ?
        ORDER BY idx.RDB$INDEX_NAME, iseg.RDB$FIELD_POSITION
        """,
        (TARGET_TABLE,),
    )
    _print_rows(
        ["index_name", "unique", "inactive", "foreign_key", "field", "field_position"],
        cursor.fetchall(),
    )


def inspect_triggers(cursor) -> None:
    _print_section(f"{TARGET_TABLE} triggers")
    cursor.execute(
        """
        SELECT
            RDB$TRIGGER_NAME,
            RDB$TRIGGER_TYPE,
            RDB$TRIGGER_SEQUENCE,
            RDB$TRIGGER_INACTIVE,
            RDB$TRIGGER_SOURCE
        FROM RDB$TRIGGERS
        WHERE RDB$RELATION_NAME = ?
        ORDER BY RDB$TRIGGER_TYPE, RDB$TRIGGER_SEQUENCE, RDB$TRIGGER_NAME
        """,
        (TARGET_TABLE,),
    )
    rows = cursor.fetchall()
    for name, trigger_type, sequence, inactive, source in rows:
        print(f"\nTrigger: {_clean(name)}")
        print(f"Type: {trigger_type} | Sequence: {sequence} | Inactive: {inactive}")
        print("Source:")
        print(_clean(source) or "<no source>")

    if not rows:
        print("No triggers found.")


def inspect_generators(cursor) -> None:
    _print_section("Potential generators/sequences")
    cursor.execute(
        """
        SELECT RDB$GENERATOR_NAME, RDB$SYSTEM_FLAG
        FROM RDB$GENERATORS
        WHERE COALESCE(RDB$SYSTEM_FLAG, 0) = 0
        ORDER BY RDB$GENERATOR_NAME
        """
    )
    rows = cursor.fetchall()
    filtered = [
        row
        for row in rows
        if any(keyword in _clean(row[0]).upper() for keyword in GENERATOR_KEYWORDS)
    ]
    _print_rows(["generator_name", "system_flag"], filtered)
    if not filtered:
        print("No obvious appointment-related generators found by keyword.")


def inspect_procedures(cursor) -> None:
    _print_section("Potential booking-related procedures")
    cursor.execute(
        """
        SELECT RDB$PROCEDURE_NAME, RDB$PROCEDURE_SOURCE
        FROM RDB$PROCEDURES
        ORDER BY RDB$PROCEDURE_NAME
        """
    )
    rows = cursor.fetchall()

    matches = []
    for name, source in rows:
        name_text = _clean(name)
        source_text = _clean(source)
        haystack = f"{name_text}\n{source_text}".upper()
        if any(keyword in haystack for keyword in PROCEDURE_KEYWORDS):
            matches.append((name_text, source_text))

    for name, source in matches:
        print(f"\nProcedure: {name}")
        if source:
            lines = source.splitlines()
            for line in lines[:80]:
                print(line)
            if len(lines) > 80:
                print(f"... <truncated, {len(lines) - 80} more lines>")
        else:
            print("<no source>")

    if not matches:
        print("No obvious booking-related procedures found by keyword.")


def inspect_recent_rows(cursor) -> None:
    _print_section(f"Optional recent {TARGET_TABLE} rows")
    answer = input(
        "Print recent appointment rows from OBJOBJ? This may include patient data. Type YES to continue: "
    ).strip()
    if answer != "YES":
        print("Skipped recent row output.")
        return

    limit_raw = input("How many rows? Press Enter for 10: ").strip()
    try:
        limit = int(limit_raw) if limit_raw else 10
    except ValueError:
        limit = 10

    limit = max(1, min(limit, 50))
    cursor.execute(
        f"""
        SELECT FIRST {limit} *
        FROM {TARGET_TABLE}
        ORDER BY DATUM DESC, CAS DESC
        """
    )
    column_names = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    _print_rows(column_names, rows)


def main() -> None:
    connection = None
    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        inspect_columns(cursor)
        inspect_constraints(cursor)
        inspect_indexes(cursor)
        inspect_triggers(cursor)
        inspect_generators(cursor)
        inspect_procedures(cursor)
        inspect_recent_rows(cursor)

        print("\nInspection complete. No database writes were performed.")

    except Exception as error:  # noqa: BLE001
        print(f"Inspection failed: {error}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
