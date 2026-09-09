"""Phase 3 business validation entry point."""

from typing import Any, Callable, Dict, Optional

try:
    from .analysis import ASSESSMENT_SCHEMA, build_assessment_prompt, validate_assessment
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
    from .handoff import sync_from_investigator
    from .run_log import run_log
except ImportError:
    from analysis import ASSESSMENT_SCHEMA, build_assessment_prompt, validate_assessment
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
    from handoff import sync_from_investigator
    from run_log import run_log


Researcher = Callable[[Dict[str, Any]], Dict[str, Any]]
Analyzer = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


def analyze_with_ollama(
    opportunity: Dict[str, Any],
    research: Dict[str, Any],
    client: Optional[OllamaClient] = None,
) -> Dict[str, Any]:
    """Ask Ollama for the final skeptical business assessment."""
    return (client or OllamaClient()).generate_json(
        build_assessment_prompt(opportunity, research),
        schema=ASSESSMENT_SCHEMA,
    )


def run_one_validation(
    research: Researcher = collect_business_research,
    analyze: Analyzer = analyze_with_ollama,
    database_path: Optional[str] = None,
) -> bool:
    """Run exactly one eligible opportunity through business validation."""
    print("Preparing Validator database...")
    init_database(database_path)
    recovered = recover_interrupted_validations(database_path)
    if recovered:
        print("Recovered {} interrupted validation(s) for retry.".format(recovered))
    print("Selecting the highest-priority eligible opportunity...")
    opportunity = select_next_opportunity(database_path)
    if opportunity is None:
        print("No eligible business opportunities available.")
        return False
    validation_id = opportunity.get("validation_id")
    if validation_id is None:
        validation_id = create_validation(opportunity["app_id"], database_path)
        print("Created business validation {}.".format(validation_id))
    else:
        print("Retrying failed business validation {}.".format(validation_id))
    update_validation_status(validation_id, "IN_PROGRESS", database_path)
    print(
        "Validating {} (Phase 2 score {})".format(
            opportunity.get("app_name") or opportunity["app_id"],
            opportunity.get("final_score"),
        )
    )
    try:
        print("Collecting business research...")
        evidence = research(opportunity)
        additional_research = evidence.get("additional_research", {})
        topics = additional_research.get("topics", {})
        print(
            "Business research collected: {} topic(s), {} page(s), {} error(s).".format(
                len(topics),
                additional_research.get("pages_opened", 0),
                len(additional_research.get("errors", [])),
            )
        )
        print("Sending business evidence to Ollama for analysis...")
        result = analyze(opportunity, evidence)
        print("Ollama business analysis received; validating assessment...")
        print("Ollama returned fields: {}".format(", ".join(sorted(result))))
        validate_assessment(result)
        print("Saving validated business result...")
        save_validation_result(validation_id, result, database_path)
        print("Business validation result saved.")
    except Exception as error:
        update_validation_status(validation_id, "FAILED", database_path, str(error))
        print("Business validation failed: {}".format(error))
        return False
    print("Business validation complete.")
    return True


def run_validator_iteration(database_path: Optional[str] = None) -> bool:
    """Sync Investigator and process one eligible business validation."""
    print("Syncing completed Investigator data...")
    synced = sync_from_investigator(database_path=database_path)
    print("Synchronized {} Phase 2 row change(s).".format(synced))
    return run_one_validation(database_path=database_path)


def main() -> None:
    with run_log("single business validation"):
        run_validator_iteration()


if __name__ == "__main__":
    main()
