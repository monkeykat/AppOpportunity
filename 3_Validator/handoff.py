"""Synchronize the Phase 2 database into Validator's private database."""

import shutil
import sqlite3
from pathlib import Path
from typing import Optional

try:
    from .config import get_database_path, get_investigator_database_path
    from .database import init_database
except ImportError:
    from config import get_database_path, get_investigator_database_path
    from database import init_database


def _quote_identifier(identifier: str) -> str:
    return '"{}"'.format(identifier.replace('"', '""'))


def _sync_table(connection: sqlite3.Connection, table: str) -> int:
    source_columns = {
        row[1] for row in connection.execute("PRAGMA source.table_info({})".format(_quote_identifier(table)))
    }
    target_columns = {
        row[1] for row in connection.execute("PRAGMA main.table_info({})".format(_quote_identifier(table)))
    }
    columns = [column for column in ("app_id",) if column in source_columns and column in target_columns]
    columns.extend(
        column
        for column in sorted(source_columns & target_columns)
        if column not in {"id", "app_id"}
    )
    if not columns:
        return 0

    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    updates = ", ".join(
        "{} = excluded.{}".format(_quote_identifier(column), _quote_identifier(column))
        for column in columns
        if column != "app_id"
    )
    sql = (
        "INSERT INTO main.{table} ({columns}) "
        "SELECT {columns} FROM source.{table} WHERE 1 "
        "ON CONFLICT(app_id) DO UPDATE SET {updates}"
    ).format(
        table=_quote_identifier(table),
        columns=quoted_columns,
        updates=updates,
    )
    before = connection.total_changes
    connection.execute(sql)
    return connection.total_changes - before


def sync_from_investigator(
    source_database_path: Optional[Path] = None,
    database_path: Optional[Path] = None,
) -> int:
    """Copy or synchronize Phase 2 data into Validator without replacing validations."""
    source_path = Path(source_database_path) if source_database_path else get_investigator_database_path()
    target_path = Path(database_path) if database_path else get_database_path()
    source_path = source_path.resolve()
    target_path = target_path.resolve()
    if not source_path.exists():
        raise FileNotFoundError("Investigator database not found: {}".format(source_path))
    if source_path == target_path:
        raise ValueError("Investigator and Validator databases must be different files")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        shutil.copy2(source_path, target_path)
        init_database(target_path)
        with sqlite3.connect(source_path) as source:
            return source.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]

    init_database(target_path)
    with sqlite3.connect(target_path) as connection:
        connection.execute("ATTACH DATABASE ? AS source", (str(source_path),))
        try:
            synced = _sync_table(connection, "opportunities")
            synced += _sync_table(connection, "investigations")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("DETACH DATABASE source")
    return synced


__all__ = ["sync_from_investigator"]