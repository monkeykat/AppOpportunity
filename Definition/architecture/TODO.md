( ) Phase 4 Product Definition implementation

## Project Setup

- [ ] Create the phase-owned `Definition/` project structure.
- [ ] Add `design_product.py` as the single-run entry point.
- [ ] Add `run_continuous.py` for repeated one-product runs.
- [ ] Add `handoff.py`, `database.py`, `analysis.py`, `ollama_client.py`,
	`config.py`, and `run_log.py` using the conventions from Phases 1-3.
- [ ] Add `requirements.txt`, `README.md`, and `tests/test_phase4.py`.
- [ ] Keep Phase 4 dependencies minimal and do not add a frontend or
	multi-agent system.

## Configuration and Logging

- [ ] Add `PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS` to the shared
	environment configuration.
- [ ] Load the Phase 4 database path with a default of
	`Definition/app_designer.db`.
- [ ] Load the Phase 3 source database path with a default of
	`Validator/app_validator.db`.
- [ ] Configure the Phase 4 Ollama model and endpoint using the existing
	environment conventions.
- [ ] Create timestamped logs in `Definition/logs/`.
- [ ] Tee progress logs to the terminal and the Phase 4 log file.
- [ ] Log handoff, selection, research assembly, Ollama calls, validation,
	saving, retries, stale-record recovery, and queue completion.
- [ ] Make the continuous runner use a monotonic deadline and handle Ctrl+C
	cleanly.
- [ ] Retry an iteration after an error without terminating the entire
	continuous run.

## Phase 3 Handoff

- [ ] Copy `Validator/app_validator.db` to `Definition/app_designer.db` on
	the first run.
- [ ] Synchronize `opportunities`, `investigations`, and
	`business_validations` on later runs.
- [ ] Preserve existing `product_designs` during every synchronization.
- [ ] Never modify the Validator database.
- [ ] Record `source_validation_id`, `source_validated_at`, and a bounded
	`source_validation_snapshot` on every product design.
- [ ] Detect changes to the controlling Phase 3 validation.
- [ ] Mark a design `STALE` when its source validation changes.
- [ ] Prevent `STALE` designs from being handed to Phase 5 until redesigned.
- [ ] Test first-run copying, later synchronization, preservation of designs,
	and stale-source detection.

## Database Schema and Lifecycle

- [ ] Add only the Phase 4-owned `product_designs` table.
- [ ] Add every field specified in the Phase 4 design document.
- [ ] Enforce `app_id NOT NULL UNIQUE` with a foreign key to `opportunities`.
- [ ] Enforce `source_validation_id` as a foreign key to
	`business_validations`.
- [ ] Enforce statuses `PENDING`, `IN_PROGRESS`, `COMPLETE`, `FAILED`, and
	`STALE`.
- [ ] Enforce `design_score` as an integer from 1 through 10.
- [ ] Store feature collections, strategies, risks, evidence, and snapshots
	as validated JSON.
- [ ] Create or recover one design record per app.
- [ ] Recover abandoned `IN_PROGRESS` records as `FAILED`.
- [ ] Retry `FAILED` and `STALE` records in place without creating duplicates.
- [ ] Save the complete design atomically in one transaction.
- [ ] Clear stale errors when a retry succeeds.
- [ ] Preserve completed designs and do not automatically repeat them.

## Opportunity Selection

- [ ] Select only `business_validations.status = COMPLETE` rows.
- [ ] Select only recommendations `BUILD_CANDIDATE` and `PROMISING`.
- [ ] Prioritize `BUILD_CANDIDATE` over `PROMISING`.
- [ ] Order within each recommendation by descending `viability_score`.
- [ ] Use ascending `app_id` as the deterministic tie-breaker.
- [ ] Exclude `PASS` and `POSSIBLE` validations.
- [ ] Select designs with no existing record or status `FAILED`/`STALE`.
- [ ] Return the selected app, investigation, validation, and source metadata
	needed to build the bounded Ollama context.
- [ ] Add tests for recommendation priority, score ordering, tie-breaking,
	completed designs, failed retries, and stale redesigns.

## Product Analysis

- [ ] Read bounded Phase 2 complaints, competitor observations, and
	conclusions.
- [ ] Read Phase 3 target customer, value proposition, business risks, key
	assumptions, viability score, and recommendation.
