"""Configuration for the Phase 2 investigator."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent


def load_workspace_env() -> None:
    """Load the shared workspace .env file when available."""
    env_path = WORKSPACE_DIR / ".env"
    try:
        from dotenv import load_dotenv
    except ImportError:
        if not env_path.exists():
            return
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    else:
        load_dotenv(env_path)


load_workspace_env()


def get_database_path() -> Path:
    """Return the Phase 2 database path, resolved relative to this folder."""
    configured_path = Path(os.getenv("INVESTIGATOR_DATABASE_PATH", "app_investigator.db"))
    return configured_path if configured_path.is_absolute() else BASE_DIR / configured_path


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("INVESTIGATOR_OLLAMA_MODEL", "qwen2.5-coder:7b")
INVESTIGATOR_CONTINUOUS_RUN_DURATION_SECONDS = int(
    os.getenv("INVESTIGATOR_CONTINUOUS_RUN_DURATION_SECONDS", "0")
)

MAX_REVIEWS_PER_APP = int(os.getenv("MAX_REVIEWS_PER_APP", "30"))
MAX_COMPETITORS = int(os.getenv("MAX_COMPETITORS", "10"))
MAX_SEARCH_RESULTS_PER_TOPIC = int(os.getenv("MAX_SEARCH_RESULTS_PER_TOPIC", "10"))
MAX_RESEARCH_PAGES = int(os.getenv("MAX_RESEARCH_PAGES", "30"))