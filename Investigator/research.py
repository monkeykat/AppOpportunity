"""Dependency-light collection of public app evidence."""

from html.parser import HTMLParser
import re
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.parse import quote_plus
from google_play import fetch_page


class _TextParser(HTMLParser):
    """Extract visible text and links from a small HTML response."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self.links: List[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(" ".join(data.split()))


def _source_record(url: str, kind: str, html: str) -> Dict[str, Any]:
    parser = _TextParser()
    parser.feed(html)
    return {
        "url": url,
        "kind": kind,
        "text": " ".join(parser.parts)[:12000],
        "links": parser.links[:50],
    }


def _review_snippets(text: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Keep likely review lines, with lower ratings first when present."""
    snippets = []
    for line in re.split(r"[\n.!?]+", text):
        line = " ".join(line.split())
        rating = re.search(r"\b([1-5])\s*(?:/\s*5|stars?)\b", line, re.IGNORECASE)
        if rating or any(word in line.lower() for word in ("crash", "ads", "subscription", "missing", "bug")):
            snippets.append({"rating": int(rating.group(1)) if rating else None, "text": line[:1000]})
    return sorted(snippets, key=lambda item: (item["rating"] is None, item["rating"] or 9))[:limit]


def _search_records(query: str, html: str, limit: int = 10) -> List[Dict[str, str]]:
    parser = _TextParser()
    parser.feed(html)
    records = []
    for link in parser.links:
        if link.startswith("/"):
            link = urljoin("https://www.google.com", link)
        parsed = urlparse(link)
        if parsed.scheme not in ("http", "https"):
            continue
        if any(existing["url"] == link for existing in records):
            continue
        records.append({"query": query, "url": link})
        if len(records) >= limit:
            break
    return records


def _default_fetch(url: str) -> str:
    return fetch_page(url)


def _default_search(query: str) -> str:
    """Fetch a public search-results page without requiring another client."""
    return fetch_page("https://www.google.com/search?q={}".format(quote_plus(query)))


def collect_research(
    opportunity: Dict[str, Any],
    fetch: Optional[Callable[[str], str]] = None,
    search: Optional[Callable[[str], str]] = None,
) -> Dict[str, Any]:
    """Collect public evidence while retaining partial failures as metadata."""
    fetcher = fetch or _default_fetch
    searcher = search or _default_search
    url = opportunity.get("url")
    evidence: Dict[str, Any] = {
        "app": dict(opportunity),
        "sources": [],
        "reviews": [],
        "competitors": [],
        "alternatives": [],
        "errors": [],
    }
    if not url:
        evidence["errors"].append("Opportunity has no public URL")
        return evidence

    try:
        app_source = _source_record(url, "app_page", fetcher(url))
        evidence["sources"].append(app_source)
        evidence["reviews"] = _review_snippets(app_source["text"])
        for link in app_source["links"]:
            absolute = urljoin(url, link)
            host = urlparse(absolute).netloc
            if host and host != urlparse(url).netloc:
                try:
                    evidence["sources"].append(
                        _source_record(absolute, "developer_or_documentation", fetcher(absolute))
                    )
                except Exception as error:
                    evidence["errors"].append({"url": absolute, "error": str(error)})
                break
    except Exception as error:
        evidence["errors"].append({"url": url, "error": str(error)})

    if searcher:
        app_name = opportunity.get("app_name") or str(opportunity.get("app_id", "app"))
        review_query = '"{}" Google Play reviews'.format(app_name)
        try:
            review_html = searcher(review_query)
            evidence["reviews"].extend(_review_snippets(_source_record(
                "search:{}".format(review_query), "review_search", review_html
            )["text"]))
            evidence["sources"].append({
                "url": "search:{}".format(review_query),
                "kind": "review_search",
                "text": _source_record("", "review_search", review_html)["text"][:12000],
            })
            evidence["reviews"] = sorted(
                evidence["reviews"],
                key=lambda item: (item["rating"] is None, item["rating"] or 9),
            )[:20]
        except Exception as error:
            evidence["errors"].append({"query": review_query, "error": str(error)})
        for label, query in (
            ("competitors", "{} app alternatives competitors".format(app_name)),
            ("alternatives", "how do people solve {} without an app".format(app_name)),
        ):
            try:
                evidence[label].extend(_search_records(query, searcher(query)))
            except Exception as error:
                evidence["errors"].append({"query": query, "error": str(error)})
    return evidence