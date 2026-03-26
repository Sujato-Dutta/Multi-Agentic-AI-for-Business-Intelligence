"""General analysis agent — stats, correlations, trends, anomalies."""

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from config import ZSCORE_THRESHOLD, TOP_N_DEFAULT
from utils.llm import call_llm

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """Performs general statistical analysis with anomaly detection."""

    def run(self, df: pd.DataFrame, query: str) -> dict[str, Any]:
        logger.info("AnalysisAgent: running on %d rows", len(df))
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        analysis: dict[str, Any] = {}

        # Summary stats
        if numeric_cols:
            analysis["summary_stats"] = df[numeric_cols].describe().to_dict()

        # Correlation matrix
        if len(numeric_cols) > 2:
            analysis["correlation"] = df[numeric_cols].corr().to_dict()

        # Rolling mean trend on date columns
        date_cols = df.select_dtypes(include=["datetime64", "datetime64[ns]"]).columns.tolist()
        if not date_cols:
            for col in df.columns:
                if "date" in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col])
                        date_cols.append(col)
                    except Exception:
                        pass
        if date_cols and numeric_cols:
            date_col = date_cols[0]
            val_col = numeric_cols[0]
            sorted_df = df.sort_values(date_col)
            analysis["trend"] = {
                "date_column": date_col,
                "value_column": val_col,
                "rolling_mean": sorted_df[val_col].rolling(7, min_periods=1).mean().tolist()[-10:],
            }

        # Top N ranking
        if numeric_cols:
            rank_col = numeric_cols[0]
            top = df.nlargest(TOP_N_DEFAULT, rank_col)
            analysis["top_n"] = {"column": rank_col, "values": top[rank_col].tolist()}

        # Anomaly flagging via z-score
        anomaly_flags: list[dict] = []
        for col in numeric_cols:
            z = np.abs(stats.zscore(df[col].dropna()))
            anomaly_idx = np.where(z > ZSCORE_THRESHOLD)[0]
            if len(anomaly_idx) > 0:
                anomaly_flags.append({
                    "column": col,
                    "count": int(len(anomaly_idx)),
                    "threshold": ZSCORE_THRESHOLD,
                })
        analysis["anomalies"] = anomaly_flags

        # LLM insights
        stats_summary = "; ".join(
            f"{c}: mean={df[c].mean():.2f}, std={df[c].std():.2f}" for c in numeric_cols[:5]
        ) if numeric_cols else "No numeric columns"
        prompt = (
            f"You are a business intelligence analyst. Given this data summary:\n"
            f"Columns: {list(df.columns)}\nRows: {len(df)}\n"
            f"Stats: {stats_summary}\n"
            f"Anomalies found: {len(anomaly_flags)} columns with outliers\n"
            f"User question: {query}\n\n"
            f"Generate 3-5 concise bullet-point insights. Be specific with numbers.\n"
            f"IMPORTANT: Output ONLY the bullet points. Do NOT include any reasoning, thinking, or explanation of your thought process."
        )
        raw = call_llm("fast", prompt)
        insights = [line.strip().lstrip("•-* ") for line in raw.strip().split("\n") if line.strip() and len(line.strip()) > 5]

        return {"insights": insights, "analysis_dict": analysis, "anomaly_flags": anomaly_flags}
