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

Final score bands are interpreted as follows: `1-3` is `PASS`, `4-5` is `INVESTIGATE_FURTHER`, `6-7` is `PROMISING`, and `8-10` is `STRONG_OPPORTUNITY`.