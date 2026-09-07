# Phase 1 MVP: Google Play App Scout

## Goal

Build a simple Python application that uses a local Ollama model to autonomously search Google Play for potentially interesting niche apps.

The application should:

1. Pick a niche to explore.
2. Search Google Play for apps in that niche.
3. Progress through search results instead of repeatedly examining the same top apps.
4. Save discovered apps to a local SQLite database.
5. Remember which apps have already been seen.
6. Remember which searches/niches have already been explored.
7. Use a local Ollama model to decide whether an app looks potentially interesting by feeding it the app's available basic information and metadata.
8. Save only potentially interesting apps as opportunities.
9. Run repeatedly without constantly doing the same work.

There is **no frontend**. The SQLite database is the output.

## Technology

Use:

- Python
- SQLite
- Ollama
- Playwright

Keep dependencies minimal.

## Database

Use one SQLite database:

**app_scout.db**

Only use three tables.

### 1. `niches`

Tracks areas being explored.

**Fields:**

- `id`
- `name`
- `status`
- `queries`
- `current_query_index`
- `current_offset`
- `last_searched`

**Field descriptions**

**`queries`**

Stores the Ollama-generated search queries for the niche as JSON.

Example:

```json
[
  "fishing",
  "fishing log",
  "fish tracker",
  "angler journal",
  "fishing forecast"
]
```

Queries are generated once and reused until exhausted.

**`current_query_index`**

Tracks which query is currently being searched.

Example:

```
0 = fishing
1 = fishing log
2 = fish tracker
3 = angler journal
4 = fishing forecast

current_query_index = 2
```

The next search will continue with:

```
fish tracker
```

**`current_offset`**

Tracks how far through the results the application has progressed.

Example:

```
current_offset = 40

Google Play may use dynamically loaded or infinite-scroll search results.

current_offset represents the number of results that have already been
processed for the current search query.

Do not assume Google Play provides a URL parameter that allows the
application to jump directly to a specific offset.

Use Playwright to load search results and continue beyond the previously
processed results. The exact implementation should depend on the current
behavior of the Google Play website.
```

Meaning the application has already processed approximately the first 40 results for the current query. The next run should continue searching for additional results instead of starting over.

**`last_searched`**

Stores the last time the niche was processed.

Example:

```
2026-09-06 14:30:00
```

This helps prevent the system from repeatedly selecting the same niche.

Example:

```
1 | Fishing Apps | ACTIVE
2 | Amateur Astronomy | ACTIVE
3 | Beekeeping | EXHAUSTED
```

Status values:

```
ACTIVE
EXHAUSTED
```

Seed the database with approximately 20 interesting niches. The user will add additional niches, which will need to be searched once added.

Examples:

```
Fishing
Amateur Astronomy
Beekeeping
Gardening
Bird Watching
Woodworking
RV Travel
Ham Radio
Home Inspection
Inventory Management
Collecting
Board Games
Hiking
Camping
Boating
Automotive
Music Practice
Photography
Aviation
Field Work
```

### 2. `apps`

Tracks every app the system has encountered.

**Fields:**

- `id`
- `package_name`
- `name`
- `developer`
- `url`
- `niche_id`
- `description`
- `category`
- `rating`
- `review_count`
- `install_count`
- `last_updated`
- `price`
- `contains_ads`
- `offers_in_app_purchases`
- `first_seen`

`package_name` must be unique. If an app already exists in the database, do not process or evaluate it again. The app should still remain in the database even if Ollama determines it is not an opportunity.

### 3. `opportunities`

Contains apps Ollama thinks are potentially interesting.

**Fields:**

- `id`
- `app_id`
- `score`
- `reason`
- `created_at`

An app should only have one opportunity record.

## Main Loop

Use the `TODO.md` file in the workspace to keep track of what has and has not been done. Update it as necessary, keep notes, and mark each task as completed when finished.

The application should run the following loop:

```
SELECT NICHE
    ↓
GET OR CREATE SEARCH QUERIES
    ↓
SELECT CURRENT QUERY
    ↓
SEARCH GOOGLE PLAY
    ↓
GET NEW RESULTS
    ↓
SKIP APPS ALREADY IN DATABASE
    ↓
SAVE NEW APPS AND METADATA
    ↓
ASK OLLAMA TO EVALUATE EACH NEW APP
    ↓
IF INTERESTING → SAVE AS OPPORTUNITY
    ↓
UPDATE SEARCH PROGRESS
    ↓
EXIT
```

