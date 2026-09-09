import json
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFINITION = ROOT / "4_Definition"
sys.path.insert(0, str(DEFINITION))

from analysis import build_design_prompt, validate_design  # noqa: E402
from database import (  # noqa: E402
    create_design,
    get_connection,
    init_database,
    is_ready_for_phase5,
    recover_invalid_completed_designs,
    recover_interrupted_designs,
    save_design_result,
    select_next_opportunity,
)
from handoff import sync_from_validator  # noqa: E402
from design_product import run_one_design  # noqa: E402
from ollama_client import OllamaClient  # noqa: E402


VALID_RESULT = {
    "product_name": "Working Journal",
    "product_summary": "A focused journal for one core task.",
    "target_user": "Serious hobbyists",
    "core_problem": "Record the activity quickly and review it later.",
    "product_strategy": ["BETTER_WORKFLOW"],
    "differentiation": "A faster workflow without unrelated features.",
    "design_rationale": "The design follows repeated workflow complaints.",
    "rejected_alternatives": ["A full social network"],
    "inherited_constraints": ["Local-first POC"],
    "validation_hypothesis": "Users will return if recording takes less than a minute.",
    "core_user_workflow": "Open -> Record activity -> View history",
    "minimum_validation_scope": ["Record activity", "View history"],
    "evidence_to_support_or_reject": [{
        "claim": "Recording is too slow today.",
        "source_phase": 2,
        "source_field": "complaint_patterns",
        "evidence_summary": "Users repeatedly describe multi-step entry.",
    }],
    "must_have_features": ["Record activity", "View history"],
    "nice_to_have_features": ["Cloud sync"],
    "excluded_features": ["Social network"],
    "mvp_scope": "Record one activity and view it in history.",
    "technical_considerations": ["Local database"],
    "technical_risks": [{
        "risk": "External API unavailable",
        "severity": "LOW",
        "why_it_matters": "Could affect optional enrichment.",
        "possible_mitigation": "Use local data.",
        "blocks_validation": False,
    }],
    "success_criteria": ["A user completes the workflow without instructions."],
    "design_score": 7,
    "recommendation": "READY_FOR_POC",
}


