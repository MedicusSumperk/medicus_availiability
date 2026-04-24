"""Basic Firebird database connection utilities."""

from __future__ import annotations

import json
from pathlib import Path

import fdb


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "db_config.local.json"


def _load_db_config() -> dict:
    """Load database connection settings from local config file."""
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def connect_to_db():
    """Create and return a Firebird database connection."""
    config = _load_db_config()
    return fdb.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["username"],
        password=config["password"],
        charset=config.get("charset", "UTF8"),
    )


def test_connection() -> None:
    """Test database connectivity with a simple query."""
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM RDB$DATABASE")
        cursor.fetchone()
        print("Connection successful")
    except Exception as error:  # noqa: BLE001
        print(f"Connection failed: {error}")
    finally:
        if "connection" in locals():
            connection.close()


if __name__ == "__main__":
    test_connection()
