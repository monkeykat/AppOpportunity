# Phase 3 Business Validator

Phase 3 evaluates whether completed Phase 2 opportunities could become viable
businesses. It is independent from Phase 1 and Phase 2 and operates on its own
copy of the Phase 2 SQLite database.

## Current Foundation

The Validator currently provides:

- A Phase 3-owned `business_validations` table.
- Selection of one completed `STRONG_OPPORTUNITY` or `PROMISING` Phase 2 record.
- Priority for `STRONG_OPPORTUNITY`, then highest Phase 2 score.
- One validation per app through a unique database constraint.
- Failed validations are retried in place on later runs.
- `PENDING`, `IN_PROGRESS`, `COMPLETE`, and `FAILED` lifecycle states.
- Strict viability score and recommendation-band validation.
- A skeptical Ollama prompt and JSON client.
- Phase 2 evidence packaging for the first business-analysis pass.
- Bounded research topics for monetization, willingness to pay, advertising,
  market size, and customer acquisition.

## Database Copy

The working database is `3_Validator/app_validator.db`. Each run automatically copies
or synchronizes data from Phase 2's `2_Investigator/app_investigator.db` into
this private database before selecting an opportunity. Existing Phase 3
`business_validations` records are preserved; the source Investigator database
is never modified.

Business-topic research uses `MAX_SEARCH_RESULTS` (default `10`) per topic and
`MAX_RESEARCH_PAGES` (default `20`) across one run. Search can be injected in
tests; the normal entry point uses the standard-library public searcher.

## Run

From the repository root:

```text
python3 3_Validator/validate_business.py
```

The command first synchronizes completed and newly added Phase 2 data, then
processes one eligible opportunity. It exits cleanly when no eligible completed
Phase 2 opportunity is available. Tests use temporary databases and injected
research and analysis callbacks.

Each run prints progress to the terminal and writes the same output to a
timestamped log under `3_Validator/logs/`.

To process eligible business opportunities continuously, run:

```text
python3 3_Validator/run_continuous.py
```

Continuous mode synchronizes `2_Investigator` before every iteration, processes
one opportunity at a time, waits 30 seconds between iterations by default, and
stops when no eligible opportunities remain. Change the delay with
`--interval`:

```text
python3 3_Validator/run_continuous.py --interval 60
```

Set `VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS` in the shared `.env` file to
limit the total runtime. `0` means run until interrupted with `Ctrl+C`:

```env
VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS=3600
```

Each continuous iteration creates its own timestamped log.

Run the current tests with:

```text
python3 -m unittest discover -s 3_Validator/tests -v
```

## Configuration and Recommendations

The Validator uses Python, SQLite, Ollama, and standard-library public web
research. Set `VALIDATOR_DATABASE_PATH`, `OLLAMA_URL`, `VALIDATOR_OLLAMA_MODEL`,
`MAX_SEARCH_RESULTS`, or `MAX_RESEARCH_PAGES` in the environment when needed.

Viability scores use these bands:

- `1-3`: `PASS`
- `4-5`: `POSSIBLE`
- `6-7`: `PROMISING`
- `8-10`: `BUILD_CANDIDATE`

`BUILD_CANDIDATE` is deliberately rare. It requires evidence of demand,
active solution-seeking, meaningful differentiation, plausible monetization,
an adequate apparent market, and reachable customers. It is not a guarantee
of business success.

The database flow is one-way and copy-based: Phase 1 produces its database,
Phase 2 owns `2_Investigator/app_investigator.db`, and Phase 3 synchronizes the
Phase 2 tables into `3_Validator/app_validator.db`. Phase 3 adds only
`business_validations` to its private copy.