- [ ] Phase 4 Product Definition implementation

## Project Setup

- [x] Create the phase-owned `Definition/` project structure.
- [x] Add `design_product.py` as the single-run entry point.
- [x] Add `run_continuous.py` for repeated one-product runs.
- [x] Add `handoff.py`, `database.py`, `analysis.py`, `ollama_client.py`,
	`config.py`, and `run_log.py` using the conventions from Phases 1-3.
- [x] Add `requirements.txt`, `README.md`, and `tests/test_phase4.py`.
- [x] Keep Phase 4 dependencies minimal and do not add a frontend or
	multi-agent system.

## Configuration and Logging

- [x] Add `PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS` to the shared
	environment configuration.
- [x] Load the Phase 4 database path with a default of
	`Definition/app_designer.db`.
- [x] Load the Phase 3 source database path with a default of
	`Validator/app_validator.db`.
- [x] Configure the Phase 4 Ollama model and endpoint using the existing
	environment conventions.
- [x] Create timestamped logs in `Definition/logs/`.
- [x] Tee progress logs to the terminal and the Phase 4 log file.
- [x] Log handoff, selection, research assembly, Ollama calls, validation,
	saving, retries, stale-record recovery, and queue completion.
- [x] Make the continuous runner use a monotonic deadline and handle Ctrl+C
	cleanly.
- [x] Retry an iteration after an error without terminating the entire
	continuous run.

## Phase 3 Handoff

- [x] Copy `Validator/app_validator.db` to `Definition/app_designer.db` on
	the first run.
- [x] Synchronize `opportunities`, `investigations`, and
	`business_validations` on later runs.
- [x] Preserve existing `product_designs` during every synchronization.
- [x] Never modify the Validator database.
- [x] Record `source_validation_id`, `source_validated_at`, and a bounded
	`source_validation_snapshot` on every product design.
- [x] Detect changes to the controlling Phase 3 validation.
- [x] Mark a design `STALE` when its source validation changes.
- [x] Prevent `STALE` designs from being handed to Phase 5 until redesigned.
- [x] Test first-run copying, later synchronization, preservation of designs,
	and stale-source detection.

## Database Schema and Lifecycle

- [x] Add only the Phase 4-owned `product_designs` table.
- [x] Add every field specified in the Phase 4 design document.
- [x] Enforce `app_id NOT NULL UNIQUE` with a foreign key to `opportunities`.
- [x] Enforce `source_validation_id` as a foreign key to
	`business_validations`.
- [x] Enforce statuses `PENDING`, `IN_PROGRESS`, `COMPLETE`, `FAILED`, and
	`STALE`.
- [x] Enforce `design_score` as an integer from 1 through 10.
- [x] Store feature collections, strategies, risks, evidence, and snapshots
	as validated JSON.
- [x] Create or recover one design record per app.
- [x] Recover abandoned `IN_PROGRESS` records as `FAILED`.
- [x] Retry `FAILED` and `STALE` records in place without creating duplicates.
- [x] Save the complete design atomically in one transaction.
- [x] Clear stale errors when a retry succeeds.
- [x] Preserve completed designs and do not automatically repeat them.

## Opportunity Selection

- [x] Select only `business_validations.status = COMPLETE` rows.
- [x] Select only recommendations `BUILD_CANDIDATE` and `PROMISING`.
- [x] Prioritize `BUILD_CANDIDATE` over `PROMISING`.
- [x] Order within each recommendation by descending `viability_score`.
- [x] Use ascending `app_id` as the deterministic tie-breaker.
- [x] Exclude `PASS` and `POSSIBLE` validations.
- [x] Select designs with no existing record or status `FAILED`/`STALE`.
- [x] Return the selected app, investigation, validation, and source metadata
	needed to build the bounded Ollama context.
- [x] Add tests for recommendation priority, score ordering, tie-breaking,
	completed designs, failed retries, and stale redesigns.

## Product Analysis

- [x] Read bounded Phase 2 complaints, competitor observations, and
	conclusions.
- [x] Read Phase 3 target customer, value proposition, business risks, key
	assumptions, viability score, and recommendation.
- [x] Do not repeat Phase 3 business validation.
- [ ] Use additional public research only for unresolved product-definition
	questions.
