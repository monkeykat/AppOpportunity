"""Copy and synchronize Validator data into Phase 4's private database."""

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

try:
    from .config import get_database_path, get_validator_database_path
    from .database import init_database
except ImportError:
    from config import get_database_path, get_validator_database_path
    from database import init_database


def _sync_table(connection: sqlite3.Connection, table: str, conflict_column: str = "app_id") -> int:
    source_columns = {row[1] for row in connection.execute(f"PRAGMA source.table_info({table})")}
    target_columns = {row[1] for row in connection.execute(f"PRAGMA main.table_info({table})")}
    columns = [conflict_column] if conflict_column in source_columns and conflict_column in target_columns else []
    columns.extend(sorted((source_columns & target_columns) - {"id", conflict_column}))
    if not columns:
        return 0
    quoted = ", ".join('"{}"'.format(column) for column in columns)
    updates = ", ".join(
        '"{0}" = excluded."{0}"'.format(column)
        for column in columns if column != conflict_column and column != "id"
    )
    before = connection.total_changes
    connection.execute(
        f"INSERT INTO main.{table} ({quoted}) SELECT {quoted} FROM source.{table} "
        f"WHERE 1 ON CONFLICT({conflict_column}) DO UPDATE SET {updates}"
    )
    return connection.total_changes - before


def _mark_stale(connection: sqlite3.Connection) -> int:
    rows = connection.execute(
        """
         SELECT product_designs.id AS design_id,
             product_designs.source_validation_snapshot,
             business_validations.id AS validation_id,
             business_validations.app_id AS validation_app_id,
             business_validations.status AS validation_status,
             business_validations.viability_score,
             business_validations.recommendation,
             business_validations.summary,
             business_validations.validated_at
        FROM product_designs
        JOIN business_validations ON business_validations.id = product_designs.source_validation_id
        WHERE product_designs.status = 'COMPLETE'
        """
    ).fetchall()
    changed = 0
    for row in rows:
        current = {
            "id": row["validation_id"],
            "app_id": row["validation_app_id"],
            "status": row["validation_status"],
            "viability_score": row["viability_score"],
            "recommendation": row["recommendation"],
            "summary": row["summary"],
            "validated_at": row["validated_at"],
        }
        if json.dumps(current, sort_keys=True) != row["source_validation_snapshot"]:
            connection.execute(
                "UPDATE product_designs SET status = 'STALE', error = ? WHERE id = ?",
                ("Source Phase 3 validation changed; redesign required.", row["design_id"]),
            )
            changed += 1
    return changed


def sync_from_validator(source_database_path: Optional[Path] = None, database_path: Optional[Path] = None) -> int:
    source = Path(source_database_path) if source_database_path else get_validator_database_path()
    target = Path(database_path) if database_path else get_database_path()
    source, target = source.resolve(), target.resolve()
    if not source.exists():
        raise FileNotFoundError(f"Validator database not found: {source}")
    if source == target:
        raise ValueError("Validator and Definition databases must be different files")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    init_database(target)
    with sqlite3.connect(target) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        connection.execute("ATTACH DATABASE ? AS source", (str(source),))
        try:
            synced = _sync_table(connection, "opportunities")
            synced += _sync_table(connection, "investigations")
            synced += _sync_table(connection, "business_validations")
            synced += _mark_stale(connection)
            connection.commit()
        finally:
            connection.execute("DETACH DATABASE source")
    return synced


__all__ = ["sync_from_validator"]