## Selecting a Niche

Choose a niche that is not exhausted. Prefer niches that have been explored the least recently. Do not constantly return to the same niche.

Use:

```sql
SELECT *
FROM niches
WHERE status = 'ACTIVE'
ORDER BY
    CASE WHEN last_searched IS NULL THEN 0 ELSE 1 END,
    last_searched ASC
LIMIT 1;
```

After processing the niche, update:

- `last_searched`

Niches can continue to be added by the user. New niches should automatically be included in future searches. Keep this simple.

## Searching Google Play

Use Playwright to search the public Google Play website.

Example search:

```
https://play.google.com/store/search?q=fishing&c=apps
```

Extract apps from the search results. For each new app, collect as much of the following publicly available information as possible:

- Name
- Developer
- Package Name
- URL
- Description
- Category
- Rating
- Review Count
- Install Count
- Last Updated
- Price
- Contains Ads
- Offers In-App Purchases

Some information may not be available directly from the search results. The application may:

1. Find the app through Google Play search.
2. Open the individual app page.
3. Extract the available metadata.

If package name is unavailable, derive or extract it from the app URL when possible.

Use conservative request rates. Do not bypass CAPTCHAs, access controls, or anti-bot protections.

## Avoid Repeatedly Searching the Same Apps

This is important. The program should not always examine only the first results.

For each niche, generate several related search terms. Example:

```
Fishing

fishing
fishing log
fish tracker
angler journal
fishing forecast
```

Search queries should be generated once and stored in:

- `niches.queries`

The application tracks:

- `current_query_index`
- `current_offset`

Example:

```
Fishing

Current Query:
fish tracker

Current Offset:
40
```

The next time the application runs, it should continue beyond the first 40 results. It should not restart from the beginning.

## Query Generation

Use Ollama to generate a user-defined number of search terms for the niche.

Example prompt:

```
Generate [USER DEFINED NUMBER] different Google Play Store search queries for finding Android apps related to this niche:

FISHING

Return only a JSON array of search queries.

The queries should explore different types of apps within the niche.

Avoid repeating the exact same concept.
```

Example result:

```json
[
  "fishing log",
  "fish tracker",
  "angler journal",
  "fishing forecast",
  "catch tracker"
]
```

Do not generate new queries every time. Generate the queries once. Store them in:

- `niches.queries`

The application should work through the queries sequentially. When one query is exhausted:

```
current_query_index += 1
current_offset = 0
```

The application then moves to the next query.

## Exhausting a Search Query

A search query is exhausted when:

1. It reaches the configured result limit.
2. Google Play no longer returns additional results.
3. Or the application repeatedly finds no new apps.

When a query is exhausted:

```
current_query_index += 1
current_offset = 0
```

The application then moves to the next query.

## Exhausting a Niche

A niche becomes exhausted when:

1. All generated search queries have been searched.
2. Each query has reached the configured result limit.
3. Or searches stop finding meaningful numbers of new apps.

Then:

```
status = EXHAUSTED
```

The system moves on.

Example:

```
Fishing → EXHAUSTED
Next:
Amateur Astronomy
```

## App Evaluation

For every **new app**, ask Ollama whether it looks potentially interesting as a possible software opportunity. Use only the information collected from Google Play. Do not perform additional research.

Use a prompt similar to:

```
Does this Android app look potentially interesting as a possible software opportunity?

We are looking for:

- Niche apps
- Apps solving a specific problem
- Apps with a clearly defined audience
- Apps that might potentially be improved upon
- Apps with low or mediocre user ratings relative to their apparent demand
- Apps that show evidence of meaningful demand
- Apps that may be outdated or neglected

Do not deeply research the app.

Use only the information provided.

Consider:

- How specific the niche is
- Whether the app solves a clear problem
- Whether there appears to be meaningful demand
- The app's rating
- The number of reviews
- The install count
- When the app was last updated
- Whether the app appears neglected or outdated
- Whether the app appears to have potential for improvement

Return only valid JSON in this format:

{
    "score": 1-10,
    "reason": "Short explanation"
}

App Information:

Name: {name}

Developer: {developer}

Category: {category}

Description:

{description}

Rating: {rating}

Review Count: {review_count}

Install Count: {install_count}

Last Updated: {last_updated}

Price: {price}

Contains Ads: {contains_ads}

Offers In-App Purchases: {offers_in_app_purchases}
```