- [ ] Cap supplemental research and save only bounded source URL, title, and
	evidence summaries that change a product decision.
- [x] Identify one concise `core_problem`.
- [x] Select one narrow `target_user` based on problem and workflow fit.
- [x] Select one or more permitted `product_strategy` values.
- [x] Define meaningful `differentiation` grounded in research.
- [x] Record `design_rationale`, `rejected_alternatives`, and
	`inherited_constraints`.
- [x] Record evidence references with claim, source phase, source field, and
	evidence summary.

## Validation Target and Scope

- [x] Define a falsifiable `validation_hypothesis`.
- [x] Define one ordered `core_user_workflow` with at least two actions.
- [x] Define `minimum_validation_scope` with one to three capabilities.
- [x] Define `must_have_features` as concrete behaviors implementing the
	minimum validation scope.
- [x] Ensure every must-have feature maps to a workflow step.
- [x] Ensure must-have and excluded features do not overlap.
- [x] Define `nice_to_have_features` as intentionally deferred behavior.
- [x] Define `excluded_features` explicitly to prevent feature creep.
- [x] Define `mvp_scope` as a summary of the minimum validation scope without
	adding extra features.
- [x] Define observable `evidence_to_support_or_reject` for the hypothesis.
- [x] Define observable, testable `success_criteria`.

## Technical Feasibility

- [x] Record high-level `technical_considerations` without designing Phase 5
	architecture.
- [x] Record `technical_risks` with risk, severity, impact, mitigation, and
	`blocks_validation` fields.
- [x] Prevent `READY_FOR_POC` when an unresolved high-severity risk blocks the
	validation workflow.
- [x] Keep the temporary `product_name` optional and non-authoritative.

## Structured Ollama Analysis

- [x] Build one complete prompt containing the bounded Phase 2 and Phase 3
	context plus the product-definition inputs.
- [x] Require Ollama to return only valid JSON.
- [x] Validate the complete response before persistence.
- [x] Reject missing or empty required fields.
- [x] Validate strategy values and JSON collection types.
- [x] Validate workflow length and minimum-scope size.
- [x] Validate feature-to-workflow mapping semantically.
- [x] Validate feature-exclusion coherence.
- [x] Validate evidence and success criteria are observable beyond basic shape.
- [x] Validate technical-risk severity and blocking behavior.
- [x] Validate score/recommendation mapping:
	`1-3 PASS`, `4-5 DESIGN_REVIEW`, `6-10 READY_FOR_POC`.
- [x] Reject a recommendation that does not match its score.
- [x] Reject `READY_FOR_POC` when required handoff fields are missing or
	inconsistent.
- [x] Handle malformed JSON, timeouts, and Ollama errors as retryable failures.

## Phase 5 Handoff

- [x] Make `COMPLETE` and `READY_FOR_POC` the only Phase 5 eligibility
	combination.
- [x] Require current `source_validation_id` and `source_validated_at`.
- [x] Exclude `FAILED` and `STALE` designs from the Phase 5 queue.
- [x] Preserve authoritative fields for Phase 5:
	`core_problem`, `target_user`, `validation_hypothesis`,
	`core_user_workflow`, `minimum_validation_scope`, `must_have_features`,
	`excluded_features`, and `success_criteria`.
- [x] Test that an eligible design contains all authoritative fields and no
	blocking technical risk.

## Tests and Documentation

- [x] Test database creation and all schema constraints.
- [ ] Test handoff synchronization and source immutability.
- [x] Test lifecycle transitions, interruption recovery, retries, and stale
	redesigns.
- [x] Test structured-output validation and score/recommendation rules.
- [x] Test one successful product-design run with a mocked Ollama response.
- [ ] Test malformed, incomplete, contradictory, and blocked-risk outputs.
- [ ] Test continuous-run duration, empty queue behavior, retry behavior, and
	graceful interruption.
- [x] Document single-run and continuous-run commands in `Definition/README.md`.
- [x] Document database ownership and Phase 3/Phase 5 handoffs.
- [x] Document log locations, retry behavior, and failure recovery.
- [x] Run the Phase 4 test suite and `git diff --check`.
