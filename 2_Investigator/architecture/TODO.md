# Phase 2 MVP: App Opportunity Investigator

Architecture source: `phase_2_app_investigator_design.rtf`

## Scope and Constraints

- [x] Keep all Phase 2 work in the `2_Investigator` folder.
- [x] Preserve every file and database in `1_Scout` exactly as-is.
- [x] Do not import Phase 1 Python modules at runtime.
- [x] Do not read from, write to, migrate, or extend the Phase 1 database.
- [x] Recreate any required support modules inside `2_Investigator`.
- [x] Use a separate Phase 2 SQLite database, `app_investigator.db`.
- [x] Define an explicit, one-way handoff for copying Phase 1 opportunity data into the Phase 2 database.
- [x] Keep the MVP dependency set minimal: Python, SQLite, Ollama, and Playwright.
- [x] Do not build a frontend.
- [x] Do not build a complex multi-agent system.
- [x] Process exactly one opportunity per run.
- [x] Add optional continuous mode that repeats one-opportunity iterations until a configured duration expires.
- [x] Ensure an app can have only one investigation.

## Project Setup

- [x] Define the Phase 2-owned project root and database path.
- [x] Define the Investigator entry point: `python investigate.py`.
- [x] Recreate Phase 2-owned configuration for research, Playwright, Ollama, and database paths.
- [x] Recreate Phase 2-owned database, Google Play, and Ollama client modules as needed; do not import their Phase 1 counterparts.
- [x] Define and implement the Phase 1-to-Phase 2 opportunity data handoff without changing `1_Scout`.
- [x] Add or update the Investigator README with setup, dependencies, Ollama requirements, and run instructions.
- [x] Add focused tests or smoke checks for database creation, selection, research parsing, and result persistence.

## Database

- [x] Create `app_investigator.db` owned exclusively by Phase 2.
- [x] Recreate the minimum Phase 1-compatible `opportunities` schema needed for Phase 2 selection.
- [x] Populate the Phase 2 `opportunities` table through the explicit Phase 1 data handoff.
- [x] Add the Phase 2 `investigations` table without changing any Phase 1 database.
- [x] Add a primary key `id`.
- [x] Add a unique `app_id` relationship to the Phase 2 `opportunities` table.
- [x] Add `status` with the values `PENDING`, `IN_PROGRESS`, `COMPLETE`, and `FAILED`.
- [x] Add text fields: `app_analysis`, `user_analysis`, `complaint_analysis`, `competitor_analysis`, and `alternative_analysis`.
- [x] Add scoring fields: `build_difficulty`, `proprietary_dependency`, `market_potential`, `competition_level`, and `final_score`.
- [x] Add `recommendation` with the values `PASS`, `INVESTIGATE_FURTHER`, `PROMISING`, and `STRONG_OPPORTUNITY`.
- [x] Add text fields `summary` and `investigated_at`.
- [x] Add migration/schema initialization that is safe to run repeatedly.
- [x] Verify the independent schema works with a copied or exported opportunity dataset.
- [x] Verify Phase 1 database files are untouched after setup and handoff.

## Opportunity Selection and Run Lifecycle

- [x] Select the highest-scoring opportunity with no matching investigation record.
- [x] Create its investigation record before starting research.
- [x] Mark the record `IN_PROGRESS` while processing.
- [x] Prevent duplicate investigations through both selection logic and the unique `app_id` constraint.
- [x] Mark successful runs `COMPLETE` and save `investigated_at`.
- [x] Mark failed runs `FAILED` while preserving the error context needed for diagnosis.
- [x] Exit cleanly when no uninvestigated opportunities remain.
- [x] Keep continuous mode alive when an iteration has no available opportunity so a later Scout sync can add work.

## Research Collection

