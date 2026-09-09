"""Configuration owned by the Phase 3 business validator."""

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
    configured_path = Path(os.getenv("VALIDATOR_DATABASE_PATH", "app_validator.db"))
    return configured_path if configured_path.is_absolute() else BASE_DIR / configured_path


def get_investigator_database_path() -> Path:
    configured_value = os.getenv("INVESTIGATOR_DATABASE_PATH")
    if configured_value:
        configured_path = Path(configured_value)
        return (
            configured_path
            if configured_path.is_absolute()
            else WORKSPACE_DIR / "2_Investigator" / configured_path
        )
    return WORKSPACE_DIR / "2_Investigator" / "app_investigator.db"


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("VALIDATOR_OLLAMA_MODEL", "qwen3.5:4b")
VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS = int(
    os.getenv("VALIDATOR_CONTINUOUS_RUN_DURATION_SECONDS", "0")
)
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
MAX_RESEARCH_PAGES = int(os.getenv("MAX_RESEARCH_PAGES", "20"))
