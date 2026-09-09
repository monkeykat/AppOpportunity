# Phase 4: Product Definition

**Goal**

Phase 1 finds interesting apps. (Complete)

Phase 2 determines whether there is a real opportunity. (Complete)

Phase 3 determines whether the opportunity could potentially become a viable business. (Complete)

Phase 4 asks:

**What should we build instead?**

The goal is to take a promising existing app and design a **better, focused alternative**.

Not a clone.

Not a feature-for-feature replacement.

The system should determine:

- What problem the new product should solve

- Which users it should focus on

- What the MVP should do

- What should be improved

- What should be removed

- What features are actually necessary

- How the product should differentiate itself

- What the smallest useful version looks like

There is **no frontend**.

The output is stored in SQLite.

Phase 4 owns the product decision. It defines the smallest product worth
validating, while Phase 5 defines the architecture and exact completion
criteria for the proof of concept. Phase 5 must not independently redefine the
core problem, target user, or validation hypothesis.

**Core Concept**

EXISTING APP

↓

WHAT DOES IT DO?

↓

WHAT DO USERS LIKE?

↓

WHAT DO USERS HATE?

↓

WHAT ARE THEY MISSING?

↓

WHAT ARE COMPETITORS DOING?

↓

WHAT SHOULD WE DO DIFFERENTLY?

↓

REMOVE UNNECESSARY FEATURES

↓

DESIGN THE MVP

↓

PRODUCT SPECIFICATION

**Technology**

Use:

- Python

- SQLite

- Ollama

Use the research already collected in Phase 2 and Phase 3.

Additional public research may be performed only to resolve a product-definition
question that Phase 2 and Phase 3 evidence cannot answer. Limit it to the
smallest practical number of sources and store a bounded URL, title, and
evidence summary only when it changes a product decision.

Keep dependencies minimal.

Do not build a complicated multi-agent system.

**Database**

Copy the completed Phase 3 database from:

`3_Validator/app_validator.db`

into the Phase 4-owned database:

`4_Definition/app_designer.db`

Phase 4 must read and write only its private copy. It must never modify the
Validator database. On later runs, synchronize new and changed Phase 3 data
while preserving existing product designs.

The handoff includes inherited `opportunities`, `investigations`, and
`business_validations` records. `business_validations` controls eligibility;
Phase 2 research is supporting evidence. The Phase 4 prompt should use only
the bounded Phase 2 complaints, competitor observations, and conclusions plus
the Phase 3 target customer, value proposition, business risks, key
assumptions, viability score, and recommendation.

Each product design must record `source_validation_id`, `source_validated_at`,
and a bounded `source_validation_snapshot`. If its controlling Phase 3
validation changes after a completed design is created, mark the product design
`STALE` and require it to be redesigned before it can be handed to Phase 5.

Do not redesign the existing tables.

Phase 4 should add **one new table**:

product_designs

**6.****product_designs**

Stores the proposed product design.

Fields:

id

app_id

status

product_name

product_summary

target_user

core_problem

product_strategy

differentiation

design_rationale

rejected_alternatives

inherited_constraints

validation_hypothesis

core_user_workflow

minimum_validation_scope

evidence_to_support_or_reject

must_have_features

nice_to_have_features

excluded_features

mvp_scope

technical_considerations

technical_risks

success_criteria

design_score

recommendation

created_at

designed_at

error

source_validation_id

source_validated_at

source_validation_snapshot

One app should have only one product design.

`app_id` must be `NOT NULL UNIQUE` and reference the copied Phase 3
opportunity. `source_validation_id` must reference the copied
`business_validations` record. Feature collections and multi-value strategies
are stored as JSON arrays. `design_score` must be an integer from 1 to 10.

**status**

Possible values:

PENDING

IN_PROGRESS

COMPLETE

FAILED

STALE

**Selecting an Opportunity**

Phase 4 should only process apps that passed Phase 3.

Prioritize:

BUILD_CANDIDATE

PROMISING

Do not process:

PASS

POSSIBLE

Select only `business_validations` rows with `status = COMPLETE` and
recommendation `BUILD_CANDIDATE` or `PROMISING`. Prioritize
`BUILD_CANDIDATE`, then its highest `viability_score`, then `PROMISING`, then
its highest `viability_score`, with a deterministic `app_id` tie-breaker.

