Phase 6: POC Builder

Goal

Phase 1 finds interesting apps. (Complete)

Phase 2 investigates whether there is a real opportunity. (Complete)

Phase 3 determines whether it could potentially be a viable business. (Complete)

Phase 4 determines what should be built instead? (Complete)

Phase 5 creates a full design architecture for a POC (Complete)

Phase 6 asks:

Can we build a basic version of it that validates the idea?

The goal is to autonomously build a very small Proof of Concept.

This is not the full application.

This is not production software.

This phase should build only enough of the product to demonstrate the core idea.

APPROVED POC ARCHITECTURE

↓

CREATE ISOLATED BUILD WORKSPACE

↓

EXECUTE APPROVED BUILD PLAN

↓

BUILD

↓

TEST

↓

WORKING, TESTED POC

Core Concept

PHASE 5

"How must the POC be built and verified?"

↓

PHASE 6

"Can we build and prove the approved POC works?"

↓

WORKING POC

The Autonomous Builder should take an approved POC architecture like:

Simple fishing journal

And not build:

❌ Complete mobile application

❌ User accounts

❌ Cloud infrastructure

❌ Social features

❌ Payments

❌ Notifications

❌ Analytics

❌ Every feature from the product design

Instead, it might build:

✓ Create fishing trip

✓ Add catch

✓ View saved catches

That's it.

The POC exists to prove:

The core concept actually works.

Input and Handoff

Phase 6 consumes a private copy of the completed Phase 5 database from:

ArchitecturePOC/app_poc_architecture.db

into the Phase 6-owned database:

BuildPOC/app_builder.db

Phase 6 must not modify the Phase 5 database. On its first run it copies the
source database; later runs synchronize new and changed inherited records while
preserving its own build records.

The primary input is the completed Phase 5 POC architecture. Phase 4 research
and product definition are inherited context, not instructions to re-decide the
product or its architecture.

Selecting an Architecture

Select one architecture where:

```text
poc_architectures.status = COMPLETE
poc_architectures.recommendation = READY_TO_BUILD
```

Select it only if it has no build record or its existing build record failed.
Prioritize the highest architecture score and use app ID as a deterministic
tie-breaker.

Only build one product at a time.

Main Loop

SYNCHRONIZE PHASE 5 HANDOFF

↓

SELECT READY_TO_BUILD ARCHITECTURE

↓

CREATE ISOLATED BUILD WORKSPACE

↓

EXECUTE APPROVED BUILD PLAN

↓

RUN DOCUMENTED ENTRYPOINT

↓

EXECUTE ACCEPTANCE TESTS

↓

BUILD POC

↓

RUN APPLICATION

↓

VERIFY COMPLETION CRITERIA

↓

FIX OBVIOUS PROBLEMS

↓

SAVE BUILD EVIDENCE

↓

EXIT

Step 1: Read the Approved POC Architecture

Read:

product_design_id

poc_platform

runtime_and_entrypoint

technology_choices

core_workflow_steps

component_plan

data_model

data_flow

external_dependencies

build_plan

test_plan

workflow_acceptance_steps

completion_criteria

Phase 6 must implement this architecture without redefining the Phase 4
validation hypothesis, core workflow, minimum validation scope, or the Phase 5
technical plan. Any necessary deviation must record its reason, impact, and
whether the validation hypothesis remains testable.

Step 2: Create an Isolated Build Workspace

Create the generated POC in a phase-owned directory:

BuildPOC/builds/<poc_architecture_id>/

The builder may write only inside this workspace. It must not modify earlier
phase source code or databases, write outside the generated POC directory, use
sudo, or copy secrets into generated code or logs.

Record the exact project path and the architecture snapshot used for this
build. This makes every generated POC reproducible even if a later handoff
synchronization changes inherited records.

Step 3: Execute the Approved Architecture

Phase 6 must follow the Phase 5 `build_plan`, platform, technology choices,
data model, component plan, and dependencies. It may choose file names and
small local implementation details, but it must not redesign the POC.

The POC may implement only the approved core workflow and acceptance criteria.
Do not add product features simply because an autonomous coding agent suggests
them.

Step 4: Build and Run the POC

Give the coding agent the approved architecture, build plan, excluded features,
allowed dependency commands, attempt budgets, required workspace, and expected
final report. The agent must report changed files, commands run, packages
installed, run command, test command, results, limitations, and errors.

The Phase 6 controller must independently run the documented
`runtime_and_entrypoint`; it must not rely on an agent statement that the
application works.

Step 5: Verify the Acceptance Contract

Run the Phase 5 `test_plan`, `workflow_acceptance_steps`, and
`completion_criteria`. For each acceptance step, save:

```text
precondition
action performed
expected result
observed result
verification method
PASS or FAIL
relevant log, screenshot, or test-output path
```

An application that starts is not complete unless every required acceptance
criterion passes. A technically complete POC proves the approved workflow can
run; it does not prove customer demand, retention, or willingness to pay.

