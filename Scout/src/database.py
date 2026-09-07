"""Database schema and initialization for the Scout app."""

import sqlite3
from typing import Optional, List, Tuple
from pathlib import Path
import json
from config import config, get_base_dir


def get_db_path() -> Path:
    """Get the path to the database file."""
    base_dir = get_base_dir()
    db_path = config['database_path']
    
    # If path is relative, join with base directory
    if not Path(db_path).is_absolute():
        return base_dir / db_path
    return Path(db_path)


def init_database() -> None:
    """Initialize the database with required tables."""
    db_path = get_db_path()
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create niches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS niches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            queries TEXT,  -- JSON array of search queries
            current_query_index INTEGER DEFAULT 0,
            current_offset INTEGER DEFAULT 0,
            last_searched DATETIME
        )
    ''')
    
    # Create apps table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            developer TEXT,
            url TEXT,
            niche_id INTEGER,
            description TEXT,
            category TEXT,
            rating REAL,
            review_count INTEGER,
            install_count TEXT,
            last_updated TEXT,
            price TEXT,
            contains_ads BOOLEAN,
            offers_in_app_purchases BOOLEAN,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id)
        )
    ''')
    
    # Create opportunities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL UNIQUE,
            app_name TEXT,
            score INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (app_id) REFERENCES apps(id)
        )
    ''')

    opportunity_columns = {
        row[1] for row in cursor.execute('PRAGMA table_info(opportunities)')
    }
    if 'app_name' not in opportunity_columns:
        cursor.execute('ALTER TABLE opportunities ADD COLUMN app_name TEXT')
    cursor.execute('''
        UPDATE opportunities
        SET app_name = (
            SELECT apps.name FROM apps WHERE apps.id = opportunities.app_id
        )
        WHERE app_name IS NULL
    ''')
    
    conn.commit()
    conn.close()


def get_niches_from_file() -> List[str]:
    """Read niches from the niches.md file.
    
    Returns:
        List of niche names
    """
    base_dir = get_base_dir()
    # niches.md is in the parent directory of src/
    niches_file = base_dir.parent / 'niches.md'
    
    if not niches_file.exists():
        return []
    
    with open(niches_file, 'r') as f:
        niches = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith('#')
        ]
    
    return niches


def seed_niches() -> None:
    """Seed the database with niches from niches.md file.
    
    Reads niches from niches.md and adds any new ones to the database.
    Does not modify existing niches.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Get niches from file
    file_niches = get_niches_from_file()
    
    if not file_niches:
        conn.close()
        return
    
    # Get existing niches from database
    cursor.execute('SELECT name FROM niches')
    existing_niches = {row[0] for row in cursor.fetchall()}
    
    # Add new niches from file
    added_count = 0
    for niche in file_niches:
        if niche not in existing_niches:
            cursor.execute(
                'INSERT INTO niches (name, status) VALUES (?, ?)',
                (niche, 'ACTIVE')
            )
            added_count += 1
    
    conn.commit()
    conn.close()
    
    if added_count > 0:
        print(f"Added {added_count} new niches to database.")


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    return sqlite3.connect(get_db_path())


if __name__ == '__main__':
    init_database()
    seed_niches()
    print('Database initialized successfully.')
