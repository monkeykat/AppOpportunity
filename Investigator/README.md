# App Opportunity Investigator

Phase 2 is independent from `Scout`. It reads only the Phase 2 SQLite database during normal execution.

## Setup

```bash
cd Investigator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

No Phase 1 module is required at runtime. The research collector uses Python's standard library, preserves source URLs, prioritizes lower-rated review evidence, discovers developer/documentation links, and records partial failures instead of aborting the run. Ollama is called through the Phase 2-owned client.

## Phase 1 handoff

Export opportunities from Phase 1 into a JSON array, then import that export explicitly:

```bash
python3 handoff.py phase_1_opportunities.json
```

Each record must contain `app_id` and `score`. The import creates or updates the Phase 2-owned `opportunities` table in `app_investigator.db`.

For a formal boundary check, snapshot the Phase 1 export source and database before the handoff, then call `boundary_check.assert_unchanged` afterward. This check is explicit and separate from normal Phase 2 execution; the investigator does not discover or open the Scout database automatically.

## Run

```bash
python3 investigate.py
```

Each run processes at most one opportunity. It collects available public evidence, asks Ollama for a structured assessment, validates the scores and recommendation, and stores the result in the Phase 2 database.

Run the offline test suite with:

```bash
python3 -m unittest discover -s tests -v
```

Final score bands are interpreted as follows: `1-3` is `PASS`, `4-5` is `INVESTIGATE_FURTHER`, `6-7` is `PROMISING`, and `8-10` is `STRONG_OPPORTUNITY`. The validator rejects recommendation and score-band mismatches. Ollama must explain build difficulty and proprietary dependency in `app_analysis`, market potential in `user_analysis`, competition in `competitor_analysis`, and the final score in `summary`; scores of 8 or higher require strong evidence and remain uncommon.

## Phase 2.1 Evidence and Research Limits

Investigations preserve bounded JSON samples in the existing `investigations` table:

- `raw_reviews`
- `raw_competitors`
- `raw_alternatives`

Existing Phase 2 databases are migrated additively when `init_database()` runs. No additional tables are created.

Research limits are centralized in `config.py` and can be overridden with environment variables:

```text
MAX_REVIEWS_PER_APP=30
MAX_COMPETITORS=10
MAX_SEARCH_RESULTS_PER_TOPIC=10
MAX_RESEARCH_PAGES=30
```

The collector continues with bounded search research when an imported opportunity does not have a public URL. Missing pages and incomplete source data remain recorded as evidence errors rather than aborting collection.

The Ollama assessment separates observed evidence from interpretation, asks for repeated complaint patterns, requires a strongest argument against the opportunity, and treats high scores as rare. That counterargument is folded into the existing `summary` field. A failed investigation can be retried in place, and interrupted `IN_PROGRESS` records are marked `FAILED` at startup; completed investigations are never automatically repeated.