"""Validates agent outputs — structure, completeness, and data grounding."""

import logging
from typing import Any

from utils.hallucination_guard import ground_insights

logger = logging.getLogger(__name__)


def validate_agent_output(output: dict) -> bool:
    """Check that insights list and analysis dict are non-empty."""
    insights = output.get("insights", [])
    analysis = output.get("analysis_dict", output.get("pricing_analysis",
                output.get("churn_analysis", output.get("forecast_df", {}))))
    return bool(insights) and bool(analysis is not None and len(str(analysis)) > 2)


def validate_and_ground(output: dict[str, Any], agent_type: str) -> tuple[dict[str, Any], float]:
    """
    Validate agent output AND run hallucination grounding.
    Replaces raw insights with grounded insights.

    Returns:
        Tuple of (output dict with grounded insights, grounding_score 0.0-1.0)
    """
    insights = output.get("insights", [])
    if not insights:
        return output, 1.0

    # Get the analysis dict based on agent type
    analysis_dict_key = {
        "pricing": "pricing_analysis",
        "churn": "churn_analysis",
        "forecasting": "forecast_df",
        "general": "analysis_dict",
    }.get(agent_type, "analysis_dict")

    analysis_dict = output.get(analysis_dict_key, output.get("analysis_dict", {}))

    if not analysis_dict or not isinstance(analysis_dict, dict):
        logger.warning("No analysis dict found for grounding (agent=%s)", agent_type)
        return output, 1.0

    # Validate and get grounding score
    from utils.hallucination_guard import validate_insights, ground_insights
    result = validate_insights(insights, analysis_dict)
    grounded = ground_insights(insights, analysis_dict)
    output["insights"] = grounded

    return output, result["grounding_score"]


def validate_dataframe_quality(df: "Any") -> dict[str, Any]:
    """
    Validate the quality of an ingested DataFrame.
    Returns a report with warnings.
    """
    warnings_list: list[str] = []

    if len(df) == 0:
        warnings_list.append("DataFrame is empty (0 rows)")

    if len(df.columns) == 0:
        warnings_list.append("DataFrame has no columns")

    # Check for high null ratio
    for col in df.columns:
        null_ratio = df[col].isnull().mean()
        if null_ratio > 0.5:
            warnings_list.append(f"Column '{col}' has {null_ratio*100:.0f}% null values")

    # Check for duplicate rows
    dup_ratio = df.duplicated().mean()
    if dup_ratio > 0.2:
        warnings_list.append(f"{dup_ratio*100:.0f}% duplicate rows detected")

    # Check for single-value columns (no variance)
    for col in df.select_dtypes(include=["number"]).columns:
        if df[col].nunique() <= 1:
            warnings_list.append(f"Column '{col}' has no variance (single value)")

    return {
        "is_valid": len(warnings_list) == 0,
        "warnings": warnings_list,
        "rows": len(df),
        "columns": len(df.columns),
    }
