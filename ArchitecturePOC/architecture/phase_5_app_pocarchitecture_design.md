# Phase 5: POC Architecture

## Goal

Phase 1 finds interesting apps (Complete). Phase 2 investigates whether a real opportunity
exists (Complete). Phase 3 determines whether the opportunity could become a viable
business (Complete). Phase 4 determines what to build, for whom, and the smallest product
worth validating (Complete).

Phase 5 asks:

**Exactly how should that validation product be structured, and what must work for its proof of concept to count as complete?**

The goal is an implementation-ready architecture for one small proof of
concept. This is not a production architecture, a business plan, or a second
product-definition phase. It is the focused technical plan that lets Phase 6
build and verify the product decision made in Phase 4.

Phase 5 owns the architecture and acceptance contract. It must preserve the
Phase 4 core problem, target user, validation hypothesis, core workflow, and
minimum validation scope. It must not silently add or remove product behavior.

There is no frontend for the Phase 5 pipeline itself. Its output is stored in
SQLite.

## Core Concept

```text
PHASE 4 PRODUCT DEFINITION
	|
	v
READ THE AUTHORITATIVE VALIDATION TARGET
	|
	v
CHOOSE THE SIMPLEST TECHNICAL APPROACH
	|
	v
DEFINE COMPONENTS, DATA FLOW, AND PERSISTENCE
	|
	v
MAP THE CORE WORKFLOW TO ACCEPTANCE TESTS
	|
	v
DEFINE WHAT "WORKING POC" MEANS
	|
	v
PHASE 5 POC ARCHITECTURE
	|
	v
PHASE 6 POC BUILDER
```

## Important Phase Separation Rule

Phase 5 consumes a completed Phase 4 output. It does not repeat Scout,
Investigator, Validator, or Product Definition work.

Phase 4 remains authoritative for:

- `core_problem`
- `target_user`
- `validation_hypothesis`
- `core_user_workflow`
- `minimum_validation_scope`
- `must_have_features`
- `excluded_features`
- `success_criteria`

Phase 5 decides how to implement and test that scope with the smallest
reasonable architecture. A technical simplification is allowed only when its
reason, impact, and effect on the validation hypothesis are recorded.

Phase 6 implements the approved Phase 5 architecture. It should not need to
re-run prior phase analysis to decide what to build.

## Technology

Use:

- Python
- SQLite
- Ollama

Use the existing phase patterns for configuration, logging, database access,
handoff, structured Ollama output validation, and continuous execution. Keep
dependencies minimal. Do not build a complicated multi-agent system.

Phase 5 may recommend an appropriate POC technology, but it must be justified
by the core workflow and favor the smallest practical implementation.

## Database and Handoff

Copy the completed Phase 4 database from:

`Definition/app_designer.db`

into the Phase 5-owned database:

`ArchitecturePOC/app_poc_architecture.db`

Phase 5 reads and writes only its private copy and must never modify the Phase
4 database. On the first run, copy the source database. On later runs,
synchronize new and changed inherited Phase 4 data while preserving existing
Phase 5 architecture records.

Do not redesign inherited tables. Phase 5 adds one table:

`poc_architectures`

### poc_architectures

Stores the technical architecture and completion contract for one Phase 4
product design.

```text
id
app_id
product_design_id
status

architecture_summary
poc_platform
runtime_and_entrypoint
technology_choices
architecture_rationale

core_workflow_steps
workflow_acceptance_steps
component_plan
data_model
data_flow
external_dependencies
permissions_and_configuration

build_plan
test_plan
completion_criteria
known_limitations
technical_risks
scope_deviations

architecture_score
recommendation

created_at
architected_at
error
```

`product_design_id` must be `NOT NULL UNIQUE` and reference the copied
`product_designs` record. `app_id` must reference the inherited opportunity.
Store multi-value fields as JSON arrays or JSON objects and validate them
before persistence. `architecture_score` must be an integer from 1 to 10.

### Status

Possible values:

```text
PENDING
IN_PROGRESS
COMPLETE
FAILED
```

The lifecycle follows the earlier phases:

1. Create or recover a `PENDING` record.
2. Mark it `IN_PROGRESS` before analysis begins.
3. Validate the complete architecture output.
4. Save all fields in one transaction and mark it `COMPLETE`.
5. On an error, store the error and mark it `FAILED`.
6. Recover abandoned `IN_PROGRESS` records as `FAILED` on the next run.
7. Retry a failed record in place; do not create a duplicate.
8. Do not automatically repeat completed architectures.

## Selecting a Product Design

Phase 5 processes only completed Phase 4 designs where:

```text
product_designs.status = COMPLETE
product_designs.recommendation = READY_FOR_POC
```

Select a design when it has no architecture record or its existing architecture
has `status = FAILED`. Prioritize the highest Phase 4 `design_score`, then use
`app_id` as a deterministic tie-breaker. Do not process `PASS` or
`DESIGN_REVIEW` designs, and do not architect the same product design twice.

## Main Loop

Each run architects one product.

```text
SYNCHRONIZE PHASE 4 HANDOFF
	|
	v
SELECT READY_FOR_POC PRODUCT DESIGN
	|
	v
READ AUTHORITATIVE PRODUCT DEFINITION
	|
	v
MAP THE CORE WORKFLOW
	|
	v
CHOOSE THE SIMPLEST TECHNICAL APPROACH
	|
	v
DEFINE COMPONENTS, DATA, AND DEPENDENCIES
	|
	v
DEFINE BUILD PLAN AND ACCEPTANCE TESTS
	|
	v
VALIDATE THE ARCHITECTURE CONTRACT
	|
	v
SAVE OR RECORD FAILURE
	|
	v
EXIT
```

## Architecture Process

### Step 1: Read the Product Definition

Read the selected Phase 4 design. Treat the following as immutable product
inputs:

```text
core_problem
target_user
validation_hypothesis
core_user_workflow
minimum_validation_scope
must_have_features
excluded_features
success_criteria
```

Read `technical_considerations`, `design_rationale`, and
`inherited_constraints` for feasibility constraints. Do not recreate market
research or business validation.

### Step 2: Confirm the POC Boundary

Translate `minimum_validation_scope` into a clear architecture boundary.

Answer:

- What must a user do from start to finish?
- What observable result proves the workflow ran successfully?
- Which one to three capabilities are essential?
- What is explicitly absent from the POC?
- Does the approach still test the Phase 4 hypothesis?

Store this as `architecture_summary` and `core_workflow_steps`. The POC must
demonstrate the core workflow, not merely display a mock screen or disconnected
components.

### Step 3: Choose the Simplest Suitable Platform

Recommend the smallest platform capable of proving the core workflow:

```text
LOCAL_WEB_APP
LOCAL_DESKTOP_APP
COMMAND_LINE_APP
MOBILE_PROTOTYPE
STATIC_INTERACTIVE_PROTOTYPE
```

Choose the platform because it lets the target user complete the workflow and
observe the intended result with the least complexity, not because it is
fashionable. Store `poc_platform`, `runtime_and_entrypoint`,
`technology_choices`, and `architecture_rationale`.

`runtime_and_entrypoint` must give the exact command or startup action Phase 6
must provide.

### Step 4: Define the Components

Define only components required by the core workflow. Each component must state
its responsibility, input, output, and dependency on other components.

Example component plan for a local fishing journal POC:

```json
[
  {
    "name": "trip_form",
    "responsibility": "Collect a new fishing-trip record.",
    "input": "Trip details entered by the user.",
    "output": "Validated trip record."
  },
  {
    "name": "catch_form",
    "responsibility": "Record a catch for an existing trip.",
    "input": "Catch details and selected trip.",
    "output": "Persisted catch record."
  },
  {
    "name": "history_view",
    "responsibility": "Show saved catches to the user.",
    "input": "Persisted records.",
    "output": "Readable catch history."
  }
]
```

Do not introduce services, queues, microservices, background workers, or
separate deployment tiers unless the Phase 4 workflow cannot work without
them. Store this plan as `component_plan`.

### Step 5: Define Data and Data Flow

Describe the smallest persistent model needed for the workflow. This is a POC
data model, not a production schema. For each record, identify only fields
needed to create, save, and display the expected result.