Select an app when it has no product design or its existing design has
`status = FAILED` or `STALE`. Reuse the existing design record for retry or
redesign rather than creating a second record.

Do not design the same product twice.

**Main Loop**

SELECT BUILD CANDIDATE

↓

READ PHASE 2 RESEARCH

↓

READ PHASE 3 BUSINESS VALIDATION

↓

IDENTIFY THE REAL PROBLEM

↓

IDENTIFY THE BEST TARGET USER

↓

IDENTIFY WHAT EXISTING APPS GET WRONG

↓

DECIDE WHAT TO DO DIFFERENTLY

↓

DEFINE THE VALIDATION HYPOTHESIS
↓
DEFINE ONE CORE USER WORKFLOW
↓
DEFINE THE MINIMUM VALIDATION SCOPE

↓

REMOVE EVERYTHING UNNECESSARY

↓

DEFINE MVP

↓

CREATE PRODUCT DESIGN

↓

SAVE

↓

EXIT

Each run should design **one product**.

**Step 1: Understand the Existing Opportunity**

Read the results from:

Phase 2

and:

Phase 3

Understand:

What does the existing app do?

What problem does it solve?

Who uses it?

What complaints do users have?

What features do users like?

What competitors exist?

What alternatives exist?

Use Phase 3 conclusions about demand, willingness to pay, market size, and
business risk as constraints. Do not repeat Phase 3 business validation.

Do not repeat all previous research.

Use the existing research to make design decisions.

**Step 2: Identify the Core Problem**

This is one of the most important steps.

Determine:

**What problem should our product actually solve?**

Do not simply say:

"We should build a better version of App X."

Instead, identify the underlying problem.

For example:

Existing App:

Fishing Tracker

The real problem might be:

"I want to quickly remember and analyze my fishing trips."

That is more useful than:

"We need to build a fishing app."

Store:

core_problem

Keep it concise.

**Step 3: Choose the Target User**

Do not try to build for everyone.

Determine the most promising user.

Examples:

Casual fishermen

Serious hobbyists

Professional guides

Competitive anglers

These may all use fishing software.

But they may want very different things.

Select the user group that appears:

Most likely to have the problem

Most dissatisfied with existing solutions

Most likely to use a better solution

Best fit for the core problem and proposed workflow

Most likely to adopt a focused improvement

Consistent with the Phase 3 business and market constraints

Store:

target_user

**Step 4: Determine Product Strategy**

Determine the basic strategy for the product.

Possible strategies include:

SIMPLER

CHEAPER

MORE_SPECIALIZED

BETTER_WORKFLOW

BETTER_USER_EXPERIENCE

DIFFERENT_AUDIENCE

SOLVE_MISSING_PROBLEM

The product may use more than one strategy.

Example:

SIMPLER

+

MORE_SPECIALIZED

Example:

Existing fishing apps attempt to provide:

Maps

Weather

Social networking

Species databases

Fishing reports

Community features

Gear stores

The new product might instead focus on:

Quickly logging fishing trips

Tracking catches

Photos

Personal statistics

The strategy is:

SIMPLER

MORE_SPECIALIZED

Store:

product_strategy

**Step 5: Define Differentiation**

Answer:

**Why would someone choose this product?**

Use the research from Phase 2.

Look for:

Repeated complaints

Missing features

Bad workflows

Overly complicated competitors

Expensive pricing

Neglected user groups

Create a concise statement.

Example:

A fast and simple fishing journal designed specifically

for individual anglers who want to record and analyze

their own fishing history without advertisements,

social networking, or unnecessary features.

Store:

differentiation

The differentiation should be meaningful.

Do not use:

"Better UI"

by itself.

That is not a product strategy.

**Step 6: Define the Validation Target**

Phase 4 must explicitly describe what the smallest product needs to prove.

Store:

`validation_hypothesis`

A falsifiable statement connecting the target user's problem to the proposed
product.

Store:

`core_user_workflow`

The single most important workflow the target user must complete.

Store:

`minimum_validation_scope`

The smallest product capable of testing the hypothesis. This is narrower than
the full MVP and should name the one to three capabilities required by the
core workflow.

Store:

`evidence_to_support_or_reject`

The observable product evidence that would support or reject the hypothesis.

The fields have distinct purposes:

```text
core_user_workflow
The single ordered user journey being proven.

minimum_validation_scope
The one to three capabilities required for that journey.

must_have_features
The concrete behaviors that implement those capabilities.

mvp_scope
A concise user-facing summary of the minimum validation scope. It must not add
features outside the workflow or minimum validation scope.
```

Every must-have feature must map to a core workflow step. A feature may not
appear in both `must_have_features` and `excluded_features`.

**Step 7: Define Must-Have Features**

Determine the smallest set of features required to solve the core problem.

Ask:

**If we removed this feature, would the product still solve the main problem?**

If yes:

It probably does not belong in the MVP.

Store the features as JSON.

Example:

[

"Create fishing trip",

"Record catch",

"Add species",

"Add location",

"Attach photo",

"View personal catch history"

]

Store:

must_have_features

Keep this list small.

A validation product should generally have:

1–3 required capabilities for the primary workflow

Not:

3–10 loosely related features or a complete replacement app

**Step 8: Define Nice-to-Have Features**

These are useful features that should **not be required for the first MVP**.

Examples:

Cloud synchronization

Advanced statistics

Social features

Sharing

AI recommendations

Apple Watch integration

Store as JSON:

nice_to_have_features

These are intentionally excluded from the first build.

**Step 9: Define Excluded Features**

This is important.

Explicitly identify things the product should **not do**.

Existing apps often become bloated because they try to solve every possible problem.

Example:

[

"Social network",

"Public fishing maps",

"Gear marketplace",

"Advertising",

"Community forums",

"Professional tournament tracking"

]

Store:

excluded_features

This helps prevent the autonomous development system from building a monster.

**Step 10: Define the MVP Scope**

Create a concise description of the smallest useful product.

Answer:

What can a user do?

What problem does it solve?

What is intentionally missing?

Example:

The MVP allows an individual angler to create fishing

trips and record catches with basic information,

locations, and photos.

The user can view their personal catch history.

The MVP does not include social features, public maps,

weather forecasting, community content, or advanced

analytics.

Store:

mvp_scope

**Step 11: Identify Technical Considerations**

This should remain high-level.

Do not design the entire architecture.

Identify important technical requirements.

Examples:

Mobile application

Local database

GPS access

Camera access

Cloud synchronization optional

Public weather API optional

Also identify possible concerns:

Third-party APIs

Proprietary data

Ongoing costs

Specialized hardware

Complex backend requirements

Store:

technical_considerations

Also store `technical_risks` as JSON objects containing:

```text
risk
severity: LOW | MEDIUM | HIGH
why_it_matters
possible_mitigation
blocks_validation: true | false
```

An unresolved `HIGH` risk where `blocks_validation` is true prevents a design
from receiving `READY_FOR_POC`.

The goal is simply to avoid designing something that Phase 4 assumes is easy but is actually technically problematic.

**Step 12: Define Success Criteria**

Determine what success would look like for the MVP.

Not business success.

**Product success.**

Examples:

A new user can understand the app without instructions.

A user can perform the primary task in under one minute.

The app solves the primary problem without unnecessary

features.

The core workflow works reliably.

Store:

success_criteria

Keep this simple.

**Step 13: Generate the Product Summary**

After the design is complete, ask Ollama to summarize the proposed product.

The goal is to create a concise product description.

Use a prompt similar to:

You are designing a new software product based on

research into an existing application and its market.

The goal is NOT to clone the existing application.

The goal is to determine what product should be built

instead.

Focus on:

- The core user problem

- The best target user

- The strongest product strategy

- Meaningful differentiation

- The smallest useful feature set

Avoid feature creep.

Do not add features simply because competitors have them.

Prefer a focused product that solves one problem well.

PRODUCT RESEARCH:

{phase_2_results}

BUSINESS VALIDATION:

{phase_3_results}

CORE PROBLEM:

{core_problem}

TARGET USER:

{target_user}

PRODUCT STRATEGY:

{product_strategy}

DIFFERENTIATION:

{differentiation}

DESIGN RATIONALE:

{design_rationale}

REJECTED ALTERNATIVES:

{rejected_alternatives}

INHERITED CONSTRAINTS:

{inherited_constraints}

VALIDATION HYPOTHESIS:

{validation_hypothesis}

CORE USER WORKFLOW:

{core_user_workflow}

MINIMUM VALIDATION SCOPE:

{minimum_validation_scope}

EVIDENCE TO SUPPORT OR REJECT:

{evidence_to_support_or_reject}

MUST-HAVE FEATURES:

{must_have_features}

NICE-TO-HAVE FEATURES:

{nice_to_have_features}

EXCLUDED FEATURES:

{excluded_features}

MVP SCOPE:

{mvp_scope}

Return only valid JSON:

{

"product_name": "Working product name",

"product_summary": "Concise description of the product.",

"core_problem": "The focused problem being solved.",

"target_user": "The narrow target user.",

"product_strategy": ["BETTER_WORKFLOW"],

"differentiation": "Why this product should be chosen.",

"design_rationale": "Why these product decisions follow from the research.",

"rejected_alternatives": ["Alternative approach intentionally rejected."],

"inherited_constraints": ["Relevant constraints inherited from Phase 3."],

"validation_hypothesis": "A falsifiable product hypothesis.",

"core_user_workflow": "The primary workflow.",

"minimum_validation_scope": "The smallest scope that tests the hypothesis.",

"evidence_to_support_or_reject": [
	{
		"claim": "Product decision supported by research.",
		"source_phase": 2,
		"source_field": "complaint_patterns",
		"evidence_summary": "Bounded supporting evidence."
	}
],

"must_have_features": ["Required capability"],

"nice_to_have_features": ["Deferred capability"],

"excluded_features": ["Explicitly excluded capability"],

"mvp_scope": "The smallest useful product description.",

"technical_considerations": ["High-level constraint or dependency."],

"technical_risks": [
	{
		"risk": "Potential implementation risk.",
		"severity": "LOW",
		"why_it_matters": "Impact on the validation workflow.",
		"possible_mitigation": "Simple mitigation.",
		"blocks_validation": false
	}
],

"success_criteria": ["Product success criterion."],

"design_score": 1-10,

"recommendation": "PASS | DESIGN_REVIEW | READY_FOR_POC"

}

`product_name` is a temporary working label. It is optional and must not affect
the product score, recommendation, validation hypothesis, or Phase 5 handoff.

**Product Design Score**

The design score represents:

**How strong and focused is this proposed product?**

It does **not** represent business potential.

Phase 3 already evaluated business potential.

Before a design can be marked `COMPLETE`, the implementation must verify:

- Required text fields are non-empty.
- `product_strategy` contains one or more permitted strategy values.
- `core_user_workflow` contains at least two ordered user actions.
- `minimum_validation_scope` has one to three capabilities.
- Every must-have feature maps to the workflow and minimum validation scope.
- Must-have and excluded features do not overlap.
- Success criteria and evidence are observable and testable.
- The design rationale contains bounded evidence references.
- No unresolved blocking technical risk remains for `READY_FOR_POC`.

**Score 1–3**

PASS

The product concept is unclear or does not meaningfully improve on existing solutions.

**Score 4–5**

DESIGN_REVIEW

There may be an opportunity, but the proposed product needs refinement.

Possible problems:

Unclear target user

Weak differentiation

Too many features

No clear advantage

**Score 6–7**

READY_FOR_POC

The product has:

Clear problem

Clear target user

Meaningful differentiation

Focused MVP

Worth building as a proof of concept.

**Score 8–10**

READY_FOR_POC

The product design is especially strong.

It should still remain rare.

The system should be skeptical.

The implementation must reject any score/recommendation mismatch:

- `1–3` requires `PASS`.
- `4–5` requires `DESIGN_REVIEW`.
- `6–10` requires `READY_FOR_POC`.

`READY_FOR_POC` is the only recommendation eligible for Phase 5. A product is
eligible only when its design status is `COMPLETE` and all required fields pass
structural validation. The saved `source_validation_id` and
`source_validated_at` must still match the controlling Phase 3 validation; a
`STALE` design is not eligible.

**Phase 4 to Phase 5 Handoff**

Phase 5 consumes the completed product design from `4_Definition/app_designer.db`.
The following fields are authoritative and must not be re-decided downstream:

- `core_problem`
- `target_user`
- `validation_hypothesis`
- `core_user_workflow`
- `minimum_validation_scope`
- `must_have_features`
- `excluded_features`
- `success_criteria`

Phase 5 may choose implementation details and document technical deviations,
but it must preserve the validation target and core workflow. A design is not
ready for handoff if those fields are missing, empty, or inconsistent with the
feature lists.

**Running the Application**

Run:

python design_product.py

