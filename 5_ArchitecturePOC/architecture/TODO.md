
# Phase 5 POC Architecture TODO

## Project Setup

- [ ] Create the phase-owned `5_ArchitecturePOC/` project structure.
- [ ] Add `architecture_poc.py` as the single-architecture entry point.
- [ ] Add `run_continuous.py` for repeated one-architecture runs.
- [ ] Add `handoff.py`, `database.py`, `analysis.py`, `ollama_client.py`,
	`config.py`, and `run_log.py` using the established phase patterns.
- [ ] Add `README.md`, `requirements.txt`, and `tests/test_phase5.py`.
- [ ] Keep the Phase 5 pipeline free of an agentic coding harness; that belongs
	to Phase 6.

## Phase 4 Handoff

- [ ] Copy `4_Definition/app_designer.db` into the private
	`5_ArchitecturePOC/app_poc_architecture.db` database on first run.
- [ ] Synchronize new and changed inherited rows without modifying Phase 4.
- [ ] Preserve existing `poc_architectures` records during synchronization.
- [ ] Reject `STALE`, `FAILED`, and structurally invalid Phase 4 designs.
- [ ] Store a bounded source design snapshot with every architecture.
- [ ] Mark completed architectures `STALE` when their source design changes.
- [ ] Test source immutability, synchronization, and stale-source recovery.

## Database and Lifecycle

- [ ] Add only the Phase 5-owned `poc_architectures` table.
- [ ] Enforce unique `app_id` and unique `product_design_id` references.
- [ ] Enforce `PENDING`, `IN_PROGRESS`, `COMPLETE`, `FAILED`, and `STALE` states.
- [ ] Recover abandoned `IN_PROGRESS` records as `FAILED`.
- [ ] Retry `FAILED` and `STALE` records in place.
- [ ] Save the complete architecture atomically in one transaction.
- [ ] Preserve completed architectures when the source design is unchanged.

## Opportunity Selection

- [ ] Select only current Phase 4 designs with `COMPLETE` and `READY_FOR_POC`.
- [ ] Prioritize Phase 3 `viability_score`, then Phase 4 `design_score`, then
	ascending `app_id`.
- [ ] Exclude `PASS`, `DESIGN_REVIEW`, `FAILED`, and `STALE` source designs.
- [ ] Process exactly one architecture per run.
- [ ] Test priority, tie-breaking, completed records, retries, and stale rows.

## Architecture Validation

- [ ] Validate every required text field and JSON collection.
- [ ] Validate the documented platform enum and exact runtime entrypoint.
- [ ] Validate component, data-model, acceptance-step, risk, and deviation
	object shapes.
- [ ] Map every minimum-validation capability to workflow and acceptance steps.
- [ ] Prevent excluded features from entering the architecture scope.
- [ ] Enforce score/recommendation bands.
- [ ] Reject blocking technical risks and hypothesis-breaking deviations.
- [ ] Reject unexpected output fields and malformed Ollama responses.

## Phase 6 Handoff

- [ ] Make only `COMPLETE` and `READY_TO_BUILD` architectures eligible.
- [ ] Preserve the source Phase 4 snapshot and the complete architecture
	snapshot for reproducible builds.
- [ ] Include the build plan, test plan, acceptance steps, limitations, risks,
	and deviations in the Phase 6 handoff.
- [ ] Test that Phase 6 receives authoritative fields without rereading mutable
	upstream state.

## Tests and Documentation

- [ ] Test one successful architecture run with a mocked Ollama response.
- [ ] Test incomplete, contradictory, malformed, and blocked-risk outputs.
- [ ] Test continuous-run duration, empty queue, retry, and interruption.
- [ ] Document setup, database ownership, handoff rules, logs, and recovery.
- [ ] Run the Phase 5 suite and `git diff --check`.
