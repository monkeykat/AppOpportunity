# **Phase 3 MVP: App Business Validator**

## **Goal**

Phase 1 finds potentially interesting apps.

**Phase 1 asks:**

Is this app interesting?

Phase 2 investigates those apps to determine whether they represent a real product opportunity.

**Phase 2 asks:**

Is there actually an opportunity here?

Phase 3 answers the next question:

**Could this realistically become a viable business?**

More specifically:

**Could we build a product that people would actually use and that has a realistic path to making money?**

Phase 3 should take the most promising opportunities from Phase 2 and evaluate:

- What product we would actually build
- What the smallest useful MVP would be
- Who would use it
- What problem it solves
- Why someone would choose it
- Why an existing user might switch
- How it would be meaningfully different
- Whether people appear willing to pay
- Whether advertising could realistically support the product
- How similar products make money
- Whether the apparent market is large enough
- How difficult it may be to acquire customers
- Rough revenue potential
- Major business risks
- Important assumptions that must be true for the business to work

There is no frontend.

The output is stored in SQLite.

The goal is **not** to create a detailed business plan.

The goal is to answer:

**Is this opportunity worth seriously considering as a business?**

# **Core Concept**

```
PHASE 1

Find interesting apps
```

↓

```
PHASE 2

Determine whether there is a real product opportunity
```

↓

```
PHASE 3

Determine whether there is a viable business
```

↓

```
FINAL VERDICT

"Could this realistically make money?"
```

# **Important Phase Separation Rule**

Phase 1 and Phase 2 are complete.

**Do not modify them.**

Phase 3 must operate independently.

Before Phase 3 begins:

1. Copy the completed Phase 2 project into the Phase 3 folder.
2. Copy the completed Phase 2 database into the Phase 3 folder as `app_validator.db`.
3. Phase 3 operates only on its own copy.
4. Do not modify the Phase 1 database.
5. Do not modify the Phase 2 database.
6. Do not overwrite any files in the completed Phase 1 or Phase 2 projects.

The database flow should be:

```
PHASE 1

app_validator.db
```

↓

`COPY`

↓

```
PHASE 2

app_validator.db
```

↓

`COPY`

↓

```
PHASE 3

app_validator.db
```

Phase 3 adds its new table only to its own database copy.

# **Technology**

Use:

- Python
- SQLite
- Ollama
- Playwright

Use public web research where necessary.

Keep dependencies minimal.

Do not build a complex multi-agent system.

# **Database**

Continue using:

`app_validator.db`

Phase 3 receives a copy of the completed Phase 2 database.

Do not redesign or modify the existing tables.

Phase 3 should add one new table:

`business_validations`

# **5. business_validations**

Stores the business viability analysis.

Fields:

```
id

app_id

status

product_concept

target_customer

value_proposition

differentiation

monetization

willingness_to_pay

apparent_market_size

customer_acquisition_difficulty

revenue_potential

business_risks

key_assumptions

viability_score

recommendation

summary

validated_at
```

One app should only have one business validation.

## **status**

Possible values:

```
PENDING

IN_PROGRESS

COMPLETE

FAILED
```

# **Field Descriptions**

## **product_concept**

A concise description of the product we would actually build.

This should focus on the:

**Smallest useful MVP**

Do not design an entire application.

Determine:

- What problem are we solving?
- What would our version do?
- What complaints would we fix?
- What features are necessary?
- What features can be ignored?
- What makes the product better?

Example:

```
A simple fishing journal focused on quickly recording

catches, locations, photos, and conditions.

The MVP would focus on fast data entry and useful

personal statistics.

It would avoid unnecessary social features, complicated

maps, and expensive subscriptions.
```

## **target_customer**

Who would realistically use the product?

Consider:

- Hobbyists
- Professionals
- Small businesses
- Enthusiasts
- Students
- Specialized workers
- Other clearly defined audiences

Determine:

- Who has the problem?
- How frequently do they have the problem?
- How important is it?
- Would they actively look for a solution?

Example:

```
Recreational fishermen who regularly track catches and

want to maintain personal fishing records.
```

## **value_proposition**

Why would someone use this product?

Consider:

- Simpler
- Faster
- Cheaper
- Better workflow
- No advertising
- Better mobile experience
- Missing feature
- More specialized
- More accurate

The value proposition should answer:

What useful value does this product provide?

Example:

```
A faster and simpler fishing journal focused on personal

catch tracking rather than trying to be an all-in-one

fishing platform.
```

## **differentiation**

What would make this product meaningfully different?

The product should not simply be:

```
Existing App

+

Different Logo
```

Consider:

- Better experience
- Simpler workflow
- Better niche focus
- Different pricing
- Missing features
- Different target audience

Also answer:

Why would an existing user switch?

And:

Why would a new user choose this product instead?

Example:

```
The product would focus specifically on rapid catch

logging and personal history.

Users could complete the primary workflow in fewer steps

than competing apps.

The product would avoid advertising and unnecessary

social features.
```

The differentiation does not need to be revolutionary.

It simply needs to provide a credible answer to:

Why would someone choose this?

# **Selecting an Opportunity**

Phase 3 should only process opportunities that completed Phase 2.

Phase 3 should process:

```
STRONG_OPPORTUNITY

PROMISING
```

Do not automatically process:

```
INVESTIGATE_FURTHER

PASS
```

Prioritize:

`STRONG_OPPORTUNITY`

↓

`PROMISING`

Within those categories, prioritize the highest Phase 2 score.

Do not validate the same app twice.

Example logic:

```
SELECT

opportunities.*,

investigations.*

FROM opportunities

JOIN investigations

ON opportunities.app_id = investigations.app_id

LEFT JOIN business_validations

ON opportunities.app_id = business_validations.app_id

WHERE

investigations.status = 'COMPLETE'

AND investigations.recommendation IN

('STRONG_OPPORTUNITY', 'PROMISING')

AND business_validations.id IS NULL

ORDER BY

CASE investigations.recommendation

WHEN 'STRONG_OPPORTUNITY' THEN 0

WHEN 'PROMISING' THEN 1

END,

investigations.final_score DESC

LIMIT 1;
```

The exact SQL can be simplified if necessary.

The important behavior is:

`STRONG OPPORTUNITY`

↓

`Highest Score`

↓

`PROMISING`

↓

`Highest Score`

# **Main Loop**

The application should perform the following process:

`SELECT PROMISING PHASE 2 OPPORTUNITY`

↓

`READ PHASE 2 RESULTS`

↓

`DEFINE SMALLEST USEFUL MVP`

↓

`DEFINE TARGET CUSTOMER`

↓

`DEFINE VALUE PROPOSITION`

↓

`DEFINE DIFFERENTIATION`

↓

`DETERMINE WHY USERS WOULD SWITCH`

↓

`RESEARCH MONETIZATION`

↓

`LOOK FOR EVIDENCE PEOPLE WILL PAY`

↓

```
IF PEOPLE WILL NOT PAY:

CAN ADVERTISING SUPPORT THE PRODUCT?
```

↓

`ESTIMATE APPARENT MARKET SIZE`

↓

`ESTIMATE CUSTOMER ACQUISITION DIFFICULTY`

↓

`ESTIMATE REVENUE POTENTIAL`

↓

`IDENTIFY BUSINESS RISKS`

↓

`IDENTIFY KEY ASSUMPTIONS`

↓

```
ASK:

"WHAT HAS TO BE TRUE FOR THIS TO WORK?"
```

↓

```
ASK:

"WHY MIGHT THIS FAIL?"
```

↓

`OLLAMA GENERATES FINAL VERDICT`

↓

`SAVE RESULTS`

↓

`EXIT`

Each run should process **one app**.

This keeps the MVP simple.

# **Step 1: Read Phase 2 Results**

Phase 3 should begin by reading the existing Phase 2 investigation.

Use:

- App information
- App analysis
- User analysis
- Complaint analysis
- Competitor analysis
- Alternative analysis
- Build difficulty
- Proprietary dependency
- Market potential
- Competition level
- Final score
- Recommendation

If Phase 2 added raw research tables, Phase 3 may use those records as additional evidence.

Do not unnecessarily repeat Phase 2 research.

Phase 3 should build upon it.

The relationship should be:

```
PHASE 1

"What apps are interesting?"
```

↓

```
PHASE 2

"Is there a product opportunity?"
```

↓

```
PHASE 3

"Could this product opportunity become a business?"
```

# **Step 2: Define the Product**

Determine:

**What would we actually build?**

Do not design an entire application.

Define the:

