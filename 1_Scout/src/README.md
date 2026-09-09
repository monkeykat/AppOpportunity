# Scout App

A Python application that uses a local Ollama model to autonomously search Google Play for potentially interesting niche apps.

## Prerequisites

- Python 3.9+
- Ollama (local AI model server)
- Playwright browsers

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd src
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Ensure Ollama is running:
```bash
ollama serve
```

## Usage

Run the application:
```bash
python scout.py
```

To keep Scout running and repeat the one-iteration loop automatically:
```bash
python run_continuous.py
```

The continuous runner waits 30 seconds between iterations by default. Set a
different delay with `--interval`:
```bash
python run_continuous.py --interval 60
```

Set `SCOUT_CONTINUOUS_RUN_DURATION_SECONDS` in the shared workspace `.env` file to
limit continuous mode. The current iteration is always allowed to finish;
`0` means run until interrupted:
```env
SCOUT_CONTINUOUS_RUN_DURATION_SECONDS=3600
```

Press `Ctrl+C` to stop continuous mode.

Each single or continuous iteration writes a timestamped log to `1_Scout/logs/`.
The log includes the normal console output, warnings, errors, and exception
tracebacks while the same output remains visible in the terminal.

## Project Structure

```
src/
├── scout.py          # Main application entry point
├── database.py       # Database schema and operations
├── config.py         # Configuration management
├── ollama_client.py  # Ollama API client
├── google_play.py    # Google Play scraping with Playwright
├── run_continuous.py  # Optional continuous runner
├── run_log.py         # Per-run console and file logging
└── requirements.txt  # Python dependencies
```

## Database

The application uses SQLite with three tables:
- `niches` - Tracks explored niches and search progress
- `apps` - Tracks all discovered apps
- `app_evaluations` - Stores every valid Ollama score and reason
- `opportunities` - Stores the evaluated apps meeting `OPPORTUNITY_THRESHOLD`

## Configuration

The shared workspace `.env` file supports `SCOUT_OLLAMA_MODEL` for the Scout
model and `OLLAMA_URL` for the Ollama server. `APPS_PER_RUN` limits the number
of search results processed in one run, regardless of how many become
opportunities.

Set `MAX_APP_RATING`, `MIN_INSTALL_COUNT`, and `MAX_INSTALL_COUNT` in the
shared workspace `.env` file to enable automatic opportunities. An app is
added directly to `opportunities` when its rating is strictly below
`MAX_APP_RATING` and its install count is inclusively between the two install
limits. Leave any of the three values blank to disable this automatic rule for
incomplete configuration. Automatically matched apps do not need to pass
through the Ollama opportunity score.

## License

MIT
