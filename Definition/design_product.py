"""Phase 4 single-product definition runner."""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

try:
    from .analysis import DESIGN_SCHEMA, build_design_prompt, validate_design
    from .database import (
        create_design,
        init_database,
        recover_invalid_completed_designs,
        recover_interrupted_designs,
        save_design_result,
        select_next_opportunity,
        update_design_status,
    )
    from .handoff import sync_from_validator
    from .ollama_client import OllamaClient
    from .run_log import run_log
except ImportError:
    from analysis import DESIGN_SCHEMA, build_design_prompt, validate_design
    from database import (
        create_design,
        init_database,
        recover_invalid_completed_designs,
        recover_interrupted_designs,
        save_design_result,
        select_next_opportunity,
        update_design_status,
    )
    from handoff import sync_from_validator
    from ollama_client import OllamaClient
    from run_log import run_log


Analyzer = Callable[[Dict[str, Any]], Dict[str, Any]]


def _source_snapshot(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": opportunity.get("source_validation_id"),
        "app_id": opportunity.get("app_id"),
        "status": opportunity.get("source_validation_status"),
        "viability_score": opportunity.get("viability_score"),
        "recommendation": opportunity.get("phase3_recommendation"),
        "summary": opportunity.get("source_validation_summary"),
        "validated_at": opportunity.get("source_validated_at"),
    }


def analyze_with_ollama(
    opportunity: Dict[str, Any], client: Optional[OllamaClient] = None
) -> Dict[str, Any]:
    return (client or OllamaClient()).generate_json(
        build_design_prompt(opportunity), schema=DESIGN_SCHEMA
    )


def run_one_design(
    analyze: Optional[Analyzer] = None,
    database_path: Optional[Path] = None,
) -> bool:
    print("Preparing Definition database...")
    init_database(database_path)
    recovered = recover_interrupted_designs(database_path)
    if recovered:
        print(f"Recovered {recovered} interrupted product design(s) for retry.")
    invalid = recover_invalid_completed_designs(database_path)
    if invalid:
        print(f"Marked {invalid} invalid completed product design(s) stale for redesign.")
    print("Selecting the highest-priority eligible business opportunity...")
    opportunity = select_next_opportunity(database_path)
    if opportunity is None:
        print("No eligible Phase 3 opportunities remain.")
        return False

    snapshot = _source_snapshot(opportunity)
    design_id = opportunity.get("design_id")
    if design_id is None:
        design_id = create_design(
            opportunity["app_id"],
            opportunity["source_validation_id"],
            opportunity.get("source_validated_at"),
            snapshot,
            database_path,
        )
        print(f"Created product design {design_id}.")
    else:
        print(f"Retrying product design {design_id} ({opportunity.get('design_status')}).")
    update_design_status(design_id, "IN_PROGRESS", database_path)
    print(
        "Defining {} from Phase 3 viability score {}...".format(
            opportunity.get("app_name") or opportunity["app_id"],
            opportunity.get("viability_score"),
        )
    )
    try:
        print("Sending bounded Phase 2 and Phase 3 evidence to Ollama...")
        result = analyze(opportunity) if analyze else analyze_with_ollama(opportunity)
        print("Ollama product definition received; validating output...")
        print("Ollama returned fields: {}".format(", ".join(sorted(result))))
        validate_design(result)
        print("Saving validated product definition...")
        save_design_result(
            design_id,
            result,
            opportunity["source_validation_id"],
            opportunity.get("source_validated_at"),
            snapshot,
            database_path,
        )
        print("Product definition saved and marked COMPLETE.")
    except Exception as error:
        update_design_status(design_id, "FAILED", database_path, str(error))
        print(f"Product definition failed: {error}")
        return False
    print("Product definition complete and eligible for Phase 5 when READY_FOR_POC.")
    return True


def run_definition_iteration(database_path: Optional[Path] = None, analyze: Optional[Analyzer] = None) -> bool:
    print("Syncing completed Validator data...")
    synced = sync_from_validator(database_path=database_path)
    print(f"Synchronized {synced} inherited row change(s).")
    return run_one_design(analyze=analyze, database_path=database_path)


def main() -> None:
    with run_log("single product definition"):
        run_definition_iteration()


if __name__ == "__main__":
    main()
