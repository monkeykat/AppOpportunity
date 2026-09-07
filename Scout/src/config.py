"""Configuration management for the Scout app."""

import os
from pathlib import Path


def get_base_dir() -> Path:
    """Get the base directory of the application."""
    # Get the directory containing this config.py file
    return Path(__file__).parent.resolve()


def load_config() -> dict:
    """Load configuration from environment variables and defaults."""
    from dotenv import load_dotenv
    
    # Load .env file if it exists
    env_path = get_base_dir() / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    return {
        'database_path': os.getenv('DATABASE_PATH', 'app_scout.db'),
        'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
        'ollama_model': os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b'),
        'max_results_per_query': int(os.getenv('MAX_RESULTS_PER_QUERY', '100')),
        'apps_per_run': int(os.getenv('APPS_PER_RUN', '20')),
        'search_query_count': int(os.getenv('SEARCH_QUERY_COUNT', '10')),
        'opportunity_threshold': int(os.getenv('OPPORTUNITY_THRESHOLD', '7')),
        'request_delay_seconds': int(os.getenv('REQUEST_DELAY_SECONDS', '2')),
    }


# Global config instance
config = load_config()
