"""Database migrations."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from cube_budget.core.constants import SCHEMA_VERSION
from cube_budget.database.connection import DatabaseConnection, get_schema_version, set_schema_version


def _load_schema_sql() -> str:
    schema_path = Path(__file__).parent / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def run_migrations(db_path: str, wal_mode: bool = True, busy_timeout_ms: int = 5000) -> None:
    """Apply database migrations if needed."""
    db = DatabaseConnection(db_path, wal_mode=wal_mode, busy_timeout_ms=busy_timeout_ms)
    conn = db.connect()

    current = get_schema_version(conn)
    if current >= SCHEMA_VERSION:
        db.close()
        return

    schema_sql = _load_schema_sql()
    conn.executescript(schema_sql)
    set_schema_version(conn, SCHEMA_VERSION)
    db.close()