Expected response:

```json
{
  "score": 8,
  "reason": "Specific niche audience with evidence of demand. The low rating and old update date suggest potential for a better alternative."
}
```

## Opportunity Threshold

If:

```
score >= 7
```

Save the app to the `opportunities` table. Otherwise, do nothing. The app is still saved in the `apps` table so it is never evaluated again.

## Running the Application

The application can be run manually:

```
python scout.py
```

Each run should:

1. Select one active niche.
2. Generate search queries if they do not already exist.
3. Select the current search query.
4. Search Google Play.
5. Continue from the saved search offset.
6. Process a limited number of results.
7. Ignore previously discovered apps.
8. Collect available metadata for new apps.
9. Save new apps to SQLite.
10. Evaluate new apps with Ollama.
11. Save promising apps as opportunities.
12. Update search progress.
13. Update `last_searched`.
14. Exit.

This makes the POC easy to test. Later, it can run continuously:

```
RUN → WAIT → RUN → WAIT
```

Continuous autonomous operation is **not required for Phase 1**.

## Configuration

Use a simple configuration file or environment variables:

```
OLLAMA_MODEL=...
MAX_RESULTS_PER_QUERY=100
APPS_PER_RUN=20
SEARCH_QUERY_COUNT=10
OPPORTUNITY_THRESHOLD=7
```

All configuration should be centralized.

## Important Rules

The application must:

### 1. Never evaluate the same app twice

Check:

- `package_name`

If the app already exists:

```
SKIP
```

### 2. Never restart searches from the beginning

Track:

- `current_query_index`
- `current_offset`

### 3. Eventually move on from a search query

When a query is exhausted:

```
current_query_index += 1
current_offset = 0
```

### 4. Eventually move on from a niche

When all queries have been completed:

```
status = EXHAUSTED
```

### 5. Use available metadata when evaluating an app

Ollama should receive all available collected metadata. At minimum:

- Name
- Developer
- Description
- Category
- Rating
- Review Count
- Install Count
- Last Updated
- Price
- Contains Ads
- Offers In-App Purchases

### 6. Keep everything local

Use:

- Ollama
- SQLite
- Python
- Playwright

### 7. Keep it simple

Do **not** build:

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
- Advanced analytics
- A complicated scoring system

## Project Structure

```
app-scout/
    ├── scout.py
    ├── database.py
    ├── google_play.py
    ├── ollama_client.py
    ├── config.py
    └── app_scout.db
```

Keep the code small and understandable.

## Definition of Done

The POC is complete when I can run:

```
python scout.py
```

And it will:

1. Pick an active niche.
2. Generate search queries if necessary.
3. Search Google Play.
4. Continue beyond previously searched results.
5. Discover apps.
6. Ignore apps already discovered.
7. Collect available Google Play metadata.
8. Save new apps to SQLite.
9. Ask local Ollama whether new apps are interesting.
10. Use available metadata when evaluating the app.
11. Save interesting apps as opportunities.
12. Remember search progress.
13. Eventually exhaust a search query.
14. Eventually exhaust a niche.
15. Move to another niche.

I should then be able to open:

```
app_scout.db
```

And run:

```sql
SELECT
    apps.name,
    apps.developer,
    apps.rating,
    apps.review_count,
    apps.install_count,
    apps.last_updated,
    opportunities.score,
    opportunities.reason
FROM opportunities
JOIN apps ON opportunities.app_id = apps.id
ORDER BY opportunities.score DESC;
```

## Core Concept

```
NICHE → GENERATE QUERIES → SELECT QUERY → SEARCH GOOGLE PLAY → CONTINUE FROM SAVED OFFSET → NEW APP? → YES → COLLECT METADATA → SAVE APP → ASK OLLAMA → INTERESTING? → YES → SAVE OPPORTUNITY → UPDATE PROGRESS
```