- [x] Add `research.py` for Phase 2 research orchestration.
- [x] Collect publicly available app information from Google Play.
- [x] Follow and collect the first available developer or documentation link.
- [x] Collect public app descriptions and linked documentation when available.
- [x] Collect user evidence from available public app-page evidence and search results.
- [x] Prioritize 1-star, 2-star, and 3-star reviews while including representative positive reviews.
- [x] Collect a reasonable sample and retain source URLs or other provenance where practical.
- [x] Research competitors using default public web search or an injected search provider.
- [x] Record competitor URLs and search provenance where available.
- [x] Identify alternatives and workarounds through public search evidence.
- [x] Handle unavailable pages, rate limits, malformed content, and partial research without crashing the whole run.

## Analysis and Scoring

- [x] Generate a concise `app_analysis` covering what the app does, the problem, target users, primary features, differentiation, and dependencies.
- [x] Generate a concise `user_analysis` covering user types, problems, severity, frequency, hobbyist/professional context, and willingness to pay.
- [x] Generate a concise `complaint_analysis` from repeated complaints, serious complaints, missing features, solvable complaints, and potential improvements.
- [x] Generate a concise `competitor_analysis` covering market crowding, strong competitors, dominant companies, and smaller competitors.
- [x] Generate a concise `alternative_analysis` covering how users solve the problem without the app.
- [x] Score `build_difficulty` from 1 (very easy) to 10 (extremely difficult).
- [x] Score `proprietary_dependency` from 1 (no meaningful dependency) to 10 (extremely difficult to reproduce).
- [x] Score `market_potential` from 1 (very little apparent demand) to 10 (strong evidence of demand).
- [x] Score `competition_level` from 1 (very little competition) to 10 (extremely competitive).
- [x] Require Ollama to use evidence and avoid assigning inflated scores by default.
- [x] Send the collected research to Ollama for a final assessment.
- [x] Require Ollama to return valid JSON containing `final_score`, `recommendation`, and `summary`.
- [x] Validate score ranges and allowed recommendation values before saving results.
- [x] Treat `final_score` as a 1-10 opportunity score and document the interpretation of score bands: 1-3 `PASS`, 4-5 `INVESTIGATE_FURTHER`, 6-7 `PROMISING`, and 8-10 `STRONG_OPPORTUNITY`.

## `investigate.py` Responsibilities

- [x] Select one opportunity.
- [x] Create and manage the investigation record.
- [x] Run the research workflow.
- [x] Call Ollama with the collected evidence.
- [x] Validate and save all analysis, scoring, recommendation, summary, status, and timestamp fields.
- [x] Provide concise progress and failure logging.
- [x] Exit after one investigation or after reporting that no work is available.

## Validation and Documentation

- [x] Test that the highest-scoring uninvestigated opportunity is selected.
- [x] Test that completed investigations are skipped on later runs.
- [x] Test that the unique app relationship prevents duplicate investigations.
- [x] Test status transitions for success, no-op, and failure paths.
- [x] Test Ollama JSON validation, including invalid JSON and invalid score/recommendation values.
- [x] Run a dry or mocked investigation without external web or Ollama calls.
- [x] Run an end-to-end investigation against a controlled test record when dependencies are available.
- [x] Confirm no file under `1_Scout` changes during Phase 2 setup, handoff, or execution.
- [x] Confirm Phase 1 behavior and database records remain intact by comparing the Phase 1 tree and database before and after Phase 2 operations.

## Phase 2.1 Quality Improvements

- [x] Add additive `raw_reviews`, `raw_competitors`, and `raw_alternatives` fields to `investigations`.
- [x] Preserve bounded raw evidence samples when saving completed investigations.
- [x] Add centralized research limits for reviews, competitors, search results, and pages.
- [x] Continue bounded search research when an opportunity has no URL.
- [x] Add structured complaint-pattern analysis output.
- [x] Add explicit evidence-versus-interpretation fields or prompt structure.
- [x] Add strongest-argument-against reasoning to the final assessment.
- [x] Improve score calibration and require explanations for intermediate scores.
- [x] Add simple retry handling for existing `FAILED` or interrupted `IN_PROGRESS` investigations.
