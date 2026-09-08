"""SQLite operations owned by the Phase 3 business validator."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .config import get_database_path
except ImportError:
    from config import get_database_path


VALIDATION_STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETE", "FAILED")
RECOMMENDATIONS = ("PASS", "POSSIBLE", "PROMISING", "BUILD_CANDIDATE")
TEXT_FIELDS = (
    "product_concept",
    "target_customer",
    "value_proposition",
    "differentiation",
    "monetization",
    "willingness_to_pay",
    "apparent_market_size",
    "customer_acquisition_difficulty",
    "revenue_potential",
    "business_risks",
    "key_assumptions",
    "summary",
)


def get_connection(database_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(database_path) if database_path else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def init_database(database_path: Optional[Path] = None) -> None:
    """Add only the Phase 3 table to the copied Phase 2 database."""
    with get_connection(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS business_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETE', 'FAILED')),
                product_concept TEXT,
                target_customer TEXT,
                value_proposition TEXT,
                differentiation TEXT,
                monetization TEXT,
                willingness_to_pay TEXT,
                apparent_market_size TEXT,
                customer_acquisition_difficulty TEXT,
                revenue_potential TEXT,
                business_risks TEXT,
                key_assumptions TEXT,
                viability_score INTEGER CHECK (viability_score BETWEEN 1 AND 10),
                recommendation TEXT CHECK (recommendation IN ('PASS', 'POSSIBLE', 'PROMISING', 'BUILD_CANDIDATE')),
                summary TEXT,
                error TEXT,
                validated_at TEXT,
                FOREIGN KEY (app_id) REFERENCES opportunities(app_id)
            )
            """
        )


def select_next_opportunity(database_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Select one eligible Phase 2 opportunity for business validation."""
    with get_connection(database_path) as connection:
        opportunity_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(opportunities)")
        }
        optional_fields = (
            "app_name", "developer", "url", "description", "category",
            "rating", "review_count", "install_count", "score", "reason",
        )
        opportunity_select = ["opportunities.app_id"]
        for field in optional_fields:
            if field in opportunity_columns:
                opportunity_select.append("opportunities.{}".format(field))
            else:
                opportunity_select.append("NULL AS {}".format(field))
        row = connection.execute(
            """
            SELECT {opportunity_fields}, investigations.*,
                   investigations.id AS investigation_id,
                     investigations.recommendation AS phase2_recommendation,
                     business_validations.id AS validation_id
            FROM opportunities
            JOIN investigations ON opportunities.app_id = investigations.app_id
            LEFT JOIN business_validations
                ON opportunities.app_id = business_validations.app_id
            WHERE investigations.status = 'COMPLETE'
              AND investigations.recommendation IN ('STRONG_OPPORTUNITY', 'PROMISING')
                            AND (business_validations.id IS NULL OR business_validations.status = 'FAILED')
            ORDER BY CASE investigations.recommendation
                WHEN 'STRONG_OPPORTUNITY' THEN 0
                WHEN 'PROMISING' THEN 1
            END, investigations.final_score DESC, opportunities.app_id ASC
            LIMIT 1
            """.format(opportunity_fields=", ".join(opportunity_select))
        ).fetchone()
    return dict(row) if row else None


def create_validation(app_id: int, database_path: Optional[Path] = None) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO business_validations (app_id, status) VALUES (?, 'PENDING')",
            (app_id,),
        )
        return int(cursor.lastrowid)


def update_validation_status(
    validation_id: int,
    status: str,
    database_path: Optional[Path] = None,
    error: Optional[str] = None,
) -> None:
    if status not in VALIDATION_STATUSES:
        raise ValueError("Invalid validation status: {}".format(status))
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "UPDATE business_validations SET status = ?, error = ? WHERE id = ?",
            (status, error, validation_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Validation {} does not exist".format(validation_id))


def save_validation_result(
    validation_id: int,
    result: Dict[str, Any],
    database_path: Optional[Path] = None,
) -> None:
    fields = tuple(field for field in TEXT_FIELDS if field != "summary") + (
        "viability_score",
        "recommendation",
        "summary",
    )
    values = [result.get(field) for field in fields]
    values.extend(("COMPLETE", datetime.now(timezone.utc).isoformat(), validation_id))
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE business_validations
            SET product_concept = ?, target_customer = ?, value_proposition = ?,
                differentiation = ?, monetization = ?, willingness_to_pay = ?,
                apparent_market_size = ?, customer_acquisition_difficulty = ?,
                revenue_potential = ?, business_risks = ?, key_assumptions = ?,
                viability_score = ?, recommendation = ?, summary = ?,
                status = ?, validated_at = ?, error = NULL
            WHERE id = ?
            """,
            values,
        )
        if cursor.rowcount != 1:
            raise ValueError("Validation {} does not exist".format(validation_id))


def recover_interrupted_validations(database_path: Optional[Path] = None) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE business_validations
            SET status = 'FAILED', error = ?
            WHERE status = 'IN_PROGRESS'
            """,
            ("Recovered interrupted validation; eligible for retry.",),
        )
        return cursor.rowcount
