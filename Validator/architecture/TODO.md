# Phase 3 TODO

Phase 3 is an independent business validator. Work only in `Validator` and use
the Phase 2 database as a private copy. Do not modify Phase 1, Phase 2, or
their databases.

## Setup and Boundaries

- [x] Confirm the Phase 1 and Phase 2 project trees and databases are preserved.
- [x] Create the Phase 3 project structure and entry point `validate_business.py`.
- [x] Copy the completed Phase 2 project inputs into the Phase 3 workspace.
- [x] Copy the completed Phase 2 `app_scout.db` into the Phase 3 workspace.
- [x] Configure Phase 3 to open only its own database copy.
- [x] Verify Phase 3 does not import Phase 1 or Phase 2 Python modules at runtime.
- [x] Keep dependencies limited to Python, SQLite, Ollama, Playwright, and required standard-library support.
- [x] Do not add a frontend, complex agents, orchestration framework, API service, scheduler, vector database, RAG system, or financial-modeling pipeline.

## Database and Schema

- [x] Add only the Phase 3 `business_validations` table to the copied database.
- [x] Preserve all existing Phase 2 tables and columns unchanged.
- [x] Add the `business_validations.id` primary key.
- [x] Add the unique `app_id` relationship so one app has one validation.
- [x] Add statuses `PENDING`, `IN_PROGRESS`, `COMPLETE`, and `FAILED`.
- [x] Add text fields `product_concept`, `target_customer`, `value_proposition`, `differentiation`, `monetization`, `willingness_to_pay`, `apparent_market_size`, `customer_acquisition_difficulty`, `revenue_potential`, `business_risks`, `key_assumptions`, and `summary`.
- [x] Add `viability_score`, `recommendation`, and `validated_at`.
- [x] Restrict recommendations to `PASS`, `POSSIBLE`, `PROMISING`, and `BUILD_CANDIDATE`.
- [x] Make schema initialization safe to run repeatedly.

## Opportunity Selection

- [x] Select only Phase 2 investigations with status `COMPLETE`.
- [x] Select only Phase 2 recommendations `STRONG_OPPORTUNITY` or `PROMISING`.
- [x] Prioritize `STRONG_OPPORTUNITY` over `PROMISING`.
- [x] Within each recommendation group, select the highest Phase 2 `final_score`.
- [x] Exclude apps that already have a `business_validations` record.
- [x] Process exactly one opportunity per run.
- [x] Exit cleanly when no eligible opportunity remains.

## Phase 2 Results and Evidence

- [x] Read the selected app information from the copied Phase 2 database.
- [x] Read the Phase 2 app, user, complaint, competitor, and alternative analyses.
- [x] Read Phase 2 difficulty, proprietary dependency, market, competition, final score, and recommendation fields.
- [x] Use Phase 2 raw evidence when available without unnecessarily repeating Phase 2 research.
- [x] Preserve the distinction between evidence, interpretation, and business judgment.

## Business Research and Analysis

- [x] Define the smallest useful MVP and the problem it tests.
- [x] Identify the necessary MVP features and explicitly exclude feature expansion.
- [x] Define the target customer and their problem frequency, importance, and search behavior.
- [x] Identify the product value proposition.
- [x] Identify meaningful differentiation from existing products and workarounds.
- [x] Explain why a new user would choose the product.
- [x] Explain why an existing user might switch.
- [x] Research monetization options, including paid apps, subscriptions, freemium, advertising, premium features, licenses, affiliates, and sponsorships where relevant.
- [x] Look for evidence of willingness to pay, including paid competitors, subscriptions, purchases, premium features, and businesses paying for similar tools.
- [x] Evaluate whether advertising could support the product based on audience size, usage, acquisition, and comparable products.
- [x] Estimate apparent market size using evidence without creating a precise TAM model.
- [x] Estimate customer acquisition difficulty using search, communities, app discovery, SEO, influencers, partnerships, and advertising.
- [x] Estimate rough revenue potential without creating a financial forecast or multi-year model.
- [x] Identify the biggest business risks.
- [x] Identify the assumptions that must be true for the business to work.
- [x] Ask why users might stay with existing products, refuse to switch, refuse to pay, or be too difficult to reach.
- [x] Ask why advertising might fail and why the market might be too small.

## Ollama Evaluation and Scoring

- [x] Implement a Phase 3-owned Ollama client with JSON parsing and reasonable invalid-response handling.
- [x] Send the Phase 2 results and Phase 3 analysis to Ollama for final business evaluation.
- [x] Require cautious, evidence-based language and explicitly discourage automatic optimism.
- [x] Require the final assessment to include `viability_score`, `recommendation`, and `summary`.
- [x] Validate `viability_score` as an integer from 1 through 10.
- [x] Enforce score bands: 1-3 `PASS`, 4-5 `POSSIBLE`, 6-7 `PROMISING`, and 8-10 `BUILD_CANDIDATE`.
- [x] Keep `BUILD_CANDIDATE` rare and require evidence of demand, active solution-seeking, differentiation, monetization, sufficient market size, and reachable customers.
- [x] Require the final summary to include the opportunity, major risks, and important assumptions.

## Run Lifecycle

- [x] Create a validation record before business research begins.
- [x] Mark the record `IN_PROGRESS` before processing the selected opportunity.
- [x] Save results only after research, evaluation, scoring, and recommendation succeed.
- [x] Mark successful validations `COMPLETE` and save `validated_at`.
- [x] Mark unexpected failures `FAILED` and preserve diagnostic context.
- [x] Recover or retry interrupted validations with a simple policy; do not build checkpoint-level recovery.
- [x] Never automatically repeat a completed validation.

## Testing and Verification

- [x] Test copied-database initialization without changing the source Phase 2 database.
- [x] Test selection priority for `STRONG_OPPORTUNITY` and `PROMISING` records.
- [x] Test that `PASS` and `INVESTIGATE_FURTHER` records are excluded.
- [x] Test that completed business validations are skipped.
- [x] Test the unique one-validation-per-app constraint.
- [x] Test status transitions for success, no eligible work, failure, and interrupted recovery.
- [x] Test Phase 2 result and raw-evidence retrieval.
- [x] Test mocked business research and final evaluation without network calls.
- [x] Test Ollama JSON parsing and invalid score/recommendation rejection.
- [x] Test score-band and recommendation consistency.
- [x] Run one controlled end-to-end validation when dependencies are available.
- [x] Snapshot Phase 1 and Phase 2 trees and databases before and after Phase 3 operations and confirm they are unchanged.
- [x] Run `python validate_business.py` and confirm it processes at most one app.

## Documentation and Completion

- [x] Document setup, database-copy requirements, Ollama configuration, dependencies, and run instructions.
- [x] Document the Phase 1 -> Phase 2 -> Phase 3 database flow.
- [x] Document recommendation bands and the meaning of `BUILD_CANDIDATE`.
- [x] Record implementation decisions that differ from the design.
- [x] Confirm every Phase 3 Definition of Done item is satisfied.

## Implementation Notes

- Phase 3 uses bounded search-result pages for business-topic research rather
	than adding a second full web crawler. This keeps the MVP small while still
	collecting provenance for monetization, willingness to pay, advertising,
	market, and acquisition questions.
- Business research accepts an injected search function so tests remain offline
	and deterministic; the normal entry point uses the standard-library searcher.
- The copied Phase 2 database currently has no eligible completed opportunity,
	so the real entry point exits cleanly until one is available.
- Final boundary verification hashed both `Scout` and `Investigator` before and
	after Validator tests and execution; both were unchanged. Existing Git
	changes under `Investigator` predated this verification and were not touched.
