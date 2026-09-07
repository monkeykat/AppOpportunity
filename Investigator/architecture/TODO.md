# Phase 2 MVP: App Opportunity Investigator

Architecture source: `phase_2_app_investigator_design.rtf`

## Scope and Constraints

- [ ] Keep all Phase 2 work in the `Investigator` folder.
- [ ] Preserve every file and database in `Scout` exactly as-is.
- [ ] Do not import Phase 1 Python modules at runtime.
- [ ] Do not read from, write to, migrate, or extend the Phase 1 database.
- [ ] Recreate any required support modules inside `Investigator`.
- [ ] Use a separate Phase 2 SQLite database, `app_investigator.db`.
- [ ] Define an explicit, one-way handoff for copying Phase 1 opportunity data into the Phase 2 database.
- [ ] Keep the MVP dependency set minimal: Python, SQLite, Ollama, and Playwright.
- [ ] Do not build a frontend.
- [ ] Do not build a complex multi-agent system.
- [ ] Process exactly one opportunity per run.
- [ ] Ensure an app can have only one investigation.

## Project Setup

- [ ] Define the Phase 2-owned project root and database path.
- [ ] Define the Investigator entry point: `python investigate.py`.
- [ ] Recreate Phase 2-owned configuration for research, Playwright, Ollama, and database paths.
- [ ] Recreate Phase 2-owned database, Google Play, and Ollama client modules as needed; do not import their Phase 1 counterparts.
- [ ] Define and implement the Phase 1-to-Phase 2 opportunity data handoff without changing `Scout`.
- [ ] Add or update the Investigator README with setup, dependencies, Ollama requirements, and run instructions.
- [ ] Add focused tests or smoke checks for database creation, selection, research parsing, and result persistence.

## Database

- [ ] Create `app_investigator.db` owned exclusively by Phase 2.
- [ ] Recreate the minimum Phase 1-compatible `opportunities` schema needed for Phase 2 selection.
- [ ] Populate the Phase 2 `opportunities` table through the explicit Phase 1 data handoff.
- [ ] Add the Phase 2 `investigations` table without changing any Phase 1 database.
- [ ] Add a primary key `id`.
- [ ] Add a unique `app_id` relationship to the Phase 2 `opportunities` table.
- [ ] Add `status` with the values `PENDING`, `IN_PROGRESS`, `COMPLETE`, and `FAILED`.
- [ ] Add text fields: `app_analysis`, `user_analysis`, `complaint_analysis`, `competitor_analysis`, and `alternative_analysis`.
- [ ] Add scoring fields: `build_difficulty`, `proprietary_dependency`, `market_potential`, `competition_level`, and `final_score`.
- [ ] Add `recommendation` with the values `PASS`, `INVESTIGATE_FURTHER`, `PROMISING`, and `STRONG_OPPORTUNITY`.
- [ ] Add text fields `summary` and `investigated_at`.
- [ ] Add migration/schema initialization that is safe to run repeatedly.
- [ ] Verify the independent schema works with a copied or exported opportunity dataset.
- [ ] Verify Phase 1 database files are untouched after setup and handoff.

## Opportunity Selection and Run Lifecycle

- [ ] Select the highest-scoring opportunity with no matching investigation record.
- [ ] Create its investigation record before starting research.
- [ ] Mark the record `IN_PROGRESS` while processing.
- [ ] Prevent duplicate investigations through both selection logic and the unique `app_id` constraint.
- [ ] Mark successful runs `COMPLETE` and save `investigated_at`.
- [ ] Mark failed runs `FAILED` while preserving the error context needed for diagnosis.
- [ ] Exit cleanly when no uninvestigated opportunities remain.

## Research Collection

- [ ] Add `research.py` for Phase 2 research orchestration.
- [ ] Collect publicly available app information from Google Play.
- [ ] Follow the developer website when available.
- [ ] Collect public app descriptions and documentation when available.
- [ ] Collect user evidence from Google Play reviews, Reddit, public forums, relevant communities, and app marketing.
- [ ] Prioritize 1-star, 2-star, and 3-star reviews while including representative positive reviews.
- [ ] Collect a reasonable sample and retain source URLs or other provenance where practical.
- [ ] Research approximately 3-10 competitors using Google Play, relevant websites, and public web search.
- [ ] Record competitor name, purpose, rating, popularity, strengths, and weaknesses where available.
- [ ] Identify alternatives and workarounds, including spreadsheets, paper notes, social groups, manual processes, generic software, websites, YouTube, separate apps, physical tools, and doing nothing.
- [ ] Handle unavailable pages, rate limits, malformed content, and partial research without crashing the whole run.

## Analysis and Scoring

- [ ] Generate a concise `app_analysis` covering what the app does, the problem, target users, primary features, differentiation, and dependencies.
- [ ] Generate a concise `user_analysis` covering user types, problems, severity, frequency, hobbyist/professional context, and willingness to pay.
- [ ] Generate a concise `complaint_analysis` from repeated complaints, serious complaints, missing features, solvable complaints, and potential improvements.
- [ ] Generate a concise `competitor_analysis` covering market crowding, strong competitors, dominant companies, and smaller competitors.
- [ ] Generate a concise `alternative_analysis` covering how users solve the problem without the app.
- [ ] Score `build_difficulty` from 1 (very easy) to 10 (extremely difficult).
- [ ] Score `proprietary_dependency` from 1 (no meaningful dependency) to 10 (extremely difficult to reproduce).
- [ ] Score `market_potential` from 1 (very little apparent demand) to 10 (strong evidence of demand).
- [ ] Score `competition_level` from 1 (very little competition) to 10 (extremely competitive).
- [ ] Require Ollama to use evidence and avoid assigning inflated scores by default.
- [ ] Send the collected research to Ollama for a final assessment.
- [ ] Require Ollama to return valid JSON containing `final_score`, `recommendation`, and `summary`.
- [ ] Validate score ranges and allowed recommendation values before saving results.
- [ ] Treat `final_score` as a 1-10 opportunity score and document the interpretation of score bands: 1-3 `PASS`, 4-5 `INVESTIGATE_FURTHER`, 6-7 `PROMISING`, and 8-10 `STRONG_OPPORTUNITY`.

## `investigate.py` Responsibilities

- [ ] Select one opportunity.
- [ ] Create and manage the investigation record.
- [ ] Run the research workflow.
- [ ] Call Ollama with the collected evidence.
- [ ] Validate and save all analysis, scoring, recommendation, summary, status, and timestamp fields.
- [ ] Provide concise progress and failure logging.
- [ ] Exit after one investigation or after reporting that no work is available.

## Validation and Documentation

- [ ] Test that the highest-scoring uninvestigated opportunity is selected.
- [ ] Test that completed investigations are skipped on later runs.
- [ ] Test that the unique app relationship prevents duplicate investigations.
- [ ] Test status transitions for success, no-op, and failure paths.
- [ ] Test Ollama JSON validation, including invalid JSON and invalid score/recommendation values.
- [ ] Run a dry or mocked investigation without external web or Ollama calls.
- [ ] Run an end-to-end investigation against a controlled test record when dependencies are available.
- [ ] Confirm no file under `Scout` changes during Phase 2 setup, handoff, or execution.
- [ ] Confirm Phase 1 behavior and database records remain intact by comparing the Phase 1 tree and database before and after Phase 2 operations.
