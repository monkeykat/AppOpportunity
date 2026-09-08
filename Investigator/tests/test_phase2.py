import sqlite3
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis import validate_assessment
from boundary_check import assert_unchanged, snapshot_files
from database import get_connection, recover_interrupted_investigations, select_next_opportunity
from handoff import import_opportunities, sync_from_scout
from investigate import analyze_with_ollama, run_one_investigation
from ollama_client import OllamaClient
from research import collect_research


VALID_RESULT = {
    "app_analysis": "The app solves a defined problem.",
    "user_analysis": "Users have a recurring need.",
    "complaint_analysis": "Complaints suggest solvable gaps.",
    "competitor_analysis": "Several competitors exist.",
    "alternative_analysis": "Users also use manual workarounds.",
    "build_difficulty": 4,
    "proprietary_dependency": 3,
    "market_potential": 7,
    "competition_level": 5,
    "final_score": 6,
    "recommendation": "PROMISING",
    "summary": "A plausible opportunity based on available evidence.",
    "strongest_argument_against": "The market may be too small to support another product.",
}


class Phase2Tests(unittest.TestCase):
    def test_ollama_client_extracts_json_from_prose(self):
        import ollama_client

        class Response:
            def read(self):
                return b'{"response":"Here is the result:\\n```json\\n{\\"ok\\": true}\\n```"}'

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        original_urlopen = ollama_client.urlopen
        ollama_client.urlopen = lambda *_args, **_kwargs: Response()
        try:
            self.assertEqual(OllamaClient().generate_json("test")["ok"], True)
        finally:
            ollama_client.urlopen = original_urlopen

    def test_ollama_client_accepts_thinking_json_when_response_empty(self):
        import ollama_client

        class Response:
            def read(self):
                return b'{"response":"","thinking":"{\\"ok\\": true}"}'

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

    def test_explicit_boundary_snapshot(self):
        with TemporaryDirectory() as directory:
            protected = Path(directory) / "phase1"
            protected.mkdir()
            source = protected / "source.db"
            source.write_bytes(b"phase 1 data")
            before = snapshot_files([protected])
            handoff_target = Path(directory) / "phase2.db"
            import_opportunities([{"app_id": 10, "score": 8}], handoff_target)
            assert_unchanged(before, [protected])

    def test_handoff_adds_new_opportunities_without_overwriting_existing(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "investigator.db"
            import_opportunities(
                [{"app_id": 1, "app_name": "Original", "score": 5}],
                database_path,
            )
            added = import_opportunities(
                [
                    {"app_id": 1, "app_name": "Changed", "score": 9},
                    {"app_id": 2, "app_name": "New", "score": 7},
                ],
                database_path,
            )

            self.assertEqual(added, 1)
            with get_connection(database_path) as connection:
                rows = connection.execute(
                    "SELECT app_id, app_name, score FROM opportunities ORDER BY app_id"
                ).fetchall()
            self.assertEqual([tuple(row) for row in rows], [(1, "Original", 5), (2, "New", 7)])

    def test_sync_from_scout_adds_and_updates_opportunities(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            scout_path = root / "Scout" / "src" / "app_scout.db"
            scout_path.parent.mkdir(parents=True)
            phase_2_path = root / "Investigator" / "app_investigator.db"

            with sqlite3.connect(scout_path) as connection:
                connection.executescript(
                    """
                    CREATE TABLE apps (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        developer TEXT,
                        url TEXT,
                        description TEXT,
                        category TEXT,
                        rating REAL,
                        review_count INTEGER,
                        install_count TEXT
                    );
                    CREATE TABLE opportunities (
                        id INTEGER PRIMARY KEY,
                        app_id INTEGER UNIQUE,
                        app_name TEXT,
                        score INTEGER,
                        reason TEXT
                    );
                    INSERT INTO apps VALUES
                        (1, 'Original', 'Dev', 'https://original.test', 'Old', 'Tools', 3.0, 10, '1000'),
                        (2, 'New', 'Dev', 'https://new.test', 'New', 'Tools', 2.0, 20, '2000');
                    INSERT INTO opportunities VALUES
                        (1, 1, 'Original', 5, 'Original reason'),
                        (2, 2, 'New', 6, 'New reason');
                    """
                )

            import_opportunities(
                [{"app_id": 1, "app_name": "Existing", "score": 9}],
                phase_2_path,
            )
            self.assertEqual(sync_from_scout(scout_path, phase_2_path), 2)
            with get_connection(phase_2_path) as connection:
                rows = connection.execute(
                    "SELECT app_id, app_name, score FROM opportunities ORDER BY app_id"
                ).fetchall()
            self.assertEqual(
                [tuple(row) for row in rows],
                [(1, "Original", 5), (2, "New", 6)],
            )

    def test_ollama_prompt_requests_complete_assessment(self):
        class PromptClient:
            def __init__(self):
                self.prompt = ""

            def generate_json(self, prompt, **_kwargs):
                self.prompt = prompt
                return dict(VALID_RESULT)

        client = PromptClient()
        result = analyze_with_ollama(
            {"app_name": "Example", "score": 8},
            {"reviews": [], "competitors": [], "alternatives": []},
            client,
        )
        self.assertEqual(result["recommendation"], "PROMISING")
        for field in (
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
            "strongest_argument_against",
        ):
            self.assertIn(field, client.prompt)
        self.assertIn("Do not return bare scores", client.prompt)
        self.assertIn("market_potential in user_analysis", client.prompt)

    def test_lifecycle_and_selection(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "investigator.db"
            import_opportunities(
                [
                    {"app_id": 1, "app_name": "Lower", "score": 5},
                    {"app_id": 2, "app_name": "Higher", "score": 9},
                ],
                database_path,
            )

            def research(_opportunity):
                return {
                    "sources": [],
                    "errors": [],
                    "reviews": [{"rating": 1, "text": "Data loss"}],
                    "competitors": [{"url": "https://competitor.test"}],
                    "alternatives": [{"url": "https://notes.test"}],
                }

            def analyze(_opportunity, _evidence):
                return dict(VALID_RESULT)

            self.assertTrue(run_one_investigation(research, analyze, database_path))
            with get_connection(database_path) as connection:
                row = connection.execute(
                    "SELECT status, final_score, investigated_at, summary FROM investigations WHERE app_id = 2"
                ).fetchone()
                self.assertEqual(tuple(row[:3]), ("COMPLETE", 6, row[2]))
                self.assertIn("Strongest argument against", row[3])
                evidence = connection.execute(
                    "SELECT raw_reviews, raw_competitors, raw_alternatives FROM investigations WHERE app_id = 2"
                ).fetchone()
                self.assertEqual(json.loads(evidence[0])[0]["rating"], 1)
                self.assertEqual(json.loads(evidence[1])[0]["url"], "https://competitor.test")
                self.assertEqual(json.loads(evidence[2])[0]["url"], "https://notes.test")
            self.assertEqual(select_next_opportunity(database_path)["app_id"], 1)

    def test_failure_preserves_error(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "investigator.db"
            import_opportunities([{"app_id": 3, "score": 4}], database_path)

            def failing_research(_opportunity):
                raise RuntimeError("research unavailable")

            self.assertFalse(run_one_investigation(failing_research, lambda _o, _e: VALID_RESULT, database_path))
            with get_connection(database_path) as connection:
                row = connection.execute("SELECT status, error FROM investigations").fetchone()
            self.assertEqual(row[0], "FAILED")
            self.assertIn("research unavailable", row[1])
            self.assertEqual(select_next_opportunity(database_path)["app_id"], 3)

            self.assertTrue(run_one_investigation(lambda _o: {"reviews": [], "competitors": [], "alternatives": []}, lambda _o, _e: dict(VALID_RESULT), database_path))
            with get_connection(database_path) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM investigations").fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT status FROM investigations").fetchone()[0], "COMPLETE")

    def test_interrupted_investigation_is_recovered_for_retry(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "investigator.db"
            import_opportunities([{"app_id": 30, "score": 6}], database_path)
            with get_connection(database_path) as connection:
                connection.execute(
                    "INSERT INTO investigations (app_id, status) VALUES (30, 'IN_PROGRESS')"
                )
            self.assertEqual(recover_interrupted_investigations(database_path), 1)
            with get_connection(database_path) as connection:
                row = connection.execute("SELECT status, error FROM investigations").fetchone()
            self.assertEqual(row[0], "FAILED")
            self.assertIn("Recovered interrupted", row[1])
            self.assertEqual(select_next_opportunity(database_path)["app_id"], 30)

    def test_constraints_and_research(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "investigator.db"
            import_opportunities([{"app_id": 4, "score": 3}], database_path)
            with self.assertRaises(sqlite3.IntegrityError):
                with get_connection(database_path) as connection:
                    connection.execute("INSERT INTO investigations (app_id, status) VALUES (4, 'PENDING')")
                    connection.execute("INSERT INTO investigations (app_id, status) VALUES (4, 'PENDING')")

        html = "<script>hidden</script><body>1 star crash. 4 stars useful.</body>"
        evidence = collect_research(
            {"app_name": "Example", "url": "https://example.test"},
            fetch=lambda _url: html,
            search=lambda _query: "<a href='https://competitor.test'>Competitor</a> 2 stars too many ads.",
        )
        self.assertNotIn("hidden", str(evidence))
        self.assertEqual(evidence["reviews"][0]["rating"], 1)
        self.assertTrue(any(review["rating"] == 2 for review in evidence["reviews"]))
        self.assertTrue(evidence["competitors"])
        with self.assertRaises(ValueError):
            invalid = dict(VALID_RESULT)
            invalid["final_score"] = 11
            validate_assessment(invalid)
        with self.assertRaises(ValueError):
            invalid = dict(VALID_RESULT)
            invalid["final_score"] = 8
            validate_assessment(invalid)

    def test_missing_url_still_collects_bounded_search_evidence(self):
        calls = []

        def search(query):
            calls.append(query)
            return "<a href='https://example.test/result'>Result</a> 2 stars has ads."

        evidence = collect_research({"app_name": "Example"}, search=search)
        self.assertEqual(len(calls), 3)
        self.assertTrue(evidence["reviews"])
        self.assertTrue(evidence["competitors"])
        self.assertTrue(evidence["alternatives"])


if __name__ == "__main__":
    unittest.main()