- [ ] Do not repeat Phase 3 business validation.
- [ ] Use additional public research only for unresolved product-definition
	questions.
- [ ] Cap supplemental research and save only bounded source URL, title, and
	evidence summaries that change a product decision.
- [ ] Identify one concise `core_problem`.
- [ ] Select one narrow `target_user` based on problem and workflow fit.
- [ ] Select one or more permitted `product_strategy` values.
- [ ] Define meaningful `differentiation` grounded in research.
- [ ] Record `design_rationale`, `rejected_alternatives`, and
	`inherited_constraints`.
- [ ] Record evidence references with claim, source phase, source field, and
	evidence summary.

## Validation Target and Scope

- [ ] Define a falsifiable `validation_hypothesis`.
- [ ] Define one ordered `core_user_workflow` with at least two actions.
- [ ] Define `minimum_validation_scope` with one to three capabilities.
- [ ] Define `must_have_features` as concrete behaviors implementing the
	minimum validation scope.
- [ ] Ensure every must-have feature maps to a workflow step.
- [ ] Ensure must-have and excluded features do not overlap.
- [ ] Define `nice_to_have_features` as intentionally deferred behavior.
- [ ] Define `excluded_features` explicitly to prevent feature creep.
- [ ] Define `mvp_scope` as a summary of the minimum validation scope without
	adding extra features.
- [ ] Define observable `evidence_to_support_or_reject` for the hypothesis.
- [ ] Define observable, testable `success_criteria`.

## Technical Feasibility

- [ ] Record high-level `technical_considerations` without designing Phase 5
	architecture.
- [ ] Record `technical_risks` with risk, severity, impact, mitigation, and
	`blocks_validation` fields.
- [ ] Prevent `READY_FOR_POC` when an unresolved high-severity risk blocks the
	validation workflow.
- [ ] Keep the temporary `product_name` optional and non-authoritative.

## Structured Ollama Analysis

- [ ] Build one complete prompt containing the bounded Phase 2 and Phase 3
	context plus the product-definition inputs.
- [ ] Require Ollama to return only valid JSON.
- [ ] Validate the complete response before persistence.
- [ ] Reject missing or empty required fields.
- [ ] Validate strategy values and JSON collection types.
- [ ] Validate workflow length and minimum-scope size.
- [ ] Validate feature-to-workflow and feature-exclusion coherence.
- [ ] Validate evidence and success criteria are observable.
- [ ] Validate technical-risk severity and blocking behavior.
- [ ] Validate score/recommendation mapping:
	`1-3 PASS`, `4-5 DESIGN_REVIEW`, `6-10 READY_FOR_POC`.
- [ ] Reject a recommendation that does not match its score.
- [ ] Reject `READY_FOR_POC` when required handoff fields are missing or
	inconsistent.
- [ ] Handle malformed JSON, timeouts, and Ollama errors as retryable failures.

## Phase 5 Handoff

- [ ] Make `COMPLETE` and `READY_FOR_POC` the only Phase 5 eligibility
	combination.
- [ ] Require current `source_validation_id` and `source_validated_at`.
- [ ] Exclude `FAILED` and `STALE` designs from the Phase 5 queue.
- [ ] Preserve authoritative fields for Phase 5:
	`core_problem`, `target_user`, `validation_hypothesis`,
	`core_user_workflow`, `minimum_validation_scope`, `must_have_features`,
	`excluded_features`, and `success_criteria`.
- [ ] Test that an eligible design contains all authoritative fields and no
	blocking technical risk.

## Tests and Documentation

- [ ] Test database creation and all schema constraints.
- [ ] Test handoff synchronization and source immutability.
- [ ] Test lifecycle transitions, interruption recovery, retries, and stale
	redesigns.
- [ ] Test structured-output validation and score/recommendation rules.
- [ ] Test one successful product-design run with a mocked Ollama response.
- [ ] Test malformed, incomplete, contradictory, and blocked-risk outputs.
- [ ] Test continuous-run duration, empty queue behavior, retry behavior, and
	graceful interruption.
- [ ] Document single-run and continuous-run commands in `Definition/README.md`.
- [ ] Document database ownership and Phase 3/Phase 5 handoffs.
- [ ] Document log locations, retry behavior, and failure recovery.
- [ ] Run the Phase 4 test suite and `git diff --check`.
