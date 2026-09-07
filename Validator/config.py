"""Configuration owned by the Phase 3 business validator."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def get_database_path() -> Path:
    configured_path = Path(os.getenv("VALIDATOR_DATABASE_PATH", "app_scout.db"))
    return configured_path if configured_path.is_absolute() else BASE_DIR / configured_path


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
MAX_RESEARCH_PAGES = int(os.getenv("MAX_RESEARCH_PAGES", "20"))
