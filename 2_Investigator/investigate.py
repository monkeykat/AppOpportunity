"""Phase 2 investigation entry point and run lifecycle."""

from typing import Any, Callable, Dict, Optional

from config import WORKSPACE_DIR, get_database_path
from database import (
    create_investigation,
    init_database,
    recover_interrupted_investigations,
    save_investigation_result,
    select_next_opportunity,
    update_investigation_status,
)
from ollama_client import OllamaClient
from research import collect_research
from handoff import sync_from_scout
from run_log import run_log


Researcher = Callable[[Dict[str, Any]], Dict[str, Any]]
Analyzer = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]

ASSESSMENT_SCHEMA = {
    "type": "object",
    "required": [
        "app_analysis", "user_analysis", "complaint_analysis",
        "competitor_analysis", "alternative_analysis", "build_difficulty",
        "proprietary_dependency", "market_potential", "competition_level",
        "final_score", "recommendation", "summary", "strongest_argument_against",
    ],
    "properties": {
        field: {"type": "string", "minLength": 1}
        for field in (
            "app_analysis", "user_analysis", "complaint_analysis",
            "competitor_analysis", "alternative_analysis", "summary",
            "strongest_argument_against",
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
Keep observed evidence separate from interpretation: describe concrete signals first,
then explain what those signals may indicate. In complaint_analysis, distinguish
repeated patterns from isolated complaints and mention which issues appear solvable.
Actively search for reasons not to pursue the opportunity. Strong opportunities should be rare.
Scores of 8 or higher require strong evidence of demand, repeated solvable problems,
an achievable product, and no overwhelming proprietary or competitive barrier.
Do not return bare scores. Explain every score in the related narrative field:
explain build_difficulty and proprietary_dependency in app_analysis, market_potential in user_analysis,
competition_level in competitor_analysis, and final_score in summary.
Use the available evidence to justify each score and state uncertainty when evidence is limited.
Return JSON with exactly these fields:
app_analysis, user_analysis, complaint_analysis, competitor_analysis,
alternative_analysis, build_difficulty, proprietary_dependency, market_potential,
competition_level, final_score, recommendation, summary, strongest_argument_against.
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
    print("Preparing Investigator database...")
    init_database(database_path)
    recovered = recover_interrupted_investigations(database_path)
    if recovered:
        print("Recovered {} interrupted investigation(s) for retry.".format(recovered))
    print("Selecting the highest-scoring available opportunity...")
    opportunity = select_next_opportunity(database_path)
    if opportunity is None:
        print("No uninvestigated opportunities available.")
        return False

    investigation_id = opportunity.get("investigation_id")
    if investigation_id is None:
        investigation_id = create_investigation(opportunity["app_id"], database_path)
        print("Created investigation {}.".format(investigation_id))
    else:
        print("Retrying failed investigation {}.".format(investigation_id))
    update_investigation_status(investigation_id, "IN_PROGRESS", database_path)
    print("Investigating {} (score {})".format(opportunity.get("app_name") or opportunity["app_id"], opportunity["score"]))
    try:
        print("Collecting public research...")
        evidence = research(opportunity)
        print(
            "Research collected: {} source(s), {} review(s), {} competitor(s), "
            "{} alternative(s), {} error(s).".format(
                len(evidence.get("sources", [])),
                len(evidence.get("reviews", [])),
                len(evidence.get("competitors", [])),
                len(evidence.get("alternatives", [])),
                len(evidence.get("errors", [])),
            )
        )
        print("Sending research to Ollama for analysis...")
        result = analyze(opportunity, evidence)
        print("Ollama analysis received; validating assessment...")
        strongest_argument = result.pop("strongest_argument_against", "")
        if strongest_argument:
            result["summary"] = "{} Strongest argument against: {}".format(
                result["summary"].rstrip(), strongest_argument.strip()
            )
        result["raw_reviews"] = evidence.get("reviews", [])
        result["raw_competitors"] = evidence.get("competitors", [])
        result["raw_alternatives"] = evidence.get("alternatives", [])
        print("Saving validated investigation result...")
        save_investigation_result(investigation_id, result, database_path)
        print("Investigation result saved.")
    except Exception as error:
        update_investigation_status(investigation_id, "FAILED", database_path, str(error))
        print("Investigation failed: {}".format(error))
        return False
    print("Investigation complete.")
    return True


def main() -> None:
    with run_log("single investigation"):
        run_investigator_iteration()


def run_investigator_iteration(database_path=None) -> bool:
    """Sync Scout and process one Investigator opportunity."""
    phase_2_database = database_path or get_database_path()
    scout_database = WORKSPACE_DIR / "1_Scout" / "src" / "app_scout.db"
    print("Syncing new opportunities from Scout...")
    imported = sync_from_scout(scout_database, phase_2_database)
    print("Synchronized {} Scout opportunity row change(s).".format(imported))
    return run_one_investigation(collect_research, analyze_with_ollama, phase_2_database)


if __name__ == "__main__":
    main()