Step 6: Repair Within the Approved Scope

One build attempt means generating or changing code and running the documented
entrypoint. One repair attempt means making one targeted change after a failed
build, startup, test, or acceptance check.

After every repair, run the same acceptance contract again. Do not add features
or change the architecture merely to make a test pass. Stop when the budget is
exhausted, an approved dependency is unavailable, or the POC can no longer test
the validation hypothesis.

Step 7: Save Build Evidence

Save a concise summary and the structured execution evidence before marking the
record complete or failed.

This part will likely require further design later.

For now, the general concept is:

PRODUCT DESIGN

↓

BUILD INSTRUCTIONS

↓

AUTONOMOUS CODING SYSTEM

↓

SOURCE CODE

↓

RUN APPLICATION

The Autonomous Builder should use an agentic coding system to build the POC.

Possible future options could include:

Roo Code

Codex

OpenCode

Claude Code

Local Ollama coding agent

Custom agent harness

The specific coding system does not need to be decided yet.

Phase 6 should be designed so the builder can eventually use whichever coding agent you decide works best.

Builder Responsibilities

The coding system should:

Create project

Write code

Run application

Check for errors

Fix obvious errors

Run again

The goal is to reach:

APPLICATION RUNS

Not:

APPLICATION IS PERFECT

Step 7: Test the Core Workflow

After building, test the primary workflow.

Example:

START APPLICATION

↓

CREATE FISHING TRIP

↓

ADD CATCH

↓

SAVE

↓

VIEW CATCH

The test can initially be very simple.

The builder should verify:

Application starts

Core workflow works

Data is saved

No obvious crashes

Step 8: Fix Obvious Problems

If the application fails:

APPLICATION DOES NOT START

Fix it.

If:

CORE WORKFLOW DOES NOT WORK

Fix it.

Do not enter an endless development cycle.

The system should have limits.

Example:

Maximum build attempts: 3

Maximum fix attempts: 5

These values can be configuration options.

If the POC still fails:

BUILD_FAILED

Save the result.

Do not endlessly attempt to fix it.

Database

Continue using:

app_builder.db

Phase 6 should add one table:

poc_builds

7. poc_builds

Fields:

id

app_id

product_design_id

poc_architecture_id

status

failure_category

poc_description

core_workflow

technology

project_path

architecture_snapshot

build_plan_snapshot

agent_name

agent_input

build_attempt_count

repair_attempt_count

run_command

test_command

build_log_path

run_log_path

test_log_path

build_result

test_result

acceptance_result

artifact_manifest

scope_deviations

known_limitations

error

created_at

completed_at

`poc_architecture_id` must be `NOT NULL UNIQUE` and reference the inherited
`poc_architectures` record. `app_id` and `product_design_id` must identify the
inherited opportunity and product design. Store snapshots, plans, acceptance
results, manifests, and multi-value fields as validated JSON.

Possible values:

PENDING

IN_PROGRESS

COMPLETE

FAILED

Use `failure_category` to distinguish `BUILD_ERROR`, `STARTUP_ERROR`,
`TEST_FAILURE`, `ACCEPTANCE_FAILURE`, `AGENT_ERROR`, `TIMEOUT`, and
`SCOPE_BLOCKED` failures.

Recover abandoned `IN_PROGRESS` records as `FAILED` on the next run. Retry a
failed record in place, preserving previous evidence and attempt counts. Do not
automatically rebuild a completed architecture.

poc_description

A concise explanation of what was built.

Example:

A simple local fishing journal that allows a user to

create a fishing trip, add catches, and view saved

catches.

core_workflow

Example:

Create trip → Add catch → View history

technology

Example:

React Native + Expo

Or:

Python + Flask

Keep this flexible.

project_path

Store the location of the generated project.

Example:

/projects/fishing-journal-poc/

build_plan

Store the short build plan.

build_result

Store a concise summary.

Example:

POC successfully built.

Application starts successfully.

User can create a trip and add catches.

test_result

Example:

PASS

Core workflow successfully tested.

Or:

FAILED

Application starts but catches are not saved.

Autonomous Builder Interface

Phase 6 may use a coding agent, but the controller owns the build result. Give
the agent a single approved architecture payload containing:

```text
generated workspace path
poc_architecture_id and architecture snapshot
approved platform and technology choices
component plan and data model
build_plan
runtime_and_entrypoint
test_plan
workflow_acceptance_steps
completion_criteria
excluded features and scope deviations
allowed dependency commands and attempt budgets
```

The agent must implement only the approved architecture. It must return a
structured report containing changed files, commands run, installed packages,
run command, test command, observed results, limitations, and errors.

The controller independently runs the reported commands, captures their output,
and evaluates the Phase 5 acceptance contract. Do not accept an agent claim
that the POC works as build evidence.

The generated POC must not add user accounts, authentication, payments, cloud
infrastructure, analytics, complex architecture, or features outside the
approved scope.