**Smallest useful MVP**

Determine:

- What problem are we solving?
- What would our version do?
- Which complaints would we fix?
- What features are necessary?
- What features can be ignored?
- What would make the product better?

The goal is not:

`BUILD EVERYTHING`

The goal is:

```
WHAT IS THE SMALLEST PRODUCT

THAT COULD TEST WHETHER PEOPLE WANT THIS?
```

Create:

`product_concept`

Example:

```
A simplified fishing journal focused on quickly recording

catches, locations, photos, and conditions.

The MVP would provide fast data entry, personal history,

and useful statistics.

Social networking, tournaments, advanced maps, and other

complex features would not be included initially.
```

Keep this concise.

# **Step 3: Define the Target Customer**

Determine:

Who would realistically use this product?

Use the Phase 2 research.

Consider:

- Hobbyists
- Professionals
- Small businesses
- Enthusiasts
- Students
- Specialized workers

Determine:

- Who has the problem?
- How frequently do they experience it?
- How important is it?
- Would they actively search for a solution?

Create:

`target_customer`

Example:

```
Recreational fishermen who fish regularly and want to

maintain personal records of catches, locations, and

conditions.
```

# **Step 4: Define the Value Proposition**

Answer:

Why would someone use this?

Use:

- Phase 2 complaints
- Competitor weaknesses
- Alternative workarounds
- User frustrations

Consider:

- Simpler
- Cheaper
- Faster
- No advertisements
- Better workflow
- Better mobile experience
- Missing feature
- More specialized

Create:

`value_proposition`

Example:

```
A faster and simpler fishing journal focused specifically

on personal catch tracking rather than trying to be an

all-in-one fishing platform.
```

# **Step 5: Determine Differentiation**

This is important.

The app should not simply be:

```
EXISTING APP

+

DIFFERENT LOGO
```

Determine:

What would make this product meaningfully different?

Consider:

- Better experience
- Simpler workflow
- Better niche focus
- Different pricing
- Missing features
- Different target audience

Also explicitly consider:

**Existing Customer**

`Why would someone currently using a competitor switch?`

**New Customer**

`Why would someone choose this product first?`

Create:

`differentiation`

The differentiation does not need to be revolutionary.

It simply needs to answer:

Why would someone choose this product?

# **Step 6: Research Monetization**

Determine how similar products make money.

Look for evidence of:

- Paid apps
- Subscriptions
- Freemium models
- Advertising
- One-time purchases
- Premium features
- Business licenses
- Affiliate revenue
- Sponsorships

Do not build a complicated financial model.

The goal is simply:

Is there a realistic path to monetization?

Create:

`monetization`

The analysis should consider both:

```
MODEL A

USER PAYS

Subscription

One-time purchase

Premium features

Freemium
```

And:

```
MODEL B

USER DOES NOT PAY

Large audience
```

↓

```
Advertising

Affiliate revenue

Sponsorship
```

Example:

```
Primary model:

Freemium subscription.

Free:

Basic catch logging.

Premium:

Advanced statistics

Unlimited history

Export

Cloud backup

Secondary possibility:

Advertising for free users.

Evidence:

Several competing products offer subscriptions or premium

features, suggesting at least some users are willing to

pay for additional functionality.
```

Possible pricing examples are hypotheses.

They are not financial forecasts.

# **Step 7: Look for Evidence of Willingness to Pay**

This is one of the most important parts of Phase 3.

Do not assume:

```
People use an app

Therefore

People will pay for an app.
```

Look for evidence.

Examples:

- Existing paid competitors
- Existing subscriptions
- Premium versions
- Users discussing prices
- Users complaining about prices
- Users purchasing alternatives
- Businesses paying for similar software
- Premium features that appear common in the market

Also consider:

- Is the problem important enough to pay for?
- Is the product used frequently?
- Does the product save meaningful time?
- Does the product create meaningful value?

Create:

`willingness_to_pay`

Use a score:

```
1

Very little evidence users would pay.

5

Some evidence.

10

Strong evidence users pay for solutions.
```

This score should reflect **evidence**, not optimism.

# **Step 8: Evaluate Advertising-Supported Potential**

Not every successful product requires paying customers.

If willingness to pay appears low, determine:

Could this product potentially attract enough users to support advertising or other audience-based monetization?

Consider:

- Apparent audience size
- Frequency of use
- Session frequency
- Existing ad-supported competitors
- Existing free products
- Affiliate opportunities
- Sponsorship opportunities

Do not add a separate database field for this.

Include the findings in:

`monetization`

and consider them during:

`revenue_potential`

Do not assume:

```
FREE APP

=

ADVERTISING BUSINESS
```

A product needs enough users and usage to make advertising meaningful.

# **Step 9: Estimate Apparent Market Size**

Do not attempt to calculate a precise TAM.

This is an MVP.

Do not create a complex market model.

Instead, estimate the:

`APPARENT MARKET SIZE`

Consider:

- Install counts
- Number of competitors
- Review counts
- Community size
- Search activity
- Relevant online communities
- Popularity of the hobby or profession

Return:

```
VERY_SMALL

SMALL

MODERATE

LARGE

VERY_LARGE
```

Store:

`apparent_market_size`

Important:

This is **not a TAM calculation**.

It is a rough categorization based on publicly observable signals.

The question is:

Are there apparently enough potential users to care?

# **Step 10: Estimate Customer Acquisition Difficulty**

This is an important business consideration.

A product can have:

```
HIGH DEMAND

+

GOOD PRODUCT

+

WILLING CUSTOMERS
```

And still fail.

Because:

`CUSTOMERS CANNOT FIND IT.`

Estimate:

`customer_acquisition_difficulty`

Use a score:

```
1

Customers appear relatively easy to reach.

5

Moderate difficulty.

10

Customers appear extremely difficult or expensive to reach.
```

Consider:

- Search intent
- Google search opportunities
- App Store discovery
- Relevant communities
- Reddit
- Facebook groups
- Industry forums
- YouTube
- Influencers
- SEO
- Partnerships
- Advertising competition

The goal is not to calculate CAC.

The goal is simply to ask:

Is there a plausible way to get this product in front of customers?

Example:

```
Fishing enthusiasts participate in large online

communities, watch relevant YouTube channels, and search

for fishing-related tools.

Customer acquisition appears moderately difficult rather

than extremely difficult.
```

# **Step 11: Estimate Revenue Potential**

Make a rough estimate.

Do not pretend this is a financial forecast.

Consider:

- Apparent market size
- Willingness to pay
- Advertising potential
- Possible pricing
- Competition
- Customer acquisition difficulty
- Business model

Return:

```
LOW

MODERATE

HIGH
```

Store:

`revenue_potential`

Definitions:

**LOW**

```
Could potentially generate some revenue, but there is

limited evidence that it could support a meaningful

business.
```

**MODERATE**

```
Could plausibly support a small or independent software

business.
```

**HIGH**

```
Evidence suggests the opportunity could potentially

support a substantial business.
```

Do not create precise revenue estimates.

Do not create:

```
Year 1:

$82,472
```

That level of precision would be mostly imaginary math wearing a tiny business suit. 📊

Keep it rough.

# **Step 12: Identify Business Risks**

Identify the biggest reasons the idea might fail.

Examples:

- Market too small
- Users unwilling to pay
- Insufficient advertising audience
- Strong competitors
- Expensive customer acquisition
- Difficult differentiation
- Network effects
- High ongoing costs
- Dependency on third-party APIs
- Seasonal demand
- Legal or regulatory issues

Create:

`business_risks`

Keep this concise.

Focus on the biggest risks.

The goal is not to list every imaginable danger.

Focus on:

What are the three to five biggest ways this could fail?

# **Step 13: Identify Key Assumptions**

Every business idea contains assumptions.

Phase 3 should identify them.

Ask:

What has to be true for this business to work?

Example:

```
This business depends on several assumptions:

1. A meaningful number of users actively want a simpler

alternative.

2. At least some users are willing to pay for premium

features.

3. Users can be reached through app store search,

communities, and relevant online content.

4. The product can provide a noticeably better workflow

than existing competitors.
```

The final analysis should distinguish between:

`ASSUMPTIONS WITH EVIDENCE`

and:

`ASSUMPTIONS THAT REMAIN UNPROVEN`

Do not add a separate database field.

Include this analysis in:

`business_risks`

and the final:

`summary`

# **Step 14: Ask Why the Business Might Fail**

The system should actively challenge the opportunity.

Ask:

`Why wouldn't this work?`

Consider:

- Why would users stay with existing apps?
- Why wouldn't users switch?
- Why wouldn't they pay?
- Why couldn't advertising support it?
- Why would customer acquisition be difficult?
- Why might the market be too small?
- Why might competitors already solve the problem adequately?

Do not allow Ollama to become an automated optimism machine.

Strong opportunities should survive skepticism.

# **Step 15: Final Business Evaluation**

After collecting the information, send the Phase 2 research and Phase 3 analysis to Ollama.

The question is:

**Is this worth building as a business?**

Use a prompt similar to:

```
You are evaluating whether a potential software product

could plausibly become a viable business.

The goal is not to determine whether the product can

be built.

The goal is to determine whether building it could

realistically create enough value to support a business.

Consider:

- The problem being solved

- The target customer

- Evidence of demand

- Evidence users actively seek solutions

- Existing user complaints

- The proposed MVP

- Why users would switch

- Product differentiation

- Existing competitors

- Monetization options

- Evidence users are willing to pay

- Whether advertising could realistically support the product

- Apparent market size

- Customer acquisition difficulty

- Revenue potential

- Major business risks

- Important assumptions that remain unproven

Do not assume:

- A popular app is automatically a good business.

- A large market means a new competitor can succeed.

- Users will pay simply because they use free apps.

- Low ratings automatically create an opportunity.

- A better product will automatically attract customers.

Be skeptical.

Actively look for reasons the business might fail.

Identify assumptions that must be true for the business

to work.

Strong opportunities should be rare.

PRODUCT CONCEPT:

{product_concept}

TARGET CUSTOMER:

{target_customer}

VALUE PROPOSITION:

{value_proposition}

DIFFERENTIATION:

{differentiation}

MONETIZATION:

{monetization}

WILLINGNESS TO PAY:

{willingness_to_pay}

APPARENT MARKET SIZE:

{apparent_market_size}

CUSTOMER ACQUISITION DIFFICULTY:

{customer_acquisition_difficulty}

REVENUE POTENTIAL:

{revenue_potential}

BUSINESS RISKS:

{business_risks}

PHASE 2 INVESTIGATION:

{phase_2_results}

Return only valid JSON:

{

"viability_score": 1-10,

"recommendation":

"PASS | POSSIBLE | PROMISING | BUILD_CANDIDATE",

"summary":

"Concise explanation of the business opportunity,

major risks, and important assumptions."

}
```

# **Final Recommendations**

Use the following categories.

## **Score 1–3**

`PASS`

The app may be interesting, but there is little evidence it could become a viable business.

Examples:

- Very small market
- Little willingness to pay
- No realistic advertising opportunity
- Difficult customer acquisition
- No meaningful differentiation

## **Score 4–5**

`POSSIBLE`

There may be something here.

However, significant questions remain unanswered.

Examples:

- Demand appears real
- But willingness to pay is unclear

or:

- The market appears large
- But differentiation is weak

or:

- The product could be useful
- But customer acquisition may be difficult

## **Score 6–7**

`PROMISING`

There is reasonable evidence of:

```
Demand

+

Clear customer

+

Useful product

+

Meaningful differentiation

+

Possible monetization

+

Plausible customer acquisition
```

Worth considering.

## **Score 8–10**

`BUILD_CANDIDATE`

Strong evidence that:

```
People have the problem

+

People actively seek solutions

+

The product can be meaningfully differentiated

+

There is evidence of willingness to pay

OR

A realistic audience-based monetization model

+

The apparent market is large enough

+

Customers appear reachable
```

These should be rare.

The system should be skeptical.

# **Running the Application**

Run:

`python validate_business.py`

Each run should:

1. Select one promising Phase 2 opportunity.
2. Ensure it has not already been validated.
3. Read the existing Phase 2 investigation.
4. Read additional Phase 2 evidence if available.
5. Define the smallest useful MVP.
6. Define the target customer.
7. Identify the value proposition.
8. Identify meaningful differentiation.
9. Determine why users might switch.
10. Research monetization.
11. Look for evidence users would pay.
12. Consider advertising-supported monetization.
13. Estimate the apparent market size.
14. Estimate customer acquisition difficulty.
15. Estimate rough revenue potential.
16. Identify the biggest business risks.
17. Identify important assumptions.
18. Ask Ollama for a skeptical final evaluation.
19. Assign a business viability score.
20. Save the results.
21. Exit.

