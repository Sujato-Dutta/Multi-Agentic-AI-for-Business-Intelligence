"""Employee churn agent — churn rates, satisfaction segmentation, risk flags."""

import logging
from typing import Any

import numpy as np
import pandas as pd

from config import (
    CHURN_SATISFACTION_THRESHOLD_LOW,
    CHURN_SATISFACTION_THRESHOLD_HIGH,
    CHURN_RETENTION_COST_MULTIPLIER,
)
from utils.llm import call_llm

logger = logging.getLogger(__name__)


class EmployeeChurnAgent:
    """Analyzes employee churn risk with satisfaction segmentation and retention costing."""

    def run(self, df: pd.DataFrame, query: str) -> dict[str, Any]:
        logger.info("EmployeeChurnAgent: running on %d rows", len(df))
        churn_analysis: dict[str, Any] = {}
        risk_flags: list[dict] = []

        # Churn rate by department
        if "department" in df.columns and "churned" in df.columns:
            churn_by_dept = df.groupby("department")["churned"].mean().round(4).to_dict()
            churn_analysis["churn_rate_by_department"] = churn_by_dept
            churn_analysis["overall_churn_rate"] = round(float(df["churned"].mean()), 4)
        elif "department" in df.columns and "attrition_risk" in df.columns:
            risk_map = {"High": 1, "Medium": 0.5, "Low": 0}
            df = df.copy()
            df["churn_score"] = df["attrition_risk"].map(risk_map).fillna(0)
            churn_by_dept = df.groupby("department")["churn_score"].mean().round(4).to_dict()
            churn_analysis["churn_rate_by_department"] = churn_by_dept
        else:
            logger.warning("Missing 'department'/'churned' columns for churn rate")

        # Satisfaction segmentation
        sat_col = None
        for candidate in ["satisfaction_score", "satisfaction"]:
            if candidate in df.columns:
                sat_col = candidate
                break
        if sat_col:
            low = int((df[sat_col] < CHURN_SATISFACTION_THRESHOLD_LOW).sum())
            mid = int(((df[sat_col] >= CHURN_SATISFACTION_THRESHOLD_LOW) &
                       (df[sat_col] < CHURN_SATISFACTION_THRESHOLD_HIGH)).sum())
            high = int((df[sat_col] >= CHURN_SATISFACTION_THRESHOLD_HIGH).sum())
            churn_analysis["satisfaction_segments"] = {
                f"low (<{CHURN_SATISFACTION_THRESHOLD_LOW})": low,
                f"medium ({CHURN_SATISFACTION_THRESHOLD_LOW}-{CHURN_SATISFACTION_THRESHOLD_HIGH})": mid,
                f"high (>={CHURN_SATISFACTION_THRESHOLD_HIGH})": high,
            }
        else:
            logger.warning("Missing satisfaction score column")

        # Risk flagging: low satisfaction + high tenure
        if sat_col and "tenure_years" in df.columns:
            at_risk = df[(df[sat_col] < CHURN_SATISFACTION_THRESHOLD_LOW) &
                         (df["tenure_years"] > df["tenure_years"].median())]
            risk_flags = at_risk[["employee_id", "department", sat_col, "tenure_years"]].head(20).to_dict("records") if "employee_id" in df.columns else []
            churn_analysis["high_risk_count"] = len(at_risk)

        # Retention cost
        if "salary" in df.columns:
            avg_salary = float(df["salary"].mean())
            predicted_churners = churn_analysis.get("high_risk_count", int(len(df) * 0.1))
            retention_cost = round(avg_salary * CHURN_RETENTION_COST_MULTIPLIER * predicted_churners, 2)
            churn_analysis["estimated_retention_cost"] = retention_cost
            churn_analysis["avg_salary"] = round(avg_salary, 2)

        # Correlation with churn
        if "churned" in df.columns:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if "churned" in numeric_cols:
                corrs = df[numeric_cols].corr()["churned"].drop("churned").round(4).to_dict()
                churn_analysis["feature_correlations"] = corrs

        # LLM insights
        summary = "; ".join(f"{k}: {v}" for k, v in churn_analysis.items() if not isinstance(v, (dict, list)))
        prompt = (
            f"You are an HR analytics expert. Given this churn analysis:\n{summary}\n"
            f"Segments: {churn_analysis.get('satisfaction_segments', 'N/A')}\n"
            f"User question: {query}\n\n"
            f"Generate 3-5 concise HR insight bullets + retention recommendations. Be specific.\n"
            f"IMPORTANT: Output ONLY the bullet points. Do NOT include any reasoning, thinking, or explanation of your thought process."
        )
        raw = call_llm("heavy_logic", prompt)
        insights = [line.strip().lstrip("•-* ") for line in raw.strip().split("\n") if line.strip() and len(line.strip()) > 5]

        return {"churn_analysis": churn_analysis, "risk_flags": risk_flags, "insights": insights}