Each run should:

1. Select one validated business opportunity.

2. Read the Phase 2 investigation.

3. Read the Phase 3 business validation.

4. Identify the core problem.

5. Select the best target user.

6. Identify what existing products get wrong.

7. Define the product strategy.

8. Define meaningful differentiation.

9. Define the validation hypothesis.

10. Define one core user workflow.

11. Define the minimum validation scope.

12. Define evidence that would support or reject the hypothesis.

13. Define must-have features.

14. Define nice-to-have features.

15. Define excluded features.

16. Define the MVP scope.

17. Identify high-level technical considerations.

18. Define product success criteria.

19. Generate a final product summary.

20. Validate and save the complete product design atomically.

21. Exit.

Provide a continuous runner consistent with the earlier phases:

```text
python run_continuous.py
```

It processes one product design at a time, stops when no eligible Phase 3
validation remains, and reads its duration from:

```text
PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS
```

Use timestamped logs in `4_Definition/logs/` and print meaningful progress before
handoff, selection, research assembly, Ollama calls, validation, saving,
retry, staleness recovery, and queue completion.

**Project Structure**

```text
4_Definition/
├── design_product.py
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
│   └── test_phase4.py
├── logs/
├── architecture/
│   └── phase_4_app_definition_design.md
└── app_designer.db
```

Do not significantly complicate the project.

**Important Rules**

**1. Do Not Clone the Existing App**

The goal is not:

Existing App

↓

Copy Features

↓

New App

The goal is:

Existing App

↓

Understand Users

↓

Understand Problems

↓

Identify Opportunity

↓

Build Better Solution

**2. Solve the Core Problem**

Do not build features just because they exist elsewhere.

Every feature should help solve:

core_problem

**3. Prefer Focus**

A smaller product is often better.

Prefer:

One problem

One target user

One clear workflow

Over:

Everything for everyone

**4. Explicitly Prevent Feature Creep**

The system must actively identify features that should **not** be built.

Use:

excluded_features

This is just as important as:

must_have_features

**5. Keep Technical Design High-Level**

Do not create:

- Complete database schemas

- API specifications

- Detailed UI designs

- Full software architecture

- Complete technical requirements

That comes later.

Phase 4 answers:

**What should we build?**

Not:

**Exactly how should we build it?**

**6. Keep Everything Simple**

Do not build:

- A frontend

- FastAPI

- Docker

- User accounts

- Authentication

- Multiple AI agents

- Complex scheduling

- Vector databases

- RAG

- Microservices

- Detailed architecture diagrams

**Definition of Done**

Phase 4 is complete when:

python design_product.py

will:

1. Select a viable Phase 3 business opportunity.

2. Read the existing research.

3. Identify the core problem.

4. Identify the best target user.

5. Identify what existing solutions get wrong.

6. Determine a product strategy.

7. Create meaningful differentiation.

8. Define the validation hypothesis.

9. Define one core user workflow.

10. Define the minimum validation scope.

11. Define evidence that would support or reject the hypothesis.

12. Define a small set of must-have features consistent with the workflow.

13. Define nice-to-have and explicitly excluded features.

14. Define the smallest useful MVP.

15. Identify high-level technical considerations.

16. Define product success criteria.

17. Generate a concise product description.

18. Score the product design and validate its recommendation band.

19. Confirm the design is coherent, testable, and ready for the Phase 5
handoff when marked `READY_FOR_POC`.

20. Save the complete product design atomically to SQLite.

**Core Idea**

The pipeline now becomes:

PHASE 1: SCOUT

"Is this app interesting?"

↓

PHASE 2: INVESTIGATOR

"Is there a real opportunity here?"

↓

PHASE 3: BUSINESS VALIDATOR

"Could this actually make money?"

↓

PHASE 4: PRODUCT DESIGNER

"What should we build instead?"

↓

PRODUCT DESIGN

The important transformation happens here:

EXISTING APP

"Fishing Tracker Pro"

↓

PHASE 1

Interesting niche

↓

PHASE 2

Users repeatedly complain that it is complicated,

expensive, and overloaded with features.

↓

PHASE 3

There appears to be a viable audience willing to pay

for a simpler tool.

↓

PHASE 4

DO NOT BUILD:

"Fishing Tracker Pro Clone"

BUILD:

"A simple personal fishing journal for serious

recreational anglers."