# **Project Structure**

Phase 3 should be its own independent project folder.

Example:

`phase3-validator/`

├── `validate_business.py`

│

├── `database.py`

├── `business_research.py`

├── `ollama_client.py`

├── `config.py`

│

├── `TODO.md`

│

└── `app_validator.db`

The database should be a copy of the completed Phase 2 database.

# **File Responsibilities**

## **validate_business.py**

Responsible for:

`SELECT OPPORTUNITY`

↓

`READ PHASE 2 RESULTS`

↓

`RUN BUSINESS VALIDATION`

↓

`CALL OLLAMA`

↓

`SAVE RESULTS`

It should contain the main application flow.

Keep it simple.

## **database.py**

Responsible for:

- Connecting to SQLite
- Creating the `business_validations` table
- Selecting unvalidated opportunities
- Creating validation records
- Updating validation status
- Saving validation results

Do not redesign the existing database.

Do not modify the existing Phase 1 or Phase 2 tables.

## **business_research.py**

Responsible for:

```
Define Product Concept

Define Target Customer

Identify Value Proposition

Identify Differentiation

Research Monetization

Research Willingness To Pay

Evaluate Advertising Potential

Estimate Apparent Market Size

Estimate Customer Acquisition Difficulty

Estimate Revenue Potential

Identify Business Risks
```

Keep the research logic simple and modular.

Do not create a complex agent system.

## **ollama_client.py**

Responsible for:

- Calling Ollama
- Generating structured analysis
- Parsing JSON responses
- Handling invalid responses reasonably

Use the local Ollama model.

## **config.py**

Centralize configuration.

Example:

```
OLLAMA_MODEL=...

OPPORTUNITY_THRESHOLD=...

REQUEST_DELAY=...

MAX_SEARCH_RESULTS=...

VALIDATION_RETRY_COUNT=...
```

Only include configuration that is actually needed.

Do not create configuration for hypothetical future features.

# **TODO.md**

Create a TODO list first.

Use:

`TODO.md`

in the Phase 3 workspace.

The implementation should:

1. Create the TODO list before beginning development.
2. Track major implementation tasks.
3. Mark tasks complete when finished.
4. Add useful implementation notes where necessary.

Example:

```
# Phase 3 TODO

- [ ] Set up Phase 3 project structure

- [ ] Copy Phase 2 database

- [ ] Add business_validations table

- [ ] Implement opportunity selection

- [ ] Implement Phase 2 data retrieval

- [ ] Implement product concept analysis

- [ ] Implement monetization research

- [ ] Implement willingness-to-pay research

- [ ] Implement market analysis

- [ ] Implement customer acquisition analysis

- [ ] Implement final Ollama evaluation

- [ ] Test complete validation run
```

# **Important Rules**

## **1. Validate an App Only Once**

Once a validation is:

`COMPLETE`

do not automatically validate it again.

One app should have only one:

`business_validations`

record.

# **2. Do Not Modify Earlier Phases**

Phase 3 must not modify:

```
Phase 1 files

Phase 2 files

Phase 1 database

Phase 2 database
```

Phase 3 works with:

```
ITS OWN FILES

+

ITS OWN COPY OF THE DATABASE
```

# **3. Use Evidence, Not Assumptions**

The system should look for evidence that:

- People use solutions
- People have the problem
- People are dissatisfied
- People actively seek alternatives
- People pay for alternatives
- Businesses pay for similar solutions
- Advertising-supported competitors exist
- The audience is large enough to support monetization

Do not confuse:

`POSSIBILITY`

with:

`EVIDENCE`

# **4. Be Skeptical**

The goal is not to convince ourselves every app is a business opportunity.

The system should actively look for reasons an idea might fail.

Ask:

```
Why wouldn't this work?

Why would users stay with existing apps?

Why wouldn't users switch?

Why wouldn't they pay?

Why couldn't advertising support it?

Why would customer acquisition be difficult?

Why couldn't this make enough money?
```

# **5. Define the Smallest Useful MVP**

Do not design a complete application.

The question is:

What is the smallest useful product we could build to test this opportunity?

Avoid feature explosions.

Do not turn:

`Fishing Journal`

into:

```
Fishing Journal

+

Social Network

+

Marketplace

+

AI Assistant

+

Weather Platform

+

Boat Integration

+

Tournament System
```