Running the Application

Eventually:

python build_poc.py

Each run should:

1. Synchronize the Phase 5 handoff.
2. Select one eligible completed `READY_TO_BUILD` architecture.
3. Create its isolated build workspace.
4. Save the architecture and build-plan snapshots.
5. Send the approved architecture payload to the coding agent.
6. Run the documented entrypoint independently.
7. Execute the approved test plan and workflow acceptance steps.
8. Repair only within the approved scope and retry the same checks.
9. Save build commands, logs, artifacts, and acceptance evidence.
10. Mark the build complete only when every completion criterion passes.
11. Exit.

Provide a continuous runner consistent with the earlier phases:

```text
python run_continuous.py
```

It processes one architecture at a time, stops when no eligible architecture
remains, and reads its duration from:

```text
POC_BUILDER_CONTINUOUS_RUN_DURATION_SECONDS
```

Project Structure

```text
BuildPOC/
├── build_poc.py
├── run_continuous.py
├── handoff.py
├── database.py
├── builder_agent.py
├── verification.py
├── config.py
├── run_log.py
├── requirements.txt
├── README.md
├── tests/
│   └── test_phase6.py
├── logs/
├── architecture/
│   └── phase_6_app_pocbuilder_design.md
├── builds/
│   ├── <poc_architecture_id>/
│   └── <next_poc_architecture_id>/
└── app_builder.db
```

## Important Rules

1. Execute the Approved Architecture

Phase 5 determined the POC platform, components, data flow, test plan, and
completion criteria. Phase 6 implements and verifies that decision; it does
not replace it with a new product or architecture plan.

2. Protect the Build Boundary

The generated project must remain inside its assigned `BuildPOC/builds/`
workspace. The builder must not alter prior phases, source databases, or
unrelated files. It must not use elevated privileges or include secrets in code
or build evidence.

3. Verify Evidence, Not Claims

Record the commands, logs, automated-test output, and workflow acceptance
results that prove the POC works. A running process alone is not sufficient.

4. Avoid Infrastructure

Do not automatically build:

- APIs
- Cloud databases
- Authentication
- Docker
- Kubernetes
- Microservices

unless the approved architecture requires them. Local storage is acceptable
when it supports the required workflow.

5. Failure Is an Acceptable Result

When a POC cannot be built or accepted within its approved scope, save its
failure category, evidence, and remaining limitation. A failed build is useful
when it clearly records why the architecture could not be demonstrated.

6. Do Not Loop Forever

Use configured attempt limits. A build attempt generates or changes code and
runs the entrypoint. A repair attempt makes one targeted correction after a
failure, then reruns the same acceptance checks. Stop after the configured
budget, an unrecoverable dependency failure, or a blocked hypothesis.

Prefer:

INPUT

↓

CORE ACTION

↓

RESULT

Example:

Add Item

↓

Save Item

↓

View Item

Over a dozen disconnected features.

7. Do Not Rebuild the Existing App

Phase 4 defined the product and Phase 5 defined its approved POC architecture.

Phase 6 should build:

THE NEW PRODUCT CONCEPT

Not:

THE ORIGINAL APP

Keep Everything Simple

Do not build:

- A frontend for the pipeline itself
- User accounts
- Authentication
- Complex scheduling
- Microservices
- Kubernetes
- Production infrastructure
- CI/CD pipelines
- Detailed monitoring
- Complex autonomous agent hierarchies

The generated POC may have a UI because it is an application.

But the App Scout pipeline itself does not need a UI.

Definition of Done

Phase 6 is complete when:

python build_poc.py

can:

1. Copy and synchronize the Phase 5 database into `BuildPOC/app_builder.db`.
2. Select exactly one completed `READY_TO_BUILD` architecture.
3. Create one retryable build record linked to that architecture.
4. Create an isolated project workspace and save architecture snapshots.
5. Give a coding agent only the approved build and acceptance contract.
6. Independently run the documented entrypoint.
7. Execute the approved test plan and every workflow acceptance step.
8. Record commands, logs, artifacts, observed results, and acceptance evidence.
9. Repair only within the approved scope and rerun the same checks.
10. Stop at the configured build and repair limits.
11. Store a precise failure category and evidence when the POC cannot pass.
12. Mark a POC complete only after every Phase 5 completion criterion passes.
13. Make the generated project and its build evidence available for review.

Core Idea

The complete pipeline now looks like:

PHASE 1

SCOUT

"Is this app interesting?"

↓

PHASE 2

INVESTIGATOR

"Is there a real opportunity here?"

↓

PHASE 3

BUSINESS VALIDATOR

"Could this actually make money?"

↓

PHASE 4

PRODUCT DESIGNER

"What should we build instead?"

↓

PHASE 5

POC ARCHITECTURE

"How must the POC be built and verified?"

↓

PHASE 6

POC BUILDER

"Build and verify the approved POC."

↓

WORKING, TESTED POC