Define the end-to-end flow:

```text
USER INPUT
    -> VALIDATION
    -> CORE APPLICATION ACTION
    -> PERSISTENCE OR REQUIRED INTEGRATION
    -> OBSERVABLE USER RESULT
```

Store `data_model` and `data_flow`. The architecture must explain where data
lives during the POC, how it survives when persistence is required, and how the
user can observe the saved or computed result.

### Step 6: Identify Dependencies and Configuration

List only dependencies required by the POC. For each dependency, state why the
core workflow needs it, whether it is local, public, paid, or credentialed,
what happens if it is unavailable, and whether a local fixture, fake, or stub
can validate the workflow instead.

Do not require paid APIs, cloud accounts, authentication, analytics,
notifications, or third-party infrastructure simply to make the POC resemble a
full product.

Store `external_dependencies`, `permissions_and_configuration`, and
`technical_risks`.

### Step 7: Produce the Build Plan

Create a short ordered plan that Phase 6 can execute. Every step must build or
verify a visible portion of the core workflow.

```text
1. Create the POC project and runnable entrypoint.
2. Implement the smallest local persistence model.
3. Build the input path for the first workflow action.
4. Build the core action and save its result.
5. Build the result view that makes the outcome observable.
6. Run the POC and complete the workflow manually.
7. Add focused automated checks for persistence and the core workflow.
```

Store this as `build_plan`.

### Step 8: Define Acceptance Tests and Completion Criteria

Convert `success_criteria` into concrete checks. Every acceptance step must
have a precondition, user action, expected result, and verification method.

```json
[
  {
    "precondition": "The POC is running with an empty local database.",
    "action": "Create a fishing trip and record a catch.",
    "expected_result": "The catch is saved and visible in the history view.",
    "verification": "Manual workflow test and focused persistence test."
  }
]
```

Store `workflow_acceptance_steps`, `test_plan`, and `completion_criteria`.

A POC is complete only when:

1. The documented setup and start command works.
2. A representative user can complete the entire `core_user_workflow`.
3. Every capability in `minimum_validation_scope` works end to end.
4. The user can observe the result required by `validation_hypothesis`.
5. Every Phase 4 `success_criteria` item has a manual or automated check.
6. Excluded features are absent unless invisible technical support requires
   them.
7. Known limitations, setup requirements, and approved deviations are
   documented.

### Step 9: Record Deviations and Limitations

Record `scope_deviations` only when a technical constraint requires departure
from Phase 4. Each entry must include the original requirement, technical
reason, replacement approach, and impact on the validation hypothesis.

If a deviation prevents testing the hypothesis, the architecture must not
receive `READY_TO_BUILD`. Record non-blocking POC constraints separately in
`known_limitations`.

## Structured Ollama Output

Ollama may help create the architecture, but the program must validate every
required field before writing it. Use one complete JSON response rather than
separate partial summaries.

The prompt must require the Phase 4 product definition as authoritative; forbid
new product features or repeated business validation; require the simplest
architecture capable of completing and testing the workflow; and demand valid
JSON matching the required schema.

The required output shape is:

```json
{
  "architecture_summary": "How the POC proves the product hypothesis.",
  "poc_platform": "LOCAL_WEB_APP",
  "runtime_and_entrypoint": "Exact command or startup action.",
  "technology_choices": ["Python", "SQLite"],
  "architecture_rationale": "Why this is the simplest suitable approach.",
  "core_workflow_steps": ["Open", "Create record", "View result"],
  "workflow_acceptance_steps": [
    {
      "precondition": "Required starting state.",
      "action": "User action.",
      "expected_result": "Observable result.",
      "verification": "How to verify it."
    }
  ],
  "component_plan": [
    {
      "name": "component_name",
      "responsibility": "What it does.",
      "input": "What it receives.",
      "output": "What it produces."
    }
  ],
  "data_model": [
    {
      "entity": "entity_name",
      "required_fields": ["field_name"],
      "purpose": "Why this data is needed."
    }
  ],
  "data_flow": ["User action", "Validation", "Persistence", "Visible result"],
  "external_dependencies": [],
  "permissions_and_configuration": [],
  "build_plan": ["Ordered build step"],
  "test_plan": ["Focused test or manual check"],
  "completion_criteria": ["Verifiable completion condition"],
  "known_limitations": [],
  "technical_risks": [],
  "scope_deviations": [],
  "architecture_score": 1,
  "recommendation": "PASS | ARCHITECTURE_REVIEW | READY_TO_BUILD"
}
```

