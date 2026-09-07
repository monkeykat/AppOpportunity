"""Google Play scraping module using Playwright."""

import time
import json
from typing import List, Dict, Optional
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, Page, Locator
from config import config
import re


class GooglePlayScraper:
    """Scraper for Google Play Store."""
    
    def __init__(self):
        self.base_url = "https://play.google.com"
        self.search_url = f"{self.base_url}/store/search"
        self.request_delay = config['request_delay_seconds']
    
    def search_apps(self, query: str, offset: int = 0, max_results: int = 20) -> List[Dict]:
        """Search for apps on Google Play.
        
        Args:
            query: Search query string
            offset: Offset to start results from
            max_results: Maximum number of results to return
            
        Returns:
            List of app dictionaries with basic information
        """
        apps = []
        
        with sync_playwright() as p:
            with p.chromium.launch(headless=True) as browser:
                page = browser.new_page()

                # Google Play keeps background requests open, so networkidle can hang.
                url = f"{self.search_url}?{urlencode({'q': query, 'c': 'apps'})}"
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30_000)
                    page.wait_for_selector(
                        'a[href*="/store/apps/details?id="]',
                        timeout=15_000,
                    )
                except Exception as e:
                    print(f"Error loading search results for '{query}': {e}")
                    return apps
                time.sleep(self.request_delay)

                app_links = page.locator('a[href*="/store/apps/details?id="]')
                target_count = offset + max_results
                previous_count = 0
                stalled_scrolls = 0

                while app_links.count() < target_count and stalled_scrolls < 3:
                    count = app_links.count()
                    if count == previous_count:
                        stalled_scrolls += 1
                    else:
                        stalled_scrolls = 0
                        previous_count = count

                    if count > 0:
                        app_links.nth(count - 1).scroll_into_view_if_needed()
                    page.wait_for_timeout(max(self.request_delay * 1000, 1000))

                count = app_links.count()

                start_idx = min(offset, count)
                end_idx = min(offset + max_results, count)

                for i in range(start_idx, end_idx):
                    link = app_links.nth(i)
                    href = link.get_attribute('href')
                    if href:
                        app = self._extract_app_info_from_link(link, page)
                        if app:
                            apps.append(app)
            
        return apps
    
    def _extract_app_info_from_link(self, link: Locator, page: Page) -> Optional[Dict]:
        """Extract app information from an app link element.
        
        Args:
            link: The link element pointing to app details
            page: The page object for navigation
            
        Returns:
            Dictionary with app information, or None if extraction fails
        """
        try:
            href = link.get_attribute('href')
            if not href:
                return None
            
            package_name = self._extract_package_name(href)
            if not package_name:
                return None
            
            # Get name from link text
            name = link.text_content()
            
            return {
                'package_name': package_name,
                'name': name.strip() if name else None,
                'developer': None,
                'url': f"{self.base_url}{href}" if href else None,
                'rating': None,
                'review_count': None,
                'install_count': None,
                'category': None,
                'description': None,
                'price': None,
                'contains_ads': False,
                'offers_in_app_purchases': False,
            }
        except Exception as e:
            print(f"Error extracting app info from link: {e}")
            return None
    
    def _extract_package_name(self, url: str) -> Optional[str]:
        """Extract package name from Google Play URL.
        
        Args:
            url: The Google Play app URL
            
        Returns:
            Package name, or None if not found
        """
        match = re.search(r'id=([a-zA-Z0-9_.]+)', url)
        if match:
            return match.group(1)
        return None
    
    def get_app_details(self, package_name: str, url: str) -> Optional[Dict]:
        """Get detailed information for an app.
        
        Args:
            package_name: The package name of the app
            url: The Google Play URL for the app
            
        Returns:
            Dictionary with detailed app information, or None if extraction fails
        """
        with sync_playwright() as p:
            with p.chromium.launch(headless=True) as browser:
                page = browser.new_page()
                
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30_000)
                    page.wait_for_selector('h1', timeout=15_000)
                except Exception as e:
                    print(f"Error loading app details: {e}")
                    return None

                time.sleep(self.request_delay)
                
                details = {
                    'package_name': package_name,
                }

                structured = self._extract_structured_app_data(page)
                details.update(structured)
                
                # Extract name from h1
                name = page.locator('h1').first
                if 'name' not in details and name.count() > 0:
                    details['name'] = name.first.text_content().strip()
                
                # Extract developer from link
                developer = page.locator('a[href*="/store/apps/dev?id="]').first
                if 'developer' not in details and developer.count() > 0:
                    details['developer'] = developer.text_content().strip()
                
                # Extract description from main content section - look for text starting with 'About this app'
                desc = page.locator('div:has-text("About this app")').first
                if 'description' not in details and desc.count() > 0:
                    details['description'] = desc.text_content().strip()
                
                # Extract category from semantic metadata, with a legacy fallback.
                category = page.locator('[itemprop="genre"]').first
                if 'category' not in details and category.count() > 0:
                    details['category'] = category.text_content().strip()
                elif 'category' not in details:
                    category_links = page.locator('a[href*="/store/apps/category="]')
                    if category_links.count() > 0:
                        details['category'] = category_links.last.text_content().strip()
                
                # Extract rating from aria-label
                rating = page.locator(
                    '[role=img][aria-label*="stars out of"], '
                    '[role=img][aria-label*="stars"]'
                ).first
                if 'rating' not in details and rating.count() > 0:
                    aria = rating.get_attribute('aria-label')
                    match = re.search(r'(\d+(?:\.\d+)?)', aria or '')
                    if match:
                        details['rating'] = float(match.group(1))
                
                # Extract review count
                review = page.locator('div.g1rdde').first
                if 'review_count' not in details and review.count() > 0:
                    review_text = review.text_content()
                    # Parse text like "54M reviews" or "1,234"
                    details['review_count'] = self._parse_count(review_text)
                
                # The number and label are siblings in the downloads metadata block.
                install_label = page.get_by_text('Downloads', exact=True).first
                install = install_label.locator('xpath=..') if install_label.count() > 0 else None
                if install is not None and install.count() > 0:
                    install_text = install.text_content()
                    details['install_count'] = self._parse_count(install_text)
                
                # Extract last updated - look for "Updated on" text
                updated_label = page.get_by_text('Updated on', exact=True).first
                updated = updated_label.locator('xpath=..') if updated_label.count() > 0 else None
                if 'last_updated' not in details and updated is not None and updated.count() > 0:
                    updated_text = updated.text_content()
                    # Extract date from text like "Updated on Sep 2, 2026"
                    match = re.search(r'Updated on\s*([A-Za-z]+\s+\d+,?\s+\d+)', updated_text)
                    if match:
                        details['last_updated'] = match.group(1).strip()
                
                # Extract price
                price = page.locator('span.IX9Uod').first
                if 'price' not in details and price.count() > 0:
                    price_text = price.text_content()
                    if price_text in ['Install', 'Available on']:
                        details['price'] = 0.0
                    else:
                        # Parse price like "$4.99"
                        match = re.search(r'\$([\d.]+)', price_text)
                        if match:
                            details['price'] = float(match.group(1))
                if 'price' not in details and page.get_by_text('Install', exact=True).count() > 0:
                    details['price'] = 0.0
                
                # Check for ads
                ads = page.locator('div:has-text("Contains ads")')
                details['contains_ads'] = ads.count() > 0
                
                # Check for in-app purchases
                iap = page.locator('div:has-text("Offers in-app purchases")')
                details['offers_in_app_purchases'] = iap.count() > 0
                
                return details

    def _extract_structured_app_data(self, page: Page) -> Dict:
        """Extract app metadata from a SoftwareApplication JSON-LD block."""
        for script in page.locator('script[type="application/ld+json"]').all():
            try:
                data = json.loads(script.text_content() or '')
            except (TypeError, json.JSONDecodeError):
                continue

            candidates = data.get('@graph', []) if isinstance(data, dict) else data
            if isinstance(candidates, dict):
                candidates = [candidates]
            if not isinstance(candidates, list):
                continue

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                schema_type = candidate.get('@type', '')
                types = schema_type if isinstance(schema_type, list) else [schema_type]
                if 'SoftwareApplication' not in types:
                    continue

                result = {}
                for source_key, target_key in (
                    ('name', 'name'),
                    ('description', 'description'),
                    ('applicationCategory', 'category'),
                    ('dateModified', 'last_updated'),
                ):
                    value = candidate.get(source_key)
                    if isinstance(value, str) and value.strip():
                        result[target_key] = value.strip()

                author = candidate.get('author')
                if isinstance(author, dict) and author.get('name'):
                    result['developer'] = str(author['name']).strip()

                rating = candidate.get('aggregateRating')
                if isinstance(rating, dict):
                    rating_value = rating.get('ratingValue')
                    review_count = rating.get('ratingCount')
                    try:
                        result['rating'] = float(rating_value)
                    except (TypeError, ValueError):
                        pass
                    try:
                        result['review_count'] = int(review_count)
                    except (TypeError, ValueError):
                        pass

                offers = candidate.get('offers')
                if isinstance(offers, list):
                    offers = offers[0] if offers else None
                if isinstance(offers, dict):
                    try:
                        result['price'] = float(offers['price'])
                    except (KeyError, TypeError, ValueError):
                        pass

                return result

        return {}
    
    def _parse_count(self, text: str) -> Optional[int]:
        """Parse a count string like '1.2M reviews' or '10B+Downloads' to an integer.
        
        Args:
            text: The count string to parse
            
        Returns:
            Integer count, or None if parsing fails
        """
        import re
        if not text:
            return None
        
        text = text.replace(',', '').strip()
        
        # Extract the number part using regex (handles "14.4M reviews", "10B+Downloads", etc.)
        match = re.search(r'([\d.]+)\s*([KMB]?)\s*[+\s]?', text, re.IGNORECASE)
        if not match:
            try:
                return int(text)
            except ValueError:
                return None
        
        try:
            number = float(match.group(1))
            suffix = match.group(2).upper() if match.group(2) else ''
            
            if suffix == 'B':
                return int(number * 1_000_000_000)
            elif suffix == 'M':
                return int(number * 1_000_000)
            elif suffix == 'K':
                return int(number * 1_000)
            else:
                return int(number)
        except ValueError:
            return None
    
    def close(self) -> None:
        """Close the scraper and cleanup resources."""
        pass  # Playwright handles cleanup automatically in context managers
