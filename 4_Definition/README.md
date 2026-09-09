# Phase 4: Product Definition

Phase 4 turns a completed Validator opportunity into a focused product
hypothesis and the smallest product worth validating. It does not repeat
business validation or design the POC architecture.

## Database Ownership

Phase 4 copies `3_Validator/app_validator.db` to its private
`4_Definition/app_designer.db`. It preserves inherited Phase 2 and Phase 3 data
and adds the `product_designs` table. The Validator database is never modified.

A completed design is eligible for Phase 5 only when:

```text
status = COMPLETE
recommendation = READY_FOR_POC
```

The source Phase 3 validation must still match the saved validation snapshot.
Changed source validations make a design `STALE` and require redesign.

## Run One Design

From the workspace root:

```bash
/home/gulfaero/Documents/Code/App\ Opportunity/1_Scout/.venv/bin/python 4_Definition/design_product.py
```

Or from `4_Definition/`:

```bash
../1_Scout/.venv/bin/python design_product.py
```

The run selects one eligible opportunity, sends bounded Phase 2 and Phase 3
evidence to Ollama, validates the complete structured product design, and saves
it atomically.

## Continuous Mode

Set `PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS` in the shared `.env`
file. A value of `0` runs until interrupted.

```bash
/home/gulfaero/Documents/Code/App\ Opportunity/1_Scout/.venv/bin/python 4_Definition/run_continuous.py --interval 30
```

Logs are written to `4_Definition/logs/` and mirrored to the terminal.

## Tests

```bash
/home/gulfaero/Documents/Code/App\ Opportunity/1_Scout/.venv/bin/python -m unittest discover -s 4_Definition/tests -v
```
