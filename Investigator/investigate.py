"""Phase 2 investigation entry point and run lifecycle."""

from typing import Any, Callable, Dict, Optional

from database import (
    create_investigation,
    init_database,
    save_investigation_result,
    select_next_opportunity,
    update_investigation_status,
)
from ollama_client import OllamaClient
from research import collect_research


Researcher = Callable[[Dict[str, Any]], Dict[str, Any]]
Analyzer = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]

ASSESSMENT_SCHEMA = {
    "type": "object",
    "required": [
        "app_analysis", "user_analysis", "complaint_analysis",
        "competitor_analysis", "alternative_analysis", "build_difficulty",
        "proprietary_dependency", "market_potential", "competition_level",
        "final_score", "recommendation", "summary",
    ],
    "properties": {
        field: {"type": "string", "minLength": 1}
        for field in (
            "app_analysis", "user_analysis", "complaint_analysis",
            "competitor_analysis", "alternative_analysis", "summary",
        )
    },
    "additionalProperties": False,
}
for _score_field in (
    "build_difficulty", "proprietary_dependency", "market_potential",
    "competition_level", "final_score",
):
    ASSESSMENT_SCHEMA["properties"][_score_field] = {
        "type": "integer", "minimum": 1, "maximum": 10,
    }
ASSESSMENT_SCHEMA["properties"]["recommendation"] = {
    "type": "string",
    "enum": ["PASS", "INVESTIGATE_FURTHER", "PROMISING", "STRONG_OPPORTUNITY"],
}


def analyze_with_ollama(
    opportunity: Dict[str, Any],
    evidence: Dict[str, Any],
    client: Optional[OllamaClient] = None,
) -> Dict[str, Any]:
    """Ask Ollama for the structured assessment required by the database."""
    prompt = """You are evaluating whether building an alternative to an app is worthwhile.
Use only the supplied evidence. Be conservative when evidence is missing and do not invent facts.
Return JSON with exactly these fields:
app_analysis, user_analysis, complaint_analysis, competitor_analysis,
alternative_analysis, build_difficulty, proprietary_dependency, market_potential,
competition_level, final_score, recommendation, summary.
The five score fields must be integers from 1 to 10. Recommendation must be one of
PASS, INVESTIGATE_FURTHER, PROMISING, STRONG_OPPORTUNITY.
Interpret final_score bands as 1-3 PASS, 4-5 INVESTIGATE_FURTHER, 6-7 PROMISING, 8-10 STRONG_OPPORTUNITY.

Opportunity:
{}

Evidence:
{}""".format(opportunity, evidence)
    return (client or OllamaClient()).generate_json(prompt, schema=ASSESSMENT_SCHEMA)


def run_one_investigation(
    research: Researcher,
    analyze: Analyzer,
    database_path: Optional[str] = None,
) -> bool:
    """Run exactly one opportunity and return whether work was completed."""
    init_database(database_path)
    opportunity = select_next_opportunity(database_path)
    if opportunity is None:
        print("No uninvestigated opportunities available.")
        return False

    investigation_id = create_investigation(opportunity["app_id"], database_path)
    update_investigation_status(investigation_id, "IN_PROGRESS", database_path)
    print("Investigating {} (score {})".format(opportunity.get("app_name") or opportunity["app_id"], opportunity["score"]))
    try:
        evidence = research(opportunity)
        result = analyze(opportunity, evidence)
        save_investigation_result(investigation_id, result, database_path)
    except Exception as error:
        update_investigation_status(investigation_id, "FAILED", database_path, str(error))
        print("Investigation failed: {}".format(error))
        return False
    print("Investigation complete.")
    return True


def main() -> None:
    run_one_investigation(collect_research, analyze_with_ollama)


if __name__ == "__main__":
    main()