## Architecture Score

The architecture score measures whether the POC is focused, buildable, and
capable of testing the Phase 4 validation hypothesis. It does not re-evaluate
business viability or product desirability.

```text
Score 1-3: PASS
The workflow cannot be implemented simply, does not test the hypothesis, or
requires unresolved dependencies.

Score 4-5: ARCHITECTURE_REVIEW
The product remains promising, but the architecture has material ambiguity,
avoidable complexity, or incomplete acceptance criteria.

Score 6-10: READY_TO_BUILD
The architecture preserves the validation target, has bounded implementation
scope, and defines a runnable, testable POC completion contract.
```

The implementation must reject a score/recommendation mismatch:

```text
1-3  -> PASS
4-5  -> ARCHITECTURE_REVIEW
6-10 -> READY_TO_BUILD
```

Only architecture records with `status = COMPLETE` and
`recommendation = READY_TO_BUILD` are eligible for Phase 6.

## Running the Application

The Phase 5 architecture program is:

```text
python architecture_poc.py
```

Each run should:

1. Synchronize the Phase 4 database handoff.
2. Select one eligible `READY_FOR_POC` product design.
3. Read the authoritative product definition.
4. Define the POC boundary and core workflow implementation.
5. Choose the simplest suitable platform and runtime.
6. Define components, data model, data flow, dependencies, and configuration.
7. Create the build plan, test plan, and acceptance checklist.
8. Record deviations, risks, and limitations.
9. Validate the complete structured architecture output.
10. Score the architecture and validate its recommendation.
11. Save the architecture atomically to SQLite.
12. Exit.

Provide a continuous runner consistent with earlier phases:

```text
python run_continuous.py
```

It processes one architecture at a time, stops when no eligible designs remain,
and reads its duration from:

```text
POC_ARCHITECTURE_CONTINUOUS_RUN_DURATION_SECONDS
```

Use timestamped logs in `ArchitecturePOC/logs/` and print meaningful progress
before handoff, selection, analysis, Ollama calls, validation, saving, retry,
and completion.

## Project Structure

```text
ArchitecturePOC/
├── architecture_poc.py
├── run_continuous.py
├── handoff.py
├── database.py
├── analysis.py
├── ollama_client.py
├── config.py
├── run_log.py
├── requirements.txt
├── README.md
├── tests/
│   └── test_phase5.py
├── logs/
├── architecture/
│   └── phase_5_app_pocarchitecture_design.md
└── app_poc_architecture.db
```

Keep the Phase 5 pipeline simple. It should not include a user-facing frontend,
FastAPI, Docker, authentication, cloud deployment, RAG, vector databases,
microservices, or autonomous coding-agent orchestration. Those are not needed
to produce a POC architecture.

## Definition of Done

Phase 5 is complete when `python architecture_poc.py` can:

1. Copy and synchronize the Phase 4 database into its own database.
2. Select exactly one eligible completed `READY_FOR_POC` product design.
3. Preserve the Phase 4 product decision as authoritative input.
4. Create one retryable architecture record per selected product design.
5. Define a minimal platform, runtime, components, data model, and data flow.
6. Define only dependencies required by the core workflow.
7. Produce a short Phase 6 build plan.
8. Produce concrete workflow acceptance steps and focused tests.
9. Define verifiable POC completion criteria mapped to Phase 4 success criteria.
10. Record technical risks, known limitations, and scope deviations.
11. Validate JSON structure, lifecycle state, score, and recommendation before
    persistence.
12. Save a completed architecture only when it is buildable and can test the
    Phase 4 hypothesis.
13. Retry failed records in place without repeating completed work.
14. Make only completed `READY_TO_BUILD` architectures available to Phase 6.
15. Log and report progress, failures, retries, and queue completion.
