"""Strict validation and prompt construction for Phase 4 output."""

import json
import re
from typing import Any, Dict

try:
    from .database import RECOMMENDATIONS, STRATEGIES
except ImportError:
    from database import RECOMMENDATIONS, STRATEGIES

REQUIRED_TEXT = (
    "product_summary", "target_user", "core_problem", "differentiation",
    "design_rationale", "validation_hypothesis", "core_user_workflow",
    "mvp_scope",
)
REQUIRED_LISTS = (
    "product_strategy", "rejected_alternatives", "inherited_constraints",
    "must_have_features", "nice_to_have_features", "excluded_features",
    "technical_considerations", "success_criteria", "minimum_validation_scope",
)
REQUIRED_FIELDS = set(REQUIRED_TEXT + REQUIRED_LISTS + (
    "evidence_to_support_or_reject", "technical_risks", "design_score", "recommendation",
))
ALLOWED_FIELDS = REQUIRED_FIELDS | {"product_name"}
OBSERVABLE_MARKERS = re.compile(
    r"\b(users?|customers?|persons?|complete|finish|record|log|measure|time|second|minute|"
    r"hour|day|week|month|count|number|rate|percent|%|return|use|crash|error|"
    r"interview|feedback|support|reject|under|over|at least|zero)\b",
    re.IGNORECASE,
)


def _nonempty_text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")


def _tokens(value: str) -> set[str]:
    ignored = {"a", "an", "and", "the", "to", "of", "in", "for", "with", "or"}
    return {
        token for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in ignored
    }


def _require_observable(value: Any, name: str) -> None:
    _nonempty_text(value, name)
    if not OBSERVABLE_MARKERS.search(value):
        raise ValueError(f"{name} must describe observable evidence")


def _valid_source_phase(value: Any) -> bool:
    if value in {2, 3}:
        return True
    return isinstance(value, str) and value.strip().upper() in {"PHASE 2", "PHASE 3"}


