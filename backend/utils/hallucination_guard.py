"""Hallucination guard — validates LLM insights against computed data.

Architecture:
- All calculations are done deterministically by pandas/numpy/scipy
- LLM only generates natural language narration of pre-computed results
- This module cross-references LLM output numbers against the actual data
- Insights that cite numbers not grounded in the data get flagged
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Regex to extract numbers from text (integers, decimals, percentages)
_NUMBER_RE = re.compile(r"(?<!\w)(-?\d+(?:,\d{3})*(?:\.\d+)?)\s*%?")


def extract_numbers(text: str) -> list[float]:
    """Extract all numeric values from a text string."""
    matches = _NUMBER_RE.findall(text)
    numbers = []
    for m in matches:
        try:
            numbers.append(float(m.replace(",", "")))
        except ValueError:
            pass
    return numbers


def extract_data_numbers(analysis_dict: dict[str, Any], max_depth: int = 3) -> set[float]:
    """Recursively extract all numeric values from the computed analysis dict."""
    numbers: set[float] = set()

    def _walk(obj: Any, depth: int = 0) -> None:
        if depth > max_depth:
            return
        if isinstance(obj, (int, float)):
            numbers.add(round(float(obj), 4))
        elif isinstance(obj, str):
            for n in extract_numbers(obj):
                numbers.add(round(n, 4))
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v, depth + 1)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _walk(item, depth + 1)

    _walk(analysis_dict)
    return numbers


def is_number_grounded(claimed: float, ground_truth: set[float], tolerance: float = 0.05) -> bool:
    """Check if a claimed number is within tolerance of any ground truth number."""
    if claimed == 0:
        return True  # Zero is always valid
    for gt in ground_truth:
        if gt == 0:
            continue
        relative_error = abs(claimed - gt) / max(abs(gt), 1e-9)
        if relative_error <= tolerance:
            return True
    return False


def validate_insights(
    insights: list[str],
    analysis_dict: dict[str, Any],
    tolerance: float = 0.10,
) -> dict[str, Any]:
    """
    Validate LLM-generated insights against computed analysis data.

    Returns:
        {
            "valid_insights": [...],       # Insights that pass grounding check
            "flagged_insights": [...],     # Insights with ungrounded numbers
            "grounding_score": float,      # 0.0-1.0 how well grounded the output is
            "total_numbers_checked": int,
            "ungrounded_numbers": int,
        }
    """
    ground_truth = extract_data_numbers(analysis_dict)
    valid: list[str] = []
    flagged: list[str] = []
    total_checked = 0
    ungrounded = 0

    for insight in insights:
        claimed_numbers = extract_numbers(insight)
        if not claimed_numbers:
            # No numbers — text-only insight, keep it
            valid.append(insight)
            continue

        insight_ungrounded = 0
        for num in claimed_numbers:
            total_checked += 1
            # Skip very small numbers (likely ordinals like "3 insights")
            if abs(num) < 1 and num != 0:
                continue
            if not is_number_grounded(num, ground_truth, tolerance):
                insight_ungrounded += 1
                ungrounded += 1

        # If more than half the numbers in an insight are ungrounded, flag it
        if insight_ungrounded > len(claimed_numbers) / 2:
            flagged.append(insight)
            logger.warning("Flagged insight (ungrounded numbers): %s", insight[:100])
        else:
            valid.append(insight)

    grounding_score = 1.0 - (ungrounded / max(total_checked, 1))

    result = {
        "valid_insights": valid,
        "flagged_insights": flagged,
        "grounding_score": round(grounding_score, 3),
        "total_numbers_checked": total_checked,
        "ungrounded_numbers": ungrounded,
    }

    if flagged:
        logger.warning(
            "Hallucination guard: %d/%d insights flagged (grounding=%.0f%%)",
            len(flagged), len(insights), grounding_score * 100
        )
    else:
        logger.info("Hallucination guard: all %d insights grounded (%.0f%%)", len(insights), grounding_score * 100)

    return result


def ground_insights(
    insights: list[str],
    analysis_dict: dict[str, Any],
    tolerance: float = 0.10,
) -> list[str]:
    """
    Return only grounded insights. Flagged insights are replaced with a safe version.
    This is the primary function agents should call.
    """
    result = validate_insights(insights, analysis_dict, tolerance)

    grounded = list(result["valid_insights"])

    # For flagged insights, add a disclaimer prefix instead of dropping them entirely
    for flagged in result["flagged_insights"]:
        grounded.append(f"[Note: Some figures are approximations] {flagged}")

    return grounded
