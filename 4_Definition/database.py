"""SQLite persistence for Phase 4 product definitions."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .config import get_database_path
except ImportError:
    from config import get_database_path


STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETE", "FAILED", "STALE")
RECOMMENDATIONS = ("PASS", "DESIGN_REVIEW", "READY_FOR_POC")
STRATEGIES = (
    "SIMPLER", "CHEAPER", "MORE_SPECIALIZED", "BETTER_WORKFLOW",
    "BETTER_USER_EXPERIENCE", "DIFFERENT_AUDIENCE", "SOLVE_MISSING_PROBLEM",
)
JSON_FIELDS = (
    "product_strategy", "rejected_alternatives", "inherited_constraints",
    "evidence_to_support_or_reject", "must_have_features", "nice_to_have_features",
    "excluded_features", "technical_considerations", "technical_risks",
    "success_criteria", "minimum_validation_scope", "source_validation_snapshot",
)
TEXT_FIELDS = (
    "product_name", "product_summary", "target_user", "core_problem",
    "differentiation", "design_rationale", "validation_hypothesis",
    "core_user_workflow", "minimum_validation_scope", "mvp_scope",
    "designed_at", "error", "source_validated_at",
)


def get_connection(database_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(database_path) if database_path else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def init_database(database_path: Optional[Path] = None) -> None:
    with get_connection(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS product_designs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETE', 'FAILED', 'STALE')),
                product_name TEXT,
                product_summary TEXT,
                target_user TEXT,
                core_problem TEXT,
                product_strategy TEXT,
                differentiation TEXT,
                design_rationale TEXT,
                rejected_alternatives TEXT,
                inherited_constraints TEXT,
                validation_hypothesis TEXT,
                core_user_workflow TEXT,
                minimum_validation_scope TEXT,
                evidence_to_support_or_reject TEXT,
                must_have_features TEXT,
                nice_to_have_features TEXT,
                excluded_features TEXT,
                mvp_scope TEXT,
                technical_considerations TEXT,
                technical_risks TEXT,
                success_criteria TEXT,
                design_score INTEGER CHECK (design_score BETWEEN 1 AND 10),
                recommendation TEXT CHECK (recommendation IN ('PASS', 'DESIGN_REVIEW', 'READY_FOR_POC')),
                created_at TEXT NOT NULL,
                designed_at TEXT,
                error TEXT,
                source_validation_id INTEGER NOT NULL,
                source_validated_at TEXT,
                source_validation_snapshot TEXT NOT NULL,
                FOREIGN KEY (app_id) REFERENCES opportunities(app_id),
                FOREIGN KEY (source_validation_id) REFERENCES business_validations(id)
            )
            """
        )


def select_next_opportunity(database_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    with get_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT opportunities.*, investigations.*,
                   investigations.id AS investigation_id,
                   business_validations.id AS source_validation_id,
                   business_validations.status AS source_validation_status,
                   business_validations.validated_at AS source_validated_at,
                   business_validations.viability_score,
                   business_validations.recommendation AS phase3_recommendation,
                   business_validations.summary AS source_validation_summary,
                   product_designs.id AS design_id,
                   product_designs.status AS design_status
            FROM business_validations
            JOIN opportunities ON opportunities.app_id = business_validations.app_id
            JOIN investigations ON investigations.app_id = business_validations.app_id
            LEFT JOIN product_designs ON product_designs.app_id = business_validations.app_id
            WHERE business_validations.status = 'COMPLETE'
              AND business_validations.recommendation IN ('BUILD_CANDIDATE', 'PROMISING')
              AND investigations.status = 'COMPLETE'
              AND (product_designs.id IS NULL OR product_designs.status IN ('FAILED', 'STALE'))
            ORDER BY CASE business_validations.recommendation
                WHEN 'BUILD_CANDIDATE' THEN 0
                WHEN 'PROMISING' THEN 1
            END, business_validations.viability_score DESC, opportunities.app_id ASC
            LIMIT 1
            """
        ).fetchone()
    return dict(row) if row else None


def create_design(
    app_id: int,
    source_validation_id: int,
    source_validated_at: Optional[str],
    source_snapshot: Dict[str, Any],
    database_path: Optional[Path] = None,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO product_designs
                (app_id, status, created_at, source_validation_id,
                 source_validated_at, source_validation_snapshot)
            VALUES (?, 'PENDING', ?, ?, ?, ?)
            """,
            (app_id, now, source_validation_id, source_validated_at, json.dumps(source_snapshot, sort_keys=True)),
        )
        return int(cursor.lastrowid)


def update_design_status(
    design_id: int,
    status: str,
    database_path: Optional[Path] = None,
    error: Optional[str] = None,
) -> None:
    if status not in STATUSES:
        raise ValueError(f"Invalid product design status: {status}")
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "UPDATE product_designs SET status = ?, error = ? WHERE id = ?",
            (status, error, design_id),
        )
        if cursor.rowcount != 1:
            raise ValueError(f"Product design {design_id} does not exist")


