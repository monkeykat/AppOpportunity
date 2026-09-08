import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from Validator.analysis import validate_assessment
from Validator.business_research import collect_business_research
from Validator.database import (
    get_connection,
    init_database,
    recover_interrupted_validations,
    select_next_opportunity,
)
from Validator.handoff import sync_from_investigator
from Validator.ollama_client import OllamaClient
from Validator.validate_business import run_one_validation


VALID_RESULT = {
    "product_concept": "A focused MVP for the recurring problem.",
    "target_customer": "People who experience the problem frequently.",
    "value_proposition": "A simpler workflow than current alternatives.",
    "differentiation": "Focused experience and clearer pricing.",
    "monetization": "Subscription or paid premium features may be viable.",
    "willingness_to_pay": "Paid alternatives provide limited evidence of willingness to pay.",
    "apparent_market_size": "The available evidence suggests a reachable niche.",
    "customer_acquisition_difficulty": "Search and communities may provide initial reach.",
    "revenue_potential": "Revenue potential is plausible but unproven.",
    "business_risks": "The market may be too small and competitors may be good enough.",
    "key_assumptions": "Users must value the improvement and be reachable.",
    "viability_score": 6,
    "recommendation": "PROMISING",
    "summary": "Promising but unproven, with meaningful market and acquisition risks.",
}


