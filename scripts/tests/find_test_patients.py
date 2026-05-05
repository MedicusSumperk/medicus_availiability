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
LIKELY_COLUMNS = [
    "IDPAC",
    "PRIJMENI",
    "JMENO",
    "TITUL",
    "CELEJMENO",
    "RODCIS",
    "DATNAR",
    "POJ",
    "TELEFON",
    "EMAIL",
    "POZNAMKA",
]
SEARCHABLE_NAMES = [
    "PRIJMENI",
    "JMENO",
    "CELEJMENO",
    "RODCIS",
    "TELEFON",
    "EMAIL",
    "POZNAMKA",
]


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _load_columns(cursor) -> list[str]:
    cursor.execute(
        """
        SELECT RDB$FIELD_NAME
        FROM RDB$RELATION_FIELDS
        WHERE RDB$RELATION_NAME = ?
        ORDER BY RDB$FIELD_POSITION
        """,
        (TABLE_NAME,),
    )
    return [_clean(row[0]).upper() for row in cursor.fetchall()]


def _print_available_columns(columns: list[str]) -> None:
    print(f"Available {TABLE_NAME} columns:")
    print(", ".join(columns))


def _build_query(columns: list[str], terms: list[str]) -> tuple[str, list[str]]:
    output_columns = [column for column in LIKELY_COLUMNS if column in columns]
    if "IDPAC" not in output_columns and "IDPAC" in columns:
        output_columns.insert(0, "IDPAC")

    searchable_columns = [column for column in SEARCHABLE_NAMES if column in columns]
    if not searchable_columns:
        raise ValueError("No known searchable patient columns found in KAR")

    where_parts = []
    params = []
    for column in searchable_columns:
        for term in terms:
            where_parts.append(f"UPPER(CAST({column} AS VARCHAR(255))) LIKE ?")
            params.append(f"%{term.upper()}%")

    query = f"""
        SELECT FIRST 50 {", ".join(output_columns)}
        FROM {TABLE_NAME}
        WHERE {" OR ".join(where_parts)}
        ORDER BY IDPAC DESC
    """
    return query, params


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

        columns = _load_columns(cursor)
        _print_available_columns(columns)

        query, params = _build_query(columns, terms)
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