def save_design_result(
    design_id: int,
    result: Dict[str, Any],
    source_validation_id: int,
    source_validated_at: Optional[str],
    source_snapshot: Dict[str, Any],
    database_path: Optional[Path] = None,
) -> None:
    encoded = {
        field: json.dumps(result[field], sort_keys=True)
        for field in JSON_FIELDS[:-1]
    }
    parameters = [
        result.get("product_name"), result["product_summary"],
        encoded["product_strategy"], encoded["rejected_alternatives"],
        encoded["inherited_constraints"], encoded["evidence_to_support_or_reject"],
        encoded["must_have_features"], encoded["nice_to_have_features"],
        encoded["excluded_features"], encoded["technical_considerations"],
        encoded["technical_risks"], encoded["success_criteria"],
        result["target_user"], result["core_problem"], result["differentiation"],
        result["design_rationale"], result["validation_hypothesis"],
        result["core_user_workflow"], encoded["minimum_validation_scope"],
        result["mvp_scope"], datetime.now(timezone.utc).isoformat(), None,
        source_validation_id, source_validated_at,
        json.dumps(source_snapshot, sort_keys=True), result["design_score"],
        result["recommendation"], design_id,
    ]
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE product_designs SET
                product_name = ?, product_summary = ?,
                product_strategy = ?, rejected_alternatives = ?, inherited_constraints = ?,
                evidence_to_support_or_reject = ?, must_have_features = ?,
                nice_to_have_features = ?, excluded_features = ?,
                technical_considerations = ?, technical_risks = ?, success_criteria = ?,
                target_user = ?, core_problem = ?, differentiation = ?, design_rationale = ?,
                validation_hypothesis = ?, core_user_workflow = ?, minimum_validation_scope = ?,
                mvp_scope = ?, designed_at = ?, error = ?, source_validation_id = ?,
                source_validated_at = ?, source_validation_snapshot = ?,
                design_score = ?, recommendation = ?, status = 'COMPLETE'
            WHERE id = ?
            """,
            parameters,
        )
        if cursor.rowcount != 1:
            raise ValueError(f"Product design {design_id} does not exist")


def recover_interrupted_designs(database_path: Optional[Path] = None) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "UPDATE product_designs SET status = 'FAILED', error = ? WHERE status = 'IN_PROGRESS'",
            ("Recovered interrupted product design; eligible for retry.",),
        )
        return cursor.rowcount


def _saved_design_is_valid(design: Dict[str, Any]) -> bool:
    try:
        from .analysis import validate_design
    except ImportError:
        from analysis import validate_design

    validation_result = dict(design)
    try:
        for field in JSON_FIELDS[:-1]:
            if isinstance(validation_result.get(field), str):
                validation_result[field] = json.loads(validation_result[field])
        validation_result = {
            field: validation_result[field]
            for field in validation_result
            if field in {
                "product_name", "product_summary", "target_user", "core_problem",
                "product_strategy", "differentiation", "design_rationale",
                "rejected_alternatives", "inherited_constraints", "validation_hypothesis",
                "core_user_workflow", "minimum_validation_scope",
                "evidence_to_support_or_reject", "must_have_features",
                "nice_to_have_features", "excluded_features", "mvp_scope",
                "technical_considerations", "technical_risks", "success_criteria",
                "design_score", "recommendation",
            }
        }
        validate_design(validation_result)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False
    return True


def recover_invalid_completed_designs(database_path: Optional[Path] = None) -> int:
    """Move completed rows that fail current validation back to redesign."""
    changed = 0
    with get_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM product_designs WHERE status = 'COMPLETE'"
        ).fetchall()
        for row in rows:
            if not _saved_design_is_valid(dict(row)):
                connection.execute(
                    "UPDATE product_designs SET status = 'STALE', error = ? WHERE id = ?",
                    ("Saved design no longer satisfies current validation; redesign required.", row["id"]),
                )
                changed += 1
    return changed


def is_ready_for_phase5(design: Dict[str, Any]) -> bool:
    """Return whether a saved design satisfies the Phase 5 handoff contract."""
    if design.get("status") != "COMPLETE" or design.get("recommendation") != "READY_FOR_POC":
        return False
    if not design.get("source_validation_id") or not design.get("source_validated_at"):
        return False
    return _saved_design_is_valid(design)


__all__ = [
    "JSON_FIELDS", "RECOMMENDATIONS", "STATUSES", "STRATEGIES",
    "create_design", "get_connection", "init_database", "recover_interrupted_designs",
    "recover_invalid_completed_designs", "save_design_result", "select_next_opportunity",
    "update_design_status",
    "is_ready_for_phase5",
]
