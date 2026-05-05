"""Read-only helper to find candidate test patients for booking write tests."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


TABLE_NAME = "KAR"
DEFAULT_TERMS = ["TEST", "TESTOV", "DEMO", "AI", "RECEP"]
OUTPUT_COLUMN_CANDIDATES = [
    "IDPAC",
    "PRIJMENI",
    "JMENO",
    "TITUL",
    "RODCIS",
    "DATNAR",
    "POJ",
    "TELEFON",
    "EMAIL",
]
SEARCHABLE_CANDIDATES = [
    "PRIJMENI",
    "JMENO",
    "TITUL",
    "RODCIS",
    "TELEFON",
    "EMAIL",
]
TEXT_FIELD_TYPES = {14, 37}  # CHAR, VARCHAR


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _load_column_metadata(cursor) -> dict[str, dict[str, int | None]]:
    cursor.execute(
        """
        SELECT
            rf.RDB$FIELD_NAME,
            f.RDB$FIELD_TYPE,
            f.RDB$FIELD_LENGTH
        FROM RDB$RELATION_FIELDS rf
        JOIN RDB$FIELDS f ON f.RDB$FIELD_NAME = rf.RDB$FIELD_SOURCE
        WHERE rf.RDB$RELATION_NAME = ?
        ORDER BY rf.RDB$FIELD_POSITION
        """,
        (TABLE_NAME,),
    )
    return {
        _clean(column_name).upper(): {
            "type": field_type,
            "length": field_length,
        }
        for column_name, field_type, field_length in cursor.fetchall()
    }


def _print_available_columns(column_metadata: dict[str, dict[str, int | None]]) -> None:
    print(f"Available {TABLE_NAME} columns:")
    print(", ".join(column_metadata.keys()))


def _is_safe_text_column(column_metadata: dict[str, dict[str, int | None]], column: str) -> bool:
    metadata = column_metadata.get(column)
    if not metadata:
        return False
    return metadata["type"] in TEXT_FIELD_TYPES


def _build_query(column_metadata: dict[str, dict[str, int | None]], terms: list[str]) -> tuple[str, list[str], list[str]]:
    available_columns = set(column_metadata.keys())
    output_columns = [column for column in OUTPUT_COLUMN_CANDIDATES if column in available_columns]
    if "IDPAC" not in output_columns and "IDPAC" in available_columns:
        output_columns.insert(0, "IDPAC")

    searchable_columns = [
        column
        for column in SEARCHABLE_CANDIDATES
        if column in available_columns and _is_safe_text_column(column_metadata, column)
    ]
    if not searchable_columns:
        raise ValueError("No known searchable CHAR/VARCHAR patient columns found in KAR")

    where_parts = []
    params = []
    for column in searchable_columns:
        for term in terms:
            where_parts.append(f"UPPER({column}) LIKE ?")
            params.append(f"%{term.upper()}%")

    query = f"""
        SELECT FIRST 50 {", ".join(output_columns)}
        FROM {TABLE_NAME}
        WHERE {" OR ".join(where_parts)}
        ORDER BY IDPAC DESC
    """
    return query, params, searchable_columns


def _print_rows(headers: list[str], rows) -> None:
    print(" | ".join(headers))
    print("-" * 120)
    for row in rows:
        print(" | ".join(_clean(value) for value in row))


def main() -> None:
    connection = None
    try:
        raw_terms = input(
            "Search terms separated by comma, or Enter for TEST/DEMO/AI/RECEP: "
        ).strip()
        if raw_terms:
            terms = [term.strip() for term in raw_terms.split(",") if term.strip()]
        else:
            terms = DEFAULT_TERMS

        connection = connect_to_db()
        cursor = connection.cursor()

        column_metadata = _load_column_metadata(cursor)
        _print_available_columns(column_metadata)

        query, params, searchable_columns = _build_query(column_metadata, terms)
        print("\nSearching safe text columns:")
        print(", ".join(searchable_columns))

        cursor.execute(query, params)
        rows = cursor.fetchall()
        headers = [description[0] for description in cursor.description]

        print("\nCandidate test patients:")
        print(f"Search terms: {', '.join(terms)}")
        if rows:
            _print_rows(headers, rows)
        else:
            print("No candidate test patients found.")
            print("Try a different term, or ask the client for a known test IDPAC.")

        print("\nNo database writes were performed.")

    except Exception as error:  # noqa: BLE001
        print(f"Test patient lookup failed: {error}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
