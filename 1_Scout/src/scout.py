"""Main application logic for the Scout app."""

import time
import json
import traceback
from typing import List, Dict, Optional
from pathlib import Path

from database import get_db_path, get_connection, init_database, seed_niches
from config import config
from ollama_client import OllamaClient
from google_play import GooglePlayScraper
from run_log import run_log


class ScoutApp:
    """Main application class for Scout."""
    
    def __init__(self):
        self.db_path = get_db_path()
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        self.ollama = OllamaClient()
        # Warm up Ollama to avoid cold start delays
        print("Warming up Ollama model...")
        if self.ollama.warmup():
            print("Ollama warmup complete.")
        else:
            print("Warning: Ollama warmup failed, first query may be slow.")
        self.scraper = GooglePlayScraper()
        
        # Configuration
        self.max_results_per_query = config['max_results_per_query']
        self.apps_per_run = config['apps_per_run']
        self.search_query_count = config['search_query_count']
        self.opportunity_threshold = config['opportunity_threshold']
        self.max_app_rating = config['max_app_rating']
        self.min_install_count = config['min_install_count']
        self.max_install_count = config['max_install_count']
    
    def select_niche(self) -> Optional[Dict]:
        """Select the next niche to search.
        
        Returns:
            Niche dictionary, or None if no niches are available
        """
        self.cursor.execute('''
            SELECT id, name, status, queries, current_query_index, current_offset, last_searched
            FROM niches
            WHERE status = 'ACTIVE'
            ORDER BY
                CASE WHEN last_searched IS NULL THEN 0 ELSE 1 END,
                last_searched ASC
            LIMIT 1
        ''')
        
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'status': row[2],
                'queries': json.loads(row[3]) if row[3] else [],
                'current_query_index': row[4] or 0,
                'current_offset': row[5] or 0,
                'last_searched': row[6],
            }
        return None
    
    def get_or_generate_queries(self, niche_name: str) -> List[str]:
        """Get existing queries for a niche or generate new ones.
        
        Args:
            niche_name: Name of the niche
            
        Returns:
            List of search queries
        """
        self.cursor.execute('''
            SELECT queries FROM niches WHERE name = ?
        ''', (niche_name,))
        
        row = self.cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        
        # Generate new queries
        prompt = f"""Generate {self.search_query_count} different Google Play Store search queries for finding Android apps related to this niche:

{niche_name.upper()}

Return only a JSON object with a "queries" key containing an array of search queries.

IMPORTANT: Each query must be 1-3 words maximum.

The queries should explore different types of apps within the niche.

Avoid repeating the exact same concept.
"""
        
        result = self.ollama.generate_json(prompt, expected_keys=['queries'])
        
        if result and 'queries' in result:
            queries = self._normalize_queries(result['queries'], niche_name)
            
            # Save queries to database
            self.cursor.execute('''
                UPDATE niches SET queries = ? WHERE name = ?
            ''', (json.dumps(queries), niche_name))
            self.conn.commit()
            
            return queries
        
        # Fallback: generate simple queries (1-3 words max)
        fallback_queries = self._normalize_queries([], niche_name)
        
        # Save fallback queries to database
        self.cursor.execute('''
            UPDATE niches SET queries = ? WHERE name = ?
        ''', (json.dumps(fallback_queries[:self.search_query_count]), niche_name))
        self.conn.commit()
        
        return fallback_queries[:self.search_query_count]

    def _normalize_queries(self, queries: List[str], niche_name: str) -> List[str]:
        """Keep search queries unique and within the 1-3 word limit."""
        normalized = []
        seen = set()

        candidates = list(queries) + [
            niche_name,
            f"{niche_name.split()[0]} app",
            f"{niche_name.split()[0]} tools",
            f"{niche_name.split()[0]} guide",
            f"{niche_name.split()[0]} tips",
            f"{niche_name.split()[0]} finder",
            f"{niche_name.split()[0]} tracker",
            f"{niche_name.split()[0]} planner",
            f"{niche_name.split()[0]} community",
            f"{niche_name.split()[0]} games",
        ]

        for query in candidates:
            if not isinstance(query, str):
                continue
            query = ' '.join(query.split())
            key = query.casefold()
            if query and 1 <= len(query.split()) <= 3 and key not in seen:
                normalized.append(query)
                seen.add(key)
            if len(normalized) == self.search_query_count:
                break

        return normalized
    
    def get_niche_queries(self, niche_name: str) -> List[str]:
        """Get queries for a niche from the database.
        
        Args:
            niche_name: Name of the niche
            
        Returns:
            List of search queries
        """
        self.cursor.execute('''
            SELECT queries FROM niches WHERE name = ?
        ''', (niche_name,))
        
        row = self.cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return []
    
    def search_niche(self, niche: Dict) -> int:
        """Search for apps in a niche.
        
        Args:
            niche: Niche dictionary with search state
            
        Returns:
            Number of new apps discovered
        """
        queries = self.get_or_generate_queries(niche['name'])
        current_index = niche['current_query_index']
        current_offset = niche['current_offset']
        
        processed_apps_count = 0
        
        # Search until we've processed enough apps or exhausted the query
        while processed_apps_count < self.apps_per_run and current_index < len(queries):
            if current_offset >= self.max_results_per_query:
                current_index += 1
                current_offset = 0
                continue

            query = queries[current_index]
            remaining_query_results = self.max_results_per_query - current_offset
            batch_limit = min(
                self.apps_per_run - processed_apps_count,
                remaining_query_results,
            )

            print(
                f"Searching {niche['name']}: '{query}' "
                f"(offset {current_offset}, up to {batch_limit})"
            )
            
            # Search Google Play
            apps = self.scraper.search_apps(
                query=query,
                offset=current_offset,
                max_results=batch_limit,
            )

            print(f"Search returned {len(apps)} result(s).")
            
            # Process each app
            for app_data in apps:
                self._process_app(app_data, niche['id'], queries[current_index])

            processed_apps_count += len(apps)
            
            # Update offset
            current_offset += len(apps)
            
            # Move on when the page has no more results or the configured limit is reached.
            if len(apps) == 0 or current_offset >= self.max_results_per_query:
                current_index += 1
                current_offset = 0
        
        # Update niche progress
        self.cursor.execute('''
            UPDATE niches 
            SET current_query_index = ?, 
                current_offset = ?,
                last_searched = datetime('now')
            WHERE id = ?
        ''', (current_index, current_offset, niche['id']))
        self.conn.commit()
        
        return processed_apps_count
    
    def _process_app(self, app_data: Dict, niche_id: int, current_query: str) -> bool:
        """Process a single app.
        
        Args:
            app_data: App data dictionary
            niche_id: ID of the niche being searched
            current_query: Current search query being processed
            
        Returns:
            True if a new app was processed, False if it already existed
        """
        package_name = app_data.get('package_name')
        if not package_name:
            return False

        app_data['name'] = app_data.get('name') or package_name
        
        # Check if app already exists
        self.cursor.execute('''
            SELECT id FROM apps WHERE package_name = ?
        ''', (package_name,))
        
        if self.cursor.fetchone():
            # App already exists, skip it
            print(f"Skipping existing app: {package_name}")
            return False
        
        # Get additional details if available
        if app_data.get('url'):
            details = self.scraper.get_app_details(package_name, app_data['url'])
            if details:
                app_data.update(details)

        # Save app to database
        self.cursor.execute('''
            INSERT INTO apps (
                package_name, name, developer, url, niche_id,
                description, category, rating, review_count,
                install_count, last_updated, price, contains_ads,
                offers_in_app_purchases
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            app_data.get('package_name'),
            app_data.get('name'),
            app_data.get('developer'),
            app_data.get('url'),
            niche_id,
            app_data.get('description'),
            app_data.get('category'),
            app_data.get('rating'),
            app_data.get('review_count'),
            app_data.get('install_count'),
            app_data.get('last_updated'),
            app_data.get('price'),
            app_data.get('contains_ads'),
            app_data.get('offers_in_app_purchases'),
        ))
        self.conn.commit()
        
        app_id = self.cursor.lastrowid
        print(f"Found app: {app_data['name']}")

        if self._matches_automatic_opportunity(app_data):
            rating = float(app_data['rating'])
            install_count = int(app_data['install_count'])
            reason = (
                "Automatic opportunity rule matched: "
                f"rating {rating} < {self.max_app_rating} and "
                f"install count {install_count} is between "
                f"{self.min_install_count} and {self.max_install_count}."
            )
            self.cursor.execute('''
                INSERT INTO opportunities (app_id, app_name, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (app_id, app_data.get('name'), self.opportunity_threshold, reason))
            self.conn.commit()
            print(
                f"Automatic opportunity: {app_data['name']} "
                f"(rating {rating}, installs {install_count})"
            )
            return True
        
        # Evaluate with Ollama
        is_interesting = self._evaluate_app(app_data, app_id)
        
        if is_interesting:
            return True
        
        return False

    def _matches_automatic_opportunity(self, app_data: Dict) -> bool:
        """Return whether an app meets the configured automatic opportunity rule."""
        if (
            self.max_app_rating is None
            or self.min_install_count is None
            or self.max_install_count is None
        ):
            return False

        try:
            rating = float(app_data.get('rating'))
            install_count = int(app_data.get('install_count'))
        except (TypeError, ValueError):
            return False

        return (
            rating < self.max_app_rating
            and self.min_install_count <= install_count <= self.max_install_count
        )
    
    def _evaluate_app(self, app_data: Dict, app_id: int) -> bool:
        """Evaluate an app using Ollama.
        
        Args:
            app_data: App data dictionary
            app_id: Database ID of the app
            
        Returns:
            True if app is interesting, False otherwise
        """
        # Build prompt for Ollama
        prompt = f"""Does this Android app look potentially interesting as a possible software opportunity?

We are looking for:

- Niche apps
- Apps solving a specific problem
- Apps with a clearly defined audience
- Apps that might potentially be improved upon
- Apps with low or mediocre user ratings relative to their apparent demand
- Apps that show evidence of meaningful demand
- Apps that may be outdated or neglected

Do not deeply research the app.

Use only the information provided.

Consider:

- How specific the niche is
- Whether the app solves a clear problem
- Whether there appears to be meaningful demand
- The app's rating
- The number of reviews
- The install count
- When the app was last updated
- Whether the app appears neglected or outdated
- Whether the app appears to have potential for improvement

Use this scoring rubric:

- 1-3: Poor opportunity; little evidence of demand or improvement potential
- 4-5: Weak or uncertain opportunity; some relevant signals but major concerns
- 6: Some promise, but the evidence is insufficient or important risks remain
- 7: Potentially interesting; credible demand and improvement potential
- 8: Strong opportunity; several strong signals and manageable risks
- 9-10: Exceptional and rare; compelling evidence across demand and improvement potential

Score the app based only on the evidence provided. Do not use 7 as a default.
Use lower scores when the evidence is weak or missing, and reserve 9-10 for
exceptional cases.

Return only valid JSON in this format:

{{
    "score": 1-10,
    "reason": "Short explanation"
}}

App Information:

Name: {app_data.get('name', 'N/A')}

Developer: {app_data.get('developer', 'N/A')}

Category: {app_data.get('category', 'N/A')}

Description:

{app_data.get('description', 'N/A')}

Rating: {app_data.get('rating', 'N/A')}

Review Count: {app_data.get('review_count', 'N/A')}

Install Count: {app_data.get('install_count', 'N/A')}

Last Updated: {app_data.get('last_updated', 'N/A')}

Price: {app_data.get('price', 'N/A')}

Contains Ads: {app_data.get('contains_ads', False)}

Offers In-App Purchases: {app_data.get('offers_in_app_purchases', False)}
"""
        
        result = self.ollama.generate_json(prompt, expected_keys=['score', 'reason'])
        
        if not result:
            return False
        
        score = result.get('score', 0)
        reason = result.get('reason', 'No reason provided')

        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 10:
            print(f"Invalid evaluation score for {app_data.get('name', 'Unknown')}: {score!r}")
            return False

        self.cursor.execute('''
            INSERT INTO app_evaluations (app_id, app_name, score, reason)
            VALUES (?, ?, ?, ?)
        ''', (app_id, app_data.get('name'), score, reason))
        self.conn.commit()
        
        if score >= self.opportunity_threshold:
            # Save as opportunity
            self.cursor.execute('''
                INSERT INTO opportunities (app_id, app_name, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (app_id, app_data.get('name'), score, reason))
            self.conn.commit()
            print(f"Opportunity: {app_data.get('name', 'Unknown')} (score {score})")
            return True
        
        return False
    
    def check_niche_exhausted(self, niche: Dict) -> bool:
        """Check if a niche has been exhausted.
        
        Args:
            niche: Niche dictionary
            
        Returns:
            True if niche is exhausted, False otherwise
        """
        queries = self.get_or_generate_queries(niche['name'])
        self.cursor.execute(
            'SELECT current_query_index FROM niches WHERE id = ?',
            (niche['id'],),
        )
        row = self.cursor.fetchone()
        current_index = row[0] if row else niche['current_query_index']
        
        if current_index >= len(queries):
            # Update niche status
            self.cursor.execute('''
                UPDATE niches SET status = 'EXHAUSTED' WHERE id = ?
            ''', (niche['id'],))
            self.conn.commit()
            return True
        
        return False
    
    def ensure_niche_queries(self, niche_name: str) -> List[str]:
        """Ensure a niche has queries generated, generate if missing.
        
        Args:
            niche_name: Name of the niche
            
        Returns:
            List of queries for the niche
        """
        queries = self.get_or_generate_queries(niche_name)
        return queries
    
    def run(self) -> None:
        """Run the main application loop."""
        print("Starting Scout...")
        
        # Initialize database if needed
        init_database()
        seed_niches()
        
        # Ensure all niches have queries generated
        print("\nChecking for niches without queries...")
        self.cursor.execute('''
            SELECT name FROM niches WHERE status = 'ACTIVE' AND queries IS NULL
        ''')
        niches_without_queries = self.cursor.fetchall()
        
        if niches_without_queries:
            print(f"Found {len(niches_without_queries)} niches without queries.")
            for (niche_name,) in niches_without_queries:
                print(f"  Generating queries for: {niche_name}")
                self.ensure_niche_queries(niche_name)
            print("Query generation complete.\n")
        
        # Select a niche
        niche = self.select_niche()
        if not niche:
            print("No active niches found.")
            return
        
        print(f"Processing niche: {niche['name']}")
        
        # Search for apps
        processed_apps = self.search_niche(niche)
        print(f"Processed {processed_apps} app result(s)")
        
        # Check if niche is exhausted
        if self.check_niche_exhausted(niche):
            print(f"Niche '{niche['name']}' is now exhausted.")
        
        print("Done.")


def main():
    """Main entry point."""
    app = ScoutApp()
    app.run()


if __name__ == '__main__':
    with run_log("single"):
        try:
            main()
        except Exception:
            traceback.print_exc()
            raise
