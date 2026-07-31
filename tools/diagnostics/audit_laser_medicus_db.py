"""Read-only audit for the separate LASER Medicus Firebird database.

The production backend does not depend on this database yet. This diagnostic
checks whether the LASER instance has the same core Medicus tables and records
basic mapping hints for future scan-room integration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import fdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "db_config.local.json"
DEFAULT_LASER_DATABASE = "C:/Medicus 3 Laser/data/MEDICUS.FDB"
CORE_TABLES = ["UZIVATEL", "OBSPRAC", "OBJOBJ", "CINNOSTI", "KAR"]


def _load_base_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as config_file:
        return json.load(config_file)


def _connect(config: dict[str, Any], database: str):
    return fdb.connect(
        host=config["host"],
        port=config["port"],
        database=database,
        user=config["username"],
        password=config["password"],
        charset=config.get("charset", "UTF8"),
    )


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM RDB$RELATIONS
        WHERE RDB$RELATION_NAME = ?
        """,
        (table_name,),
    )
    return int(cursor.fetchone()[0]) > 0


def _count_rows(cursor, table_name: str) -> int | None:
    if not _table_exists(cursor, table_name):
        return None
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return int(cursor.fetchone()[0])


def _fetch_doctors(cursor) -> list[dict[str, Any]]:
    if not _table_exists(cursor, "UZIVATEL"):
        return []
    cursor.execute(
        """
        SELECT FIRST 30 IDUZI, JMENO, PRIJMENI
        FROM UZIVATEL
        ORDER BY IDUZI
        """
    )
    return [
        {
            "iduzi": int(row[0]),
            "name": f"{(row[1] or '').strip()} {(row[2] or '').strip()}".strip(),
        }
        for row in cursor.fetchall()
    ]


def _fetch_activities(cursor) -> list[dict[str, Any]]:
    if not _table_exists(cursor, "CINNOSTI"):
        return []
    cursor.execute(
        """
        SELECT FIRST 50 ID, NAZEV
        FROM CINNOSTI
        ORDER BY ID
        """
    )
    return [{"id": int(row[0]), "name": (row[1] or "").strip()} for row in cursor.fetchall()]


def audit_laser_database(config_path: Path, database: str) -> dict[str, Any]:
    config = _load_base_config(config_path)
    connection = _connect(config, database)
    try:
        cursor = connection.cursor()
        table_counts = {table: _count_rows(cursor, table) for table in CORE_TABLES}
        return {
            "ok": True,
            "database": database,
            "table_counts": table_counts,
            "doctors": _fetch_doctors(cursor),
            "activities": _fetch_activities(cursor),
            "runtime_dependency": False,
            "note": "Read-only diagnostic only; production runtime still infers scan-room capacity from main Medicus DB.",
        }
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Base DB config with host/user/password.")
    parser.add_argument("--database", default=DEFAULT_LASER_DATABASE, help="LASER Medicus Firebird database path.")
    args = parser.parse_args()

    result = audit_laser_database(Path(args.config), args.database)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
