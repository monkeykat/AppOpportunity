# Scout App - To Do List

## Project Setup
- [x] Set up project structure and initialize repository
- [x] Create configuration system (config.py)
- [x] Create database schema and initialization (database.py)
- [x] Seed database with niches from niches.md file
- [x] Handle new niches from niches.md (add without duplicating)

## Core Components
- [x] Implement Ollama client (ollama_client.py)
- [x] Implement Google Play scraping with Playwright (google_play.py)

## Main Application Logic
- [x] Implement main application logic (scout.py)
- [x] Implement niche selection logic
- [x] Implement query generation using Ollama
- [x] Limit queries to 1-3 words maximum
- [x] Implement Google Play search and result extraction
- [x] Implement app evaluation with Ollama
- [x] Implement progress tracking (current_query_index, current_offset)
- [x] Implement niche exhaustion logic

## Recent Updates (2026-09-07)
- Read niches from niches.md file in project root
- Automatically add new niches from file (no duplicates)
- Fixed database path to be consistent
- Added bounded Google Play scrolling so saved offsets continue through loaded results
- Enforced MAX_RESULTS_PER_QUERY and same-run query exhaustion
- Fixed same-run niche exhaustion checks and missing app-name handling
- Added structured Google Play metadata extraction with DOM fallbacks

## Testing
- [x] Test the application end-to-end (requires Ollama to be running)