def validate_design(result: Dict[str, Any]) -> None:
    unexpected = sorted(set(result) - ALLOWED_FIELDS)
    if unexpected:
        raise ValueError("Product design contains unexpected fields: " + ", ".join(unexpected))
    missing = sorted(field for field in REQUIRED_FIELDS if field not in result)
    if missing:
        raise ValueError("Product design is missing: " + ", ".join(missing))
    for field in REQUIRED_TEXT:
        _nonempty_text(result[field], field)
    for field in REQUIRED_LISTS:
        if not isinstance(result[field], list):
            raise ValueError(f"{field} must be a JSON array")
    if not result["product_strategy"] or any(item not in STRATEGIES for item in result["product_strategy"]):
        raise ValueError("product_strategy must contain permitted strategy values")
    if not 1 <= len(result["minimum_validation_scope"]) <= 3:
        raise ValueError("minimum_validation_scope must contain one to three capabilities")
    if len(result["core_user_workflow"].split("->")) < 2 and len(result["core_user_workflow"].split("→")) < 2:
        raise ValueError("core_user_workflow must contain at least two ordered actions")
    if not result["must_have_features"]:
        raise ValueError("must_have_features must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in result["must_have_features"]):
        raise ValueError("must_have_features must contain non-empty strings")
    if any(not isinstance(item, str) or not item.strip() for item in result["minimum_validation_scope"]):
        raise ValueError("minimum_validation_scope must contain non-empty strings")
    if set(result["must_have_features"]) & set(result["excluded_features"]):
        raise ValueError("must-have and excluded features must not overlap")
    workflow_context = result["core_user_workflow"] + " " + " ".join(result["minimum_validation_scope"])
    workflow_tokens = _tokens(workflow_context)
    for feature in result["must_have_features"]:
        if not (_tokens(feature) & workflow_tokens):
            raise ValueError(f"Must-have feature is not represented in the core workflow: {feature}")
    if not isinstance(result["evidence_to_support_or_reject"], list) or not result["evidence_to_support_or_reject"]:
        raise ValueError("evidence_to_support_or_reject must contain evidence references")
    for evidence in result["evidence_to_support_or_reject"]:
        if not isinstance(evidence, dict):
            raise ValueError("Evidence references must be JSON objects")
        for field in ("claim", "source_phase", "source_field", "evidence_summary"):
            if field not in evidence or not str(evidence[field]).strip():
                raise ValueError(f"Evidence reference missing {field}")
        if not _valid_source_phase(evidence["source_phase"]):
            raise ValueError("Evidence source_phase must be 2 or 3")
        _require_observable(evidence["evidence_summary"], "evidence_summary")
    if any(not isinstance(item, str) or not item.strip() for item in result["success_criteria"]):
        raise ValueError("success_criteria must contain non-empty observable statements")
    for criterion in result["success_criteria"]:
        _require_observable(criterion, "success_criteria item")
    if not isinstance(result["technical_risks"], list):
        raise ValueError("technical_risks must be a JSON array")
    for risk in result["technical_risks"]:
        if not isinstance(risk, dict) or risk.get("severity") not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValueError("Each technical risk needs LOW, MEDIUM, or HIGH severity")
        if not isinstance(risk.get("blocks_validation"), bool):
            raise ValueError("technical risk blocks_validation must be boolean")
    if any(risk["severity"] == "HIGH" and risk["blocks_validation"] for risk in result["technical_risks"]):
        raise ValueError("Unresolved high-severity technical risk blocks validation")
    score = result["design_score"]
    if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 10:
        raise ValueError("design_score must be an integer from 1 to 10")
    expected = "PASS" if score <= 3 else "DESIGN_REVIEW" if score <= 5 else "READY_FOR_POC"
    if result["recommendation"] not in RECOMMENDATIONS or result["recommendation"] != expected:
        raise ValueError(f"Recommendation does not match design_score band: {score} should be {expected}")


def build_design_prompt(opportunity: Dict[str, Any]) -> str:
    phase2 = {key: opportunity.get(key) for key in (
        "app_name", "description", "category", "reason", "app_analysis",
        "user_analysis", "complaint_analysis", "competitor_analysis",
        "alternative_analysis", "summary", "final_score",
    )}
    phase3 = {key: opportunity.get(key) for key in (
        "product_concept", "target_customer", "value_proposition", "differentiation",
        "business_risks", "key_assumptions", "viability_score", "phase3_recommendation",
    )}
    prompt = """You are defining a focused software product from supplied research.
Phase 3 already evaluated business viability. Do not repeat business validation.
Phase 4 must define one target user, one core workflow, and the smallest product
that can test a falsifiable hypothesis. Do not clone the existing app or add
features merely because competitors have them. Phase 5 will decide architecture.
product_strategy must contain only these exact uppercase values:
SIMPLER, CHEAPER, MORE_SPECIALIZED, BETTER_WORKFLOW,
BETTER_USER_EXPERIENCE, DIFFERENT_AUDIENCE, SOLVE_MISSING_PROBLEM.
product_strategy must be a JSON array, for example ["SIMPLER"].
minimum_validation_scope must be a JSON array of one, two, or three short
capability strings, never a paragraph or a scalar string. For example:
["Create record", "View record"].
must_have_features, nice_to_have_features, excluded_features,
technical_considerations, and success_criteria must also be JSON arrays.
technical_risks must be a JSON array of objects with exactly these keys:
risk, severity, why_it_matters, possible_mitigation, and blocks_validation.
Use an empty array [] when there are no technical risks. Severity must be
exactly LOW, MEDIUM, or HIGH and blocks_validation must be true or false.
Return only valid JSON matching the requested schema.

PHASE 2 EVIDENCE:
{}

PHASE 3 BUSINESS CONSTRAINTS:
{}

Return fields for the complete product design, including product_summary,
core_problem, target_user, product_strategy, differentiation, design_rationale,
rejected_alternatives, inherited_constraints, validation_hypothesis,
core_user_workflow, minimum_validation_scope, evidence_to_support_or_reject,
must_have_features, nice_to_have_features, excluded_features, mvp_scope,
technical_considerations, technical_risks, success_criteria, design_score, and
recommendation. Evidence references must contain claim, source_phase,
source_field, and evidence_summary. Technical risks must contain risk, severity,
why_it_matters, possible_mitigation, and blocks_validation.
Recommendation bands are 1-3 PASS, 4-5 DESIGN_REVIEW, and 6-10 READY_FOR_POC.
The recommendation must exactly match the score: scores 1, 2, or 3 require
PASS; scores 4 or 5 require DESIGN_REVIEW; scores 6 through 10 require
READY_FOR_POC. Do not return a different recommendation for a given score.

""".format(json.dumps(phase2, default=str), json.dumps(phase3, default=str))
    return prompt


DESIGN_SCHEMA = {
    "type": "object",
    "required": sorted(REQUIRED_FIELDS),
    "additionalProperties": False,
    "properties": {
        "product_name": {"type": "string"},
        "product_summary": {"type": "string", "minLength": 1},
        "core_problem": {"type": "string", "minLength": 1},
        "target_user": {"type": "string", "minLength": 1},
        "product_strategy": {"type": "array", "items": {"type": "string"}},
        "differentiation": {"type": "string", "minLength": 1},
        "design_rationale": {"type": "string", "minLength": 1},
        "rejected_alternatives": {"type": "array"},
        "inherited_constraints": {"type": "array"},
        "validation_hypothesis": {"type": "string", "minLength": 1},
        "core_user_workflow": {"type": "string", "minLength": 1},
        "minimum_validation_scope": {"type": "array", "minItems": 1, "maxItems": 3},
        "evidence_to_support_or_reject": {"type": "array", "minItems": 1},
        "must_have_features": {"type": "array", "minItems": 1},
        "nice_to_have_features": {"type": "array"},
        "excluded_features": {"type": "array"},
        "mvp_scope": {"type": "string", "minLength": 1},
        "technical_considerations": {"type": "array"},
        "technical_risks": {"type": "array"},
        "success_criteria": {"type": "array", "minItems": 1},
        "design_score": {"type": "integer", "minimum": 1, "maximum": 10},
        "recommendation": {"type": "string", "enum": list(RECOMMENDATIONS)},
    },
}

__all__ = ["DESIGN_SCHEMA", "build_design_prompt", "validate_design"]