class ValidatorTests(unittest.TestCase):
    def create_database(self, directory: str) -> Path:
        database_path = Path(directory) / "app_validator.db"
        with get_connection(database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id INTEGER NOT NULL UNIQUE,
                    app_name TEXT,
                    score INTEGER NOT NULL
                );
                CREATE TABLE investigations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id INTEGER NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    app_analysis TEXT,
                    user_analysis TEXT,
                    complaint_analysis TEXT,
                    competitor_analysis TEXT,
                    alternative_analysis TEXT,
                    final_score INTEGER,
                    recommendation TEXT,
                    summary TEXT,
                    raw_reviews TEXT,
                    raw_competitors TEXT,
                    raw_alternatives TEXT,
                    FOREIGN KEY (app_id) REFERENCES opportunities(app_id)
                );
                """
            )
        init_database(database_path)
        return database_path

    def insert_opportunity(self, database_path: Path, app_id: int, recommendation: str, final_score: int) -> None:
        with get_connection(database_path) as connection:
            connection.execute(
                "INSERT INTO opportunities (app_id, app_name, score) VALUES (?, ?, ?)",
                (app_id, "App {}".format(app_id), final_score),
            )
            connection.execute(
                """
                INSERT INTO investigations (
                    app_id, status, final_score, recommendation, summary
                ) VALUES (?, 'COMPLETE', ?, ?, 'Phase 2 result')
                """,
                (app_id, final_score, recommendation),
            )

    def test_selection_prioritizes_strong_and_excludes_ineligible_records(self):
        with TemporaryDirectory() as directory:
            database_path = self.create_database(directory)
            self.insert_opportunity(database_path, 1, "PROMISING", 9)
            self.insert_opportunity(database_path, 2, "STRONG_OPPORTUNITY", 6)
            self.insert_opportunity(database_path, 3, "PASS", 10)
            self.assertEqual(select_next_opportunity(database_path)["app_id"], 2)

    def test_selection_accepts_minimal_opportunities_schema(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "app_validator.db"
            with get_connection(database_path) as connection:
                connection.executescript(
                    """
                    CREATE TABLE opportunities (app_id INTEGER PRIMARY KEY, score INTEGER NOT NULL);
                    CREATE TABLE investigations (
                        id INTEGER PRIMARY KEY, app_id INTEGER NOT NULL UNIQUE,
                        status TEXT NOT NULL, final_score INTEGER, recommendation TEXT
                    );
                    """
                )
                connection.execute("INSERT INTO opportunities VALUES (99, 8)")
                connection.execute(
                    "INSERT INTO investigations VALUES (1, 99, 'COMPLETE', 8, 'PROMISING')"
                )
            init_database(database_path)
            selected = select_next_opportunity(database_path)
            self.assertEqual(selected["app_id"], 99)
            self.assertIsNone(selected["app_name"])

    def test_investigator_sync_preserves_existing_business_validation(self):
        with TemporaryDirectory() as directory:
            source_path = self.create_database(directory)
            target_path = Path(directory) / "Validator" / "app_validator.db"
            self.insert_opportunity(source_path, 10, "PROMISING", 6)

            self.assertEqual(sync_from_investigator(source_path, target_path), 1)
            with get_connection(target_path) as connection:
                connection.execute(
                    "INSERT INTO business_validations (app_id, status) VALUES (10, 'COMPLETE')"
                )
            with get_connection(source_path) as connection:
                connection.execute(
                    "UPDATE investigations SET final_score = 7 WHERE app_id = 10"
                )

            sync_from_investigator(source_path, target_path)
            with get_connection(target_path) as connection:
                investigation = connection.execute(
                    "SELECT final_score FROM investigations WHERE app_id = 10"
                ).fetchone()
                validation = connection.execute(
                    "SELECT status FROM business_validations WHERE app_id = 10"
                ).fetchone()
            self.assertEqual(investigation[0], 7)
            self.assertEqual(validation[0], "COMPLETE")

    def test_lifecycle_saves_one_complete_validation(self):
        with TemporaryDirectory() as directory:
            database_path = self.create_database(directory)
            self.insert_opportunity(database_path, 4, "PROMISING", 6)
            self.assertTrue(
                run_one_validation(
                    lambda _opportunity: {"evidence": []},
                    lambda _opportunity, _research: dict(VALID_RESULT),
                    database_path,
                )
            )
            with get_connection(database_path) as connection:
                row = connection.execute(
                    "SELECT status, viability_score, recommendation, summary FROM business_validations"
                ).fetchone()
            self.assertEqual(tuple(row), ("COMPLETE", 6, "PROMISING", VALID_RESULT["summary"]))
            self.assertIsNone(select_next_opportunity(database_path))

    def test_failure_is_recorded_and_app_can_be_retried(self):
        with TemporaryDirectory() as directory:
            database_path = self.create_database(directory)
            self.insert_opportunity(database_path, 5, "PROMISING", 6)
            self.assertFalse(
                run_one_validation(
                    lambda _opportunity: (_ for _ in ()).throw(RuntimeError("research failed")),
                    lambda _opportunity, _research: dict(VALID_RESULT),
                    database_path,
                )
            )
            with get_connection(database_path) as connection:
                row = connection.execute("SELECT status, error FROM business_validations").fetchone()
            self.assertEqual(row[0], "FAILED")
            self.assertIn("research failed", row[1])
            self.assertTrue(
                run_one_validation(
                    lambda _opportunity: {"additional_research": {}},
                    lambda _opportunity, _research: dict(VALID_RESULT),
                    database_path,
                )
            )
            with get_connection(database_path) as connection:
                rows = connection.execute(
                    "SELECT status FROM business_validations"
                ).fetchall()
            self.assertEqual([row[0] for row in rows], ["COMPLETE"])

    def test_interrupted_validation_is_recovered(self):
        with TemporaryDirectory() as directory:
            database_path = self.create_database(directory)
            self.insert_opportunity(database_path, 7, "PROMISING", 6)
            with get_connection(database_path) as connection:
                connection.execute(
                    "INSERT INTO business_validations (app_id, status) VALUES (7, 'IN_PROGRESS')"
                )
            self.assertEqual(recover_interrupted_validations(database_path), 1)
            with get_connection(database_path) as connection:
                row = connection.execute(
                    "SELECT status, error FROM business_validations"
                ).fetchone()
            self.assertEqual(row[0], "FAILED")
            self.assertIn("Recovered interrupted", row[1])

    def test_business_research_preserves_phase2_results_and_raw_evidence(self):
        package = collect_business_research({
            "app_id": 8,
            "app_name": "Example App",
            "description": "Tracks a recurring activity.",
            "app_analysis": "App analysis",
            "user_analysis": "User analysis",
            "complaint_analysis": "Complaint analysis",
            "competitor_analysis": "Competitor analysis",
            "alternative_analysis": "Alternative analysis",
            "build_difficulty": 4,
            "proprietary_dependency": 2,
            "market_potential": 7,
            "competition_level": 5,
            "final_score": 6,
            "recommendation": "PROMISING",
            "summary": "Phase 2 summary",
            "raw_reviews": '[{"rating": 2, "text": "Needs a better workflow."}]',
            "raw_competitors": '[{"url": "https://competitor.test"}]',
            "raw_alternatives": '["Spreadsheet"]',
        }, search=lambda _query: "<a href='https://example.test'>Result</a> pricing subscription")
        self.assertEqual(package["phase2_results"]["analysis"]["final_score"], 6)
        self.assertEqual(package["phase2_results"]["raw_evidence"]["reviews"][0]["rating"], 2)
        self.assertEqual(package["phase2_results"]["raw_evidence"]["alternatives"], ["Spreadsheet"])
        self.assertGreaterEqual(len(package["business_questions"]), 4)
        self.assertEqual(package["additional_research"]["pages_opened"], 4)

    def test_unique_app_validation_constraint(self):
        with TemporaryDirectory() as directory:
            database_path = self.create_database(directory)
            self.insert_opportunity(database_path, 6, "PROMISING", 6)
            with self.assertRaises(sqlite3.IntegrityError):
                with get_connection(database_path) as connection:
                    connection.execute(
                        "INSERT INTO business_validations (app_id, status) VALUES (6, 'PENDING')"
                    )
                    connection.execute(
                        "INSERT INTO business_validations (app_id, status) VALUES (6, 'PENDING')"
                    )

    def test_score_band_validation(self):
        validate_assessment(dict(VALID_RESULT))
        invalid = dict(VALID_RESULT)
        invalid["viability_score"] = 8
        with self.assertRaises(ValueError):
            validate_assessment(invalid)

    def test_ollama_client_extracts_json_from_response(self):
        import Validator.ollama_client as ollama_client

        class Response:
            def read(self):
                return b'{"response":"Assessment:\\n```json\\n{\\"ok\\": true}\\n```"}'

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        original_urlopen = ollama_client.urlopen
        ollama_client.urlopen = lambda *_args, **_kwargs: Response()
        try:
            self.assertTrue(OllamaClient().generate_json("test")["ok"])
        finally:
            ollama_client.urlopen = original_urlopen


if __name__ == "__main__":
    unittest.main()
