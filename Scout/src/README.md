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

Press `Ctrl+C` to stop continuous mode.

## Project Structure

```
src/
├── scout.py          # Main application entry point
├── database.py       # Database schema and operations
├── config.py         # Configuration management
├── ollama_client.py  # Ollama API client
├── google_play.py    # Google Play scraping with Playwright
├── run_continuous.py  # Optional continuous runner
└── requirements.txt  # Python dependencies
```

## Database

The application uses SQLite with three tables:
- `niches` - Tracks explored niches and search progress
- `apps` - Tracks all discovered apps
- `opportunities` - Stores apps marked as interesting

## Configuration

See `.env.example` for available configuration options.

## License

MIT
