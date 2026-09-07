"""Validation for Ollama investigation assessments."""

from typing import Any, Dict

from database import RECOMMENDATIONS


TEXT_FIELDS = (
    "app_analysis",
    "user_analysis",
    "complaint_analysis",
    "competitor_analysis",
    "alternative_analysis",
    "summary",
)
SCORE_FIELDS = (
    "build_difficulty",
    "proprietary_dependency",
    "market_potential",
    "competition_level",
    "final_score",
)


def validate_assessment(result: Dict[str, Any]) -> None:
    """Reject incomplete or unsafe model output before it reaches SQLite."""
    required = set(TEXT_FIELDS + SCORE_FIELDS + ("recommendation",))
    missing = sorted(field for field in required if field not in result)
    if missing:
        raise ValueError("Assessment is missing: {}".format(", ".join(missing)))
    for field in TEXT_FIELDS:
        if not isinstance(result[field], str) or not result[field].strip():
            raise ValueError("Assessment field must be non-empty text: {}".format(field))
    for field in SCORE_FIELDS:
        value = result[field]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10:
            raise ValueError("Assessment score must be an integer from 1 to 10: {}".format(field))
    if result["recommendation"] not in RECOMMENDATIONS:
        raise ValueError("Invalid recommendation: {}".format(result["recommendation"]))