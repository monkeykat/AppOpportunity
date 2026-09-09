"""Phase 3 business analysis inputs derived from Phase 2 evidence."""

import json
from html.parser import HTMLParser
from typing import Any, Dict
from urllib.parse import quote_plus, urljoin, urlparse

try:
    from .config import MAX_RESEARCH_PAGES, MAX_SEARCH_RESULTS
except ImportError:
    from config import MAX_RESEARCH_PAGES, MAX_SEARCH_RESULTS


class _SearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text = []
        self.links = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.text.append(cleaned)


def _default_search(query: str) -> str:
    from urllib.request import urlopen

    with urlopen(
        "https://www.google.com/search?q={}".format(quote_plus(query)),
        timeout=30,
    ) as response:
        return response.read().decode("utf-8", errors="replace")


def _collect_topic_research(
    app_name: str,
    search: Any,
) -> Dict[str, Any]:
    topics = {
        "monetization": "{} app pricing subscription premium business model".format(app_name),
        "willingness_to_pay": "{} users willing to pay alternatives pricing".format(app_name),
        "advertising": "{} app advertising revenue audience monetization".format(app_name),
        "market_and_acquisition": "{} market community search alternatives customers".format(app_name),
    }
    results = {}
    errors = []
    pages_opened = 0
    for topic, query in topics.items():
        if pages_opened >= MAX_RESEARCH_PAGES:
            break
        try:
            parser = _SearchParser()
            parser.feed(search(query))
            records = []
            for link in parser.links:
                absolute = urljoin("https://www.google.com", link)
                if urlparse(absolute).scheme not in ("http", "https"):
                    continue
                if any(record["url"] == absolute for record in records):
                    continue
                records.append({"query": query, "url": absolute})
                if len(records) >= MAX_SEARCH_RESULTS:
                    break
            results[topic] = {
                "query": query,
                "results": records,
                "text": " ".join(parser.text)[:12000],
            }
            pages_opened += 1
        except Exception as error:
            errors.append({"topic": topic, "query": query, "error": str(error)})
    return {"topics": results, "errors": errors, "pages_opened": pages_opened}



def _decode_evidence(value: Any) -> Any:
    if not value:
        return []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []


def collect_business_research(
    opportunity: Dict[str, Any],
    search: Any = None,
) -> Dict[str, Any]:
    """Build a conservative Phase 3 analysis package from the Phase 2 record."""
    reviews = _decode_evidence(opportunity.get("raw_reviews"))
    competitors = _decode_evidence(opportunity.get("raw_competitors"))
    alternatives = _decode_evidence(opportunity.get("raw_alternatives"))
    app_name = opportunity.get("app_name") or str(opportunity.get("app_id", "app"))
    description = opportunity.get("description") or "The available Phase 2 description is limited."
    complaint_analysis = opportunity.get("complaint_analysis") or "No complaint analysis was available."
    competitor_analysis = opportunity.get("competitor_analysis") or "No competitor analysis was available."
    alternative_analysis = opportunity.get("alternative_analysis") or "No alternative analysis was available."
    topic_research = _collect_topic_research(app_name, search or _default_search)

    phase2_results = {
        "app": {
            "app_id": opportunity.get("app_id"),
            "app_name": app_name,
            "developer": opportunity.get("developer"),
            "url": opportunity.get("url"),
            "description": description,
            "category": opportunity.get("category"),
            "rating": opportunity.get("rating"),
            "review_count": opportunity.get("review_count"),
            "install_count": opportunity.get("install_count"),
        },
        "analysis": {
            "app_analysis": opportunity.get("app_analysis") or "",
            "user_analysis": opportunity.get("user_analysis") or "",
            "complaint_analysis": complaint_analysis,
            "competitor_analysis": competitor_analysis,
            "alternative_analysis": alternative_analysis,
            "build_difficulty": opportunity.get("build_difficulty"),
            "proprietary_dependency": opportunity.get("proprietary_dependency"),
            "market_potential": opportunity.get("market_potential"),
            "competition_level": opportunity.get("competition_level"),
            "final_score": opportunity.get("final_score"),
            "recommendation": opportunity.get("recommendation"),
            "summary": opportunity.get("summary") or "",
        },
        "raw_evidence": {
            "reviews": reviews,
            "competitors": competitors,
            "alternatives": alternatives,
        },
    }

    return {
        "phase2_results": phase2_results,
        "evidence": {
            "app_name": app_name,
            "description": description,
            "phase2_summary": opportunity.get("summary") or "",
            "reviews": reviews,
            "competitors": competitors,
            "alternatives": alternatives,
            "review_count": len(reviews),
            "competitor_count": len(competitors),
            "alternative_count": len(alternatives),
        },
        "business_questions": [
            "What is the smallest useful MVP that tests the strongest problem?",
            "Who has this problem often enough to seek and adopt a solution?",
            "Why would a new user choose this and why would an existing user switch?",
            "What evidence suggests users would pay or that advertising could work?",
            "How large and reachable is the apparent market?",
            "What must be true for the business to work, and why might it fail?",
        ],
        "additional_research": topic_research,
        "product_concept": "Define the smallest useful product that addresses the strongest evidence-backed problem in {}.".format(app_name),
        "target_customer": opportunity.get("user_analysis") or "The target customer requires further evidence.",
        "value_proposition": complaint_analysis,
        "differentiation": competitor_analysis,
        "monetization": "Research paid, subscription, premium, advertising, licensing, affiliate, and sponsorship options; no willingness-to-pay evidence is assumed.",
        "willingness_to_pay": "Evidence is unconfirmed; look for paid alternatives, subscriptions, premium features, and business buyers.",
        "apparent_market_size": "Use Phase 2 demand signals, review volume, installs, communities, and search activity without presenting a precise TAM.",
        "customer_acquisition_difficulty": "Assess search intent, communities, app discovery, partnerships, and paid acquisition before assuming customers are reachable.",
        "revenue_potential": "Estimate only at a rough, evidence-based level after considering pricing, audience, monetization, and acquisition difficulty.",
        "business_risks": "Consider weak demand, low willingness to pay, adequate existing solutions, competition, acquisition cost, seasonality, and dependencies.",
        "key_assumptions": "State what must be true about the customer, problem frequency, switching behavior, monetization, market size, and acquisition.",
        "alternative_analysis": alternative_analysis,
    }
