"""Configuration for the Phase 2 investigator."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def get_database_path() -> Path:
    """Return the Phase 2 database path, resolved relative to this folder."""
    configured_path = Path(os.getenv("INVESTIGATOR_DATABASE_PATH", "app_investigator.db"))
    return configured_path if configured_path.is_absolute() else BASE_DIR / configured_path


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")