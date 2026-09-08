"""Configuration owned by Phase 4 Product Definition."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent


def load_workspace_env() -> None:
    env_path = WORKSPACE_DIR / ".env"
    try:
        from dotenv import load_dotenv
    except ImportError:
        if not env_path.exists():
            return
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    else:
        load_dotenv(env_path)


load_workspace_env()


def _path_from_env(name: str, default: Path) -> Path:
    configured = os.getenv(name)
    if not configured:
        return default
    path = Path(configured)
    return path if path.is_absolute() else WORKSPACE_DIR / configured


def get_database_path() -> Path:
    return _path_from_env("PRODUCT_DEFINITION_DATABASE_PATH", BASE_DIR / "app_designer.db")


def get_validator_database_path() -> Path:
    configured = os.getenv("VALIDATOR_DATABASE_PATH")
    if not configured:
        return WORKSPACE_DIR / "Validator" / "app_validator.db"
    path = Path(configured)
    return path if path.is_absolute() else WORKSPACE_DIR / "Validator" / path


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("DEFINITION_OLLAMA_MODEL", "qwen3.8:27b")
DEFINITION_OLLAMA_TIMEOUT_SECONDS = int(
    os.getenv("DEFINITION_OLLAMA_TIMEOUT_SECONDS", "300")
)
PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS = int(
    os.getenv("PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS", "0")
)

__all__ = [
    "BASE_DIR",
    "DEFINITION_OLLAMA_TIMEOUT_SECONDS",
    "OLLAMA_MODEL",
    "OLLAMA_URL",
    "PRODUCT_DEFINITION_CONTINUOUS_RUN_DURATION_SECONDS",
    "get_database_path",
    "get_validator_database_path",
]