class Phase4Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "app_designer.db"
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE opportunities (app_id INTEGER PRIMARY KEY, app_name TEXT);
                CREATE TABLE investigations (
                    id INTEGER PRIMARY KEY, app_id INTEGER UNIQUE, status TEXT,
                    final_score INTEGER, recommendation TEXT
                );
                CREATE TABLE business_validations (
                    id INTEGER PRIMARY KEY, app_id INTEGER UNIQUE, status TEXT,
                    viability_score INTEGER, recommendation TEXT, summary TEXT,
                    validated_at TEXT
                );
                INSERT INTO opportunities VALUES (1, 'Example App');
                INSERT INTO investigations VALUES (10, 1, 'COMPLETE', 8, 'PROMISING');
                INSERT INTO business_validations VALUES
                    (20, 1, 'COMPLETE', 8, 'BUILD_CANDIDATE', 'Strong fit.', '2026-09-08T00:00:00+00:00');
                """
            )
        init_database(self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_design_passes_validation(self):
        validate_design(VALID_RESULT)

    def test_prompt_includes_real_phase2_investigation_fields(self):
        prompt = build_design_prompt({
            "app_name": "Example App",
            "description": "An example app.",
            "category": "Productivity",
            "reason": "Repeated workflow friction.",
            "app_analysis": "The app has a broad workflow.",
            "user_analysis": "Small teams use the app.",
            "complaint_analysis": "Users report too many required fields.",
            "competitor_analysis": "Competitors focus on larger teams.",
            "alternative_analysis": "Users fall back to spreadsheets.",
            "summary": "The opportunity is focused but underserved.",
            "final_score": 8,
            "product_concept": "A simpler workflow.",
            "target_customer": "Small teams",
            "value_proposition": "Faster daily entry.",
            "differentiation": "Narrower workflow.",
            "business_risks": "Limited segment.",
            "key_assumptions": "Users value speed.",
            "viability_score": 8,
            "phase3_recommendation": "BUILD_CANDIDATE",
        })
        self.assertIn("Users report too many required fields.", prompt)
        self.assertIn("Competitors focus on larger teams.", prompt)
        self.assertIn("The opportunity is focused but underserved.", prompt)

    def test_score_recommendation_mismatch_is_rejected(self):
        result = dict(VALID_RESULT, design_score=3, recommendation="READY_FOR_POC")
        with self.assertRaises(ValueError):
            validate_design(result)

    def test_unexpected_output_field_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_design(dict(VALID_RESULT, extra_field="not part of the schema"))

    def test_blocking_risk_is_rejected(self):
        risks = [{
            "risk": "Required dependency",
            "severity": "HIGH",
            "why_it_matters": "Core workflow cannot run.",
            "possible_mitigation": "None yet.",
            "blocks_validation": True,
        }]
        with self.assertRaises(ValueError):
            validate_design(dict(VALID_RESULT, technical_risks=risks))

    def test_non_observable_evidence_is_rejected(self):
        evidence = [{
            "claim": "The product is better.",
            "source_phase": 2,
            "source_field": "summary",
            "evidence_summary": "The product is better.",
        }]
        with self.assertRaises(ValueError):
            validate_design(dict(VALID_RESULT, evidence_to_support_or_reject=evidence))

    def test_invalid_saved_design_is_not_ready_for_phase5(self):
        snapshot = {
            "id": 20, "app_id": 1, "status": "COMPLETE",
            "viability_score": 8, "recommendation": "BUILD_CANDIDATE",
            "summary": "Strong fit.", "validated_at": "2026-09-08T00:00:00+00:00",
        }
        design_id = create_design(1, 20, snapshot["validated_at"], snapshot, self.database_path)
        save_design_result(design_id, VALID_RESULT, 20, snapshot["validated_at"], snapshot, self.database_path)
        with get_connection(self.database_path) as connection:
            connection.execute(
                "UPDATE product_designs SET must_have_features = ? WHERE id = ?",
                (json.dumps(["Unrelated capability"]), design_id),
            )
            row = dict(connection.execute(
                "SELECT * FROM product_designs WHERE id = ?", (design_id,)
            ).fetchone())
        self.assertFalse(is_ready_for_phase5(row))

    def test_invalid_completed_design_is_recovered_for_redesign(self):
        snapshot = {
            "id": 20, "app_id": 1, "status": "COMPLETE",
            "viability_score": 8, "recommendation": "BUILD_CANDIDATE",
            "summary": "Strong fit.", "validated_at": "2026-09-08T00:00:00+00:00",
        }
        design_id = create_design(1, 20, snapshot["validated_at"], snapshot, self.database_path)
        save_design_result(design_id, VALID_RESULT, 20, snapshot["validated_at"], snapshot, self.database_path)
        with get_connection(self.database_path) as connection:
            connection.execute(
                "UPDATE product_designs SET must_have_features = ? WHERE id = ?",
                (json.dumps(["Unrelated capability"]), design_id),
            )
        self.assertEqual(recover_invalid_completed_designs(self.database_path), 1)
        with get_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT status, error FROM product_designs WHERE id = ?", (design_id,)
            ).fetchone()
        self.assertEqual(row["status"], "STALE")
        self.assertIn("redesign required", row["error"])

    def test_feature_not_represented_in_workflow_is_rejected(self):
        result = dict(VALID_RESULT, must_have_features=["Add social network"])
        with self.assertRaises(ValueError):
            validate_design(result)

    def test_missing_required_field_is_rejected(self):
        result = dict(VALID_RESULT)
        result.pop("evidence_to_support_or_reject")
        with self.assertRaises(ValueError):
            validate_design(result)

    def test_selection_and_atomic_save(self):
        selected = select_next_opportunity(self.database_path)
        self.assertEqual(selected["app_id"], 1)
        snapshot = {
            "id": 20, "app_id": 1, "status": "COMPLETE",
            "viability_score": 8, "recommendation": "BUILD_CANDIDATE",
            "summary": "Strong fit.", "validated_at": "2026-09-08T00:00:00+00:00",
        }
        design_id = create_design(1, 20, snapshot["validated_at"], snapshot, self.database_path)
        save_design_result(design_id, VALID_RESULT, 20, snapshot["validated_at"], snapshot, self.database_path)
        with get_connection(self.database_path) as connection:
            row = connection.execute("SELECT * FROM product_designs WHERE id = ?", (design_id,)).fetchone()
        self.assertEqual(row["status"], "COMPLETE")
        self.assertEqual(json.loads(row["must_have_features"]), VALID_RESULT["must_have_features"])
        self.assertEqual(row["recommendation"], "READY_FOR_POC")
        self.assertIsNone(row["error"])
        self.assertIsNone(select_next_opportunity(self.database_path))

    def test_completed_design_is_ready_for_phase5(self):
        snapshot = {
            "id": 20, "app_id": 1, "status": "COMPLETE",
            "viability_score": 8, "recommendation": "BUILD_CANDIDATE",
            "summary": "Strong fit.", "validated_at": "2026-09-08T00:00:00+00:00",
        }
        design_id = create_design(1, 20, snapshot["validated_at"], snapshot, self.database_path)
        save_design_result(design_id, VALID_RESULT, 20, snapshot["validated_at"], snapshot, self.database_path)
        with get_connection(self.database_path) as connection:
            row = connection.execute("SELECT * FROM product_designs WHERE id = ?", (design_id,)).fetchone()
        self.assertTrue(is_ready_for_phase5(dict(row)))

    def test_interrupted_design_is_recovered_for_retry(self):
        snapshot = {
            "id": 20, "app_id": 1, "status": "COMPLETE",
            "viability_score": 8, "recommendation": "BUILD_CANDIDATE",
            "summary": "Strong fit.", "validated_at": "2026-09-08T00:00:00+00:00",
        }
        design_id = create_design(1, 20, snapshot["validated_at"], snapshot, self.database_path)
        with get_connection(self.database_path) as connection:
            connection.execute("UPDATE product_designs SET status = 'IN_PROGRESS' WHERE id = ?", (design_id,))
        self.assertEqual(recover_interrupted_designs(self.database_path), 1)
        with get_connection(self.database_path) as connection:
            row = connection.execute("SELECT status, error FROM product_designs WHERE id = ?", (design_id,)).fetchone()
        self.assertEqual(row["status"], "FAILED")
        self.assertIn("Recovered interrupted", row["error"])

    def test_schema_rejects_duplicate_app_and_invalid_foreign_key(self):
        snapshot = {
            "id": 20, "app_id": 1, "status": "COMPLETE",
            "viability_score": 8, "recommendation": "BUILD_CANDIDATE",
            "summary": "Strong fit.", "validated_at": "2026-09-08T00:00:00+00:00",
        }
        create_design(1, 20, snapshot["validated_at"], snapshot, self.database_path)
        with self.assertRaises(sqlite3.IntegrityError):
            create_design(1, 20, snapshot["validated_at"], snapshot, self.database_path)
        with self.assertRaises(sqlite3.IntegrityError):
            create_design(99, 20, snapshot["validated_at"], snapshot, self.database_path)

    def test_selection_prioritizes_build_candidate(self):
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("INSERT INTO opportunities VALUES (2, 'Promising App')")
            connection.execute("INSERT INTO investigations VALUES (11, 2, 'COMPLETE', 9, 'PROMISING')")
            connection.execute(
                "INSERT INTO business_validations VALUES (21, 2, 'COMPLETE', 10, 'PROMISING', 'Promising.', '2026-09-08T00:00:00+00:00')"
            )
        self.assertEqual(select_next_opportunity(self.database_path)["app_id"], 1)

    def test_handoff_marks_completed_design_stale_when_source_changes(self):
        source_path = Path(self.temp_dir.name) / "app_validator.db"
        with sqlite3.connect(source_path) as connection:
            connection.executescript(
                """
                CREATE TABLE opportunities (app_id INTEGER PRIMARY KEY, app_name TEXT);
                CREATE TABLE investigations (
                    id INTEGER PRIMARY KEY, app_id INTEGER UNIQUE, status TEXT,
                    final_score INTEGER, recommendation TEXT
                );
                CREATE TABLE business_validations (
                    id INTEGER PRIMARY KEY, app_id INTEGER UNIQUE, status TEXT,
                    viability_score INTEGER, recommendation TEXT, summary TEXT,
                    validated_at TEXT
                );
                INSERT INTO opportunities VALUES (1, 'Example App');
                INSERT INTO investigations VALUES (10, 1, 'COMPLETE', 8, 'PROMISING');
                INSERT INTO business_validations VALUES
                    (20, 1, 'COMPLETE', 8, 'BUILD_CANDIDATE', 'Original.', '2026-09-08T00:00:00+00:00');
                """
            )
        target_path = Path(self.temp_dir.name) / "definition.db"
        sync_from_validator(source_path, target_path)
        snapshot = {
            "id": 20, "app_id": 1, "status": "COMPLETE",
            "viability_score": 8, "recommendation": "BUILD_CANDIDATE",
            "summary": "Original.", "validated_at": "2026-09-08T00:00:00+00:00",
        }
        design_id = create_design(1, 20, snapshot["validated_at"], snapshot, target_path)
        with sqlite3.connect(target_path) as connection:
            connection.execute(
                "UPDATE product_designs SET status = 'COMPLETE' WHERE id = ?",
                (design_id,),
            )
        with sqlite3.connect(source_path) as connection:
            connection.execute(
                "UPDATE business_validations SET summary = 'Changed.' WHERE id = 20"
            )
        sync_from_validator(source_path, target_path)
        with get_connection(target_path) as connection:
            status = connection.execute(
                "SELECT status FROM product_designs WHERE id = ?", (design_id,)
            ).fetchone()[0]
        self.assertEqual(status, "STALE")

    def test_mocked_product_definition_iteration(self):
        self.assertTrue(run_one_design(analyze=lambda opportunity: VALID_RESULT, database_path=self.database_path))
        with get_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT status, recommendation FROM product_designs WHERE app_id = 1"
            ).fetchone()
        self.assertEqual(tuple(row), ("COMPLETE", "READY_FOR_POC"))


if __name__ == "__main__":
    unittest.main()
