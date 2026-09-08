"""Validation for Phase 3 business assessments."""

from typing import Any, Dict

try:
    from .database import RECOMMENDATIONS, TEXT_FIELDS
except ImportError:
    from database import RECOMMENDATIONS, TEXT_FIELDS


SCORE_FIELDS = ("viability_score",)

ASSESSMENT_SCHEMA = {
    "type": "object",
    "required": [
        "product_concept", "target_customer", "value_proposition",
        "differentiation", "monetization", "willingness_to_pay",
        "apparent_market_size", "customer_acquisition_difficulty",
        "revenue_potential", "business_risks", "key_assumptions",
        "viability_score", "recommendation", "summary",
    ],
    "properties": {
        field: {"type": "string", "minLength": 1}
        for field in TEXT_FIELDS
    },
    "additionalProperties": False,
}
ASSESSMENT_SCHEMA["properties"]["viability_score"] = {
    "type": "integer", "minimum": 1, "maximum": 10,
}
ASSESSMENT_SCHEMA["properties"]["recommendation"] = {
    "type": "string",
    "enum": list(RECOMMENDATIONS),
}


def validate_assessment(result: Dict[str, Any]) -> None:
    required = set(TEXT_FIELDS + SCORE_FIELDS + ("recommendation",))
    missing = sorted(field for field in required if field not in result)
    if missing:
        raise ValueError("Assessment is missing: {}".format(", ".join(missing)))
    for field in TEXT_FIELDS:
        if not isinstance(result[field], str) or not result[field].strip():
            raise ValueError("Assessment field must be non-empty text: {}".format(field))
    score = result["viability_score"]
    if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 10:
        raise ValueError("viability_score must be an integer from 1 to 10")
    recommendation = result["recommendation"]
    if recommendation not in RECOMMENDATIONS:
        raise ValueError("Invalid recommendation: {}".format(recommendation))
    expected = (
        "PASS" if score <= 3 else
        "POSSIBLE" if score <= 5 else
        "PROMISING" if score <= 7 else
        "BUILD_CANDIDATE"
    )
    if recommendation != expected:
        raise ValueError(
            "Recommendation does not match viability_score band: {} should be {}".format(
                score, expected
            )
        )


def build_assessment_prompt(opportunity: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    return """You are evaluating whether a potential software product could plausibly become a viable business.
Use only the supplied Phase 2 evidence and Phase 3 analysis. Use cautious language and distinguish evidence from interpretation.
Do not assume popularity means willingness to pay, low ratings create an opportunity, or a better product will attract customers.
Actively identify why users may not switch, pay, or be reachable, and why the market or advertising model may fail.
Strong opportunities should be rare. A score of 8 or higher requires evidence of demand, active solution-seeking,
meaningful differentiation, plausible monetization, a sufficiently large market, and reachable customers.
Return exactly these fields as JSON:
product_concept, target_customer, value_proposition, differentiation, monetization,
willingness_to_pay, apparent_market_size, customer_acquisition_difficulty, revenue_potential,
business_risks, key_assumptions, viability_score, recommendation, summary.
viability_score must be an integer from 1 to 10.
Recommendation bands are 1-3 PASS, 4-5 POSSIBLE, 6-7 PROMISING, and 8-10 BUILD_CANDIDATE.
The summary must explain the opportunity, major risks, and important assumptions.

Phase 2 opportunity and investigation:
{}

Phase 3 analysis:
{}""".format(opportunity, analysis)
