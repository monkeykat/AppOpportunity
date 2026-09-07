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
- `PENDING`, `IN_PROGRESS`, `COMPLETE`, and `FAILED` lifecycle states.
- Strict viability score and recommendation-band validation.
- A skeptical Ollama prompt and JSON client.
- Phase 2 evidence packaging for the first business-analysis pass.
- Bounded research topics for monetization, willingness to pay, advertising,
  market size, and customer acquisition.

## Database Copy

The working database is `Validator/app_scout.db`. It was copied from the
completed Phase 2 database and may receive only the Phase 3
`business_validations` table. The source Phase 2 database is not opened for
normal Validator execution.

Business-topic research uses `MAX_SEARCH_RESULTS` (default `10`) per topic and
`MAX_RESEARCH_PAGES` (default `20`) across one run. Search can be injected in
tests; the normal entry point uses the standard-library public searcher.

## Run

From the repository root:

```text
python3 Validator/validate_business.py
```

The current database contains no eligible completed Phase 2 opportunity, so the
entry point exits cleanly until one is available. Tests use temporary databases
and injected research and analysis callbacks.

Run the current tests with:

```text
python3 -m unittest Validator.tests.test_validator -v
```

## Configuration and Recommendations

The Validator uses Python, SQLite, Ollama, and standard-library public web
research. Set `VALIDATOR_DATABASE_PATH`, `OLLAMA_URL`, `OLLAMA_MODEL`,
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
Phase 2 works on its own copy, and Phase 3 works on `Validator/app_scout.db`.
Phase 3 adds only `business_validations` to its private copy.