"""Phase 2 Google Play page access with a dependency-safe fallback."""

def fetch_page(url: str, timeout_ms: int = 30000) -> str:
    """Fetch rendered page HTML with Playwright when available.

    Importing Playwright lazily keeps database and offline test operations usable
    before browser dependencies are installed.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _fetch_with_standard_library(url)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            return page.content()
        finally:
            browser.close()


def _fetch_with_standard_library(url: str) -> str:
    from urllib.request import Request, urlopen

    request = Request(url, headers={"User-Agent": "AppOpportunityInvestigator/1.0"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")