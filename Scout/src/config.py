"""Configuration management for the Scout app."""

import os
from pathlib import Path


def get_base_dir() -> Path:
    """Get the base directory of the application."""
    # Get the directory containing this config.py file
    return Path(__file__).parent.resolve()


def get_workspace_dir() -> Path:
    """Get the workspace directory containing the shared .env file."""
    return get_base_dir().parent.parent


def load_workspace_env() -> None:
    """Load the shared workspace .env file when available."""
    env_path = get_workspace_dir() / '.env'
    try:
        from dotenv import load_dotenv
    except ImportError:
        if not env_path.exists():
            return
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))
    else:
        load_dotenv(env_path)


def load_config() -> dict:
    """Load configuration from environment variables and defaults."""
    load_workspace_env()
    
    return {
        'database_path': os.getenv('DATABASE_PATH', 'app_scout.db'),
        'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
        'ollama_model': os.getenv('SCOUT_OLLAMA_MODEL', 'qwen2.5-coder:7b'),
        'max_results_per_query': int(os.getenv('MAX_RESULTS_PER_QUERY', '100')),
        'apps_per_run': int(os.getenv('APPS_PER_RUN', '20')),
        'search_query_count': int(os.getenv('SEARCH_QUERY_COUNT', '10')),
        'opportunity_threshold': int(os.getenv('OPPORTUNITY_THRESHOLD', '7')),
        'request_delay_seconds': int(os.getenv('REQUEST_DELAY_SECONDS', '2')),
        'continuous_run_duration_seconds': int(
            os.getenv('CONTINUOUS_RUN_DURATION_SECONDS', '0')
        ),
    }


# Global config instance
config = load_config()