Keep the product concept focused.

# **6. Willingness to Pay Is Not Guaranteed**

Do not assume:

```
People use an app

=

People will pay for an app.
```

Look for evidence.

Examples:

- Existing subscriptions
- Paid competitors
- Premium features
- People discussing purchases
- Businesses paying for similar tools

# **7. Advertising Is Not Automatically a Business Model**

Do not assume:

`Users won't pay`

↓

`We'll use ads`

Advertising requires:

- A sufficiently large audience
- Meaningful usage
- A realistic path to acquiring users

Evaluate this realistically.

# **8. Customer Acquisition Matters**

A great product can still fail if nobody finds it.

Consider:

- Search
- Communities
- App Store discovery
- SEO
- Influencers
- Partnerships
- Advertising

Do not build a CAC model.

Simply estimate:

How difficult might it be to reach customers?

# **9. Do Not Build a Complicated Financial Model**

Do not create:

- Detailed revenue forecasts
- Multi-year projections
- Complex TAM calculations
- Customer acquisition models
- Investor presentations
- Spreadsheets full of speculative numbers

This is still an MVP.

The goal is:

Is there enough evidence to justify further work?

# **10. Keep Everything Simple**

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
- Complex financial models
- Advanced analytics pipelines

This should remain a small Python application.

# **Definition of Done**

Phase 3 is complete when:

`python validate_business.py`

will:

1. Select a promising Phase 2 opportunity.
2. Ensure it has not already been validated.
3. Read the existing Phase 2 investigation.
4. Determine the smallest useful MVP.
5. Identify the target customer.
6. Identify the customer problem.
7. Identify why someone would use the product.
8. Identify meaningful differentiation.
9. Determine why users might switch.
10. Research possible monetization.
11. Look for evidence users would pay.
12. Consider advertising-supported monetization.
13. Estimate the apparent market size.
14. Estimate customer acquisition difficulty.
15. Estimate rough revenue potential.
16. Identify the biggest business risks.
17. Identify important assumptions.
18. Actively consider why the business might fail.
19. Use Ollama to produce a skeptical final assessment.
20. Assign a business viability score.
21. Produce a recommendation.
22. Save everything to SQLite.
23. Exit.

# **Core Idea**

Phase 1 asks:

**"Is this app interesting?"**

Phase 2 asks:

**"Is there a real product opportunity here?"**

Phase 3 asks:

**"Could this actually become a business?"**

The pipeline now looks like:

`THOUSANDS OF APPS`

↓

═══════════════════════

```
PHASE 1

SCOUT
```

═══════════════════════

`"Is this interesting?"`

↓

`POTENTIALLY INTERESTING APPS`

↓

═══════════════════════

```
PHASE 2

INVESTIGATOR
```

═══════════════════════

`"Is there a real opportunity?"`

↓

`PROMISING PRODUCT OPPORTUNITIES`

↓

═══════════════════════

```
PHASE 3

BUSINESS VALIDATOR
```

═══════════════════════

```
"Could this realistically

make money?"
```

↓

`BUILD CANDIDATES`

The output of Phase 3 should be a **much smaller list of opportunities that appear capable of becoming real businesses**.

For example:

```
PHASE 1

10,000 Apps Scanned
```

↓

```
100 Potential Opportunities

PHASE 2

100 Investigated
```

↓

`30 Interesting`

↓

```
10 Promising

PHASE 3

10 Business Validations
```

↓

`5 Possible`

↓

`3 Promising`

↓

`1–2 Build Candidates`

# **Final Philosophy**

Phase 3 should not try to prove that every opportunity is good.

Its job is to act as a skeptical filter.

`INTERESTING APP`

↓

`REAL PRODUCT OPPORTUNITY`

↓

`VIABLE BUSINESS?`

↓

`NO`

↓

```
PASS

OR

YES
```

↓

`BUILD CANDIDATE`

A **BUILD_CANDIDATE** should mean:

There is enough evidence of a real problem, a reachable customer, meaningful differentiation, plausible monetization, and a sufficiently large apparent market to justify spending additional time designing and testing the product.

It does **not** mean:

Guaranteed successful business.

That uncertainty is the point. Phase 3's job is simply to reduce the pile of shiny possibilities until only the ones worth serious effort remain.
