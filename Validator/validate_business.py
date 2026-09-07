"""Phase 3 business validation entry point."""

from typing import Any, Callable, Dict, Optional

try:
    from .analysis import build_assessment_prompt, validate_assessment
    from .business_research import collect_business_research
    from .database import (
        create_validation,
        init_database,
        recover_interrupted_validations,
        save_validation_result,
        select_next_opportunity,
        update_validation_status,
    )
    from .ollama_client import OllamaClient
except ImportError:
    from analysis import build_assessment_prompt, validate_assessment
    from business_research import collect_business_research
    from database import (
        create_validation,
        init_database,
        recover_interrupted_validations,
        save_validation_result,
        select_next_opportunity,
        update_validation_status,
    )
    from ollama_client import OllamaClient


Researcher = Callable[[Dict[str, Any]], Dict[str, Any]]
Analyzer = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


def analyze_with_ollama(
    opportunity: Dict[str, Any],
    research: Dict[str, Any],
    client: Optional[OllamaClient] = None,
) -> Dict[str, Any]:
    """Ask Ollama for the final skeptical business assessment."""
    return (client or OllamaClient()).generate_json(
        build_assessment_prompt(opportunity, research)
    )


def run_one_validation(
    research: Researcher = collect_business_research,
    analyze: Analyzer = analyze_with_ollama,
    database_path: Optional[str] = None,
) -> bool:
    """Run exactly one eligible opportunity through business validation."""
    init_database(database_path)
    recover_interrupted_validations(database_path)
    opportunity = select_next_opportunity(database_path)
    if opportunity is None:
        print("No eligible business opportunities available.")
        return False
    validation_id = create_validation(opportunity["app_id"], database_path)
    update_validation_status(validation_id, "IN_PROGRESS", database_path)
    print(
        "Validating {} (Phase 2 score {})".format(
            opportunity.get("app_name") or opportunity["app_id"],
            opportunity.get("final_score"),
        )
    )
    try:
        evidence = research(opportunity)
        result = analyze(opportunity, evidence)
        validate_assessment(result)
        save_validation_result(validation_id, result, database_path)
    except Exception as error:
        update_validation_status(validation_id, "FAILED", database_path, str(error))
        print("Business validation failed: {}".format(error))
        return False
    print("Business validation complete.")
    return True


if __name__ == "__main__":
    run_one_validation()
