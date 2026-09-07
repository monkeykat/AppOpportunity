"""SQLite schema and operations owned by Phase 2."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_database_path


INVESTIGATION_STATUSES = ("PENDING", "IN_PROGRESS", "COMPLETE", "FAILED")
RECOMMENDATIONS = (
    "PASS",
    "INVESTIGATE_FURTHER",
    "PROMISING",
    "STRONG_OPPORTUNITY",
)


def get_connection(database_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a connection to the Phase 2 database."""
    path = Path(database_path) if database_path else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def init_database(database_path: Optional[Path] = None) -> None:
    """Create the independent Phase 2 schema if it does not exist."""
    with get_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL UNIQUE,
                app_name TEXT,
                developer TEXT,
                url TEXT,
                description TEXT,
                category TEXT,
                rating REAL,
                review_count INTEGER,
                install_count TEXT,
                score INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETE', 'FAILED')),
                app_analysis TEXT,
                user_analysis TEXT,
                complaint_analysis TEXT,
                competitor_analysis TEXT,
                alternative_analysis TEXT,
                build_difficulty INTEGER CHECK (build_difficulty BETWEEN 1 AND 10),
                proprietary_dependency INTEGER CHECK (proprietary_dependency BETWEEN 1 AND 10),
                market_potential INTEGER CHECK (market_potential BETWEEN 1 AND 10),
                competition_level INTEGER CHECK (competition_level BETWEEN 1 AND 10),
                final_score INTEGER CHECK (final_score BETWEEN 1 AND 10),
                recommendation TEXT CHECK (recommendation IN ('PASS', 'INVESTIGATE_FURTHER', 'PROMISING', 'STRONG_OPPORTUNITY')),
                summary TEXT,
                error TEXT,
                investigated_at TEXT,
                FOREIGN KEY (app_id) REFERENCES opportunities(app_id)
            );
            """
        )


def select_next_opportunity(database_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Select the highest-scoring opportunity without an investigation."""
    with get_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT opportunities.*
            FROM opportunities
            LEFT JOIN investigations ON opportunities.app_id = investigations.app_id
            WHERE investigations.id IS NULL
            ORDER BY opportunities.score DESC, opportunities.id ASC
            LIMIT 1
            """
        ).fetchone()
    return dict(row) if row else None


def create_investigation(app_id: int, database_path: Optional[Path] = None) -> int:
    """Create the pending record before research begins."""
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO investigations (app_id, status) VALUES (?, ?)",
            (app_id, "PENDING"),
        )
        return int(cursor.lastrowid)


def update_investigation_status(
    investigation_id: int,
    status: str,
    database_path: Optional[Path] = None,
    error: Optional[str] = None,
) -> None:
    """Update a run status while preserving failure context."""
    if status not in INVESTIGATION_STATUSES:
        raise ValueError("Invalid investigation status: {}".format(status))
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "UPDATE investigations SET status = ?, error = ? WHERE id = ?",
            (status, error, investigation_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Investigation {} does not exist".format(investigation_id))


def save_investigation_result(
    investigation_id: int,
    result: Dict[str, Any],
    database_path: Optional[Path] = None,
) -> None:
    """Persist a validated completed investigation result."""
    from analysis import validate_assessment

    validate_assessment(result)
    fields = (
        "app_analysis",
        "user_analysis",
        "complaint_analysis",
        "competitor_analysis",
        "alternative_analysis",
        "build_difficulty",
        "proprietary_dependency",
        "market_potential",
        "competition_level",
        "final_score",
        "recommendation",
        "summary",
    )
    values = [result.get(field) for field in fields]
    values.extend(("COMPLETE", datetime.now(timezone.utc).isoformat(), investigation_id))
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE investigations
            SET app_analysis = ?, user_analysis = ?, complaint_analysis = ?,
                competitor_analysis = ?, alternative_analysis = ?,
                build_difficulty = ?, proprietary_dependency = ?,
                market_potential = ?, competition_level = ?, final_score = ?,
                recommendation = ?, summary = ?, status = ?, investigated_at = ?, error = NULL
            WHERE id = ?
            """,
            values,
        )
        if cursor.rowcount != 1:
            raise ValueError("Investigation {} does not exist".format(investigation_id))