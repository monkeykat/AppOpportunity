import sqlite3
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis import validate_assessment
from boundary_check import assert_unchanged, snapshot_files
from database import get_connection, select_next_opportunity
from handoff import import_opportunities
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
        ):
            self.assertIn(field, client.prompt)

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
                return {"sources": [], "errors": []}

            def analyze(_opportunity, _evidence):
                return dict(VALID_RESULT)

            self.assertTrue(run_one_investigation(research, analyze, database_path))
            with get_connection(database_path) as connection:
                row = connection.execute(
                    "SELECT status, final_score, investigated_at FROM investigations WHERE app_id = 2"
                ).fetchone()
                self.assertEqual(tuple(row), ("COMPLETE", 6, row[2]))
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


if __name__ == "__main__":
    unittest.main()