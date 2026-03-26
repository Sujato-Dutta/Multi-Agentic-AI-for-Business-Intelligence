"""Dynamic pricing agent — elasticity, margins, competitor gaps, discount simulation."""

import logging
from typing import Any

import numpy as np
import pandas as pd

from config import DISCOUNT_SCENARIOS
from utils.llm import call_llm

logger = logging.getLogger(__name__)


class DynamicPricingAgent:
    """Analyzes pricing dynamics including elasticity, margins, and discount scenarios."""

    def run(self, df: pd.DataFrame, query: str) -> dict[str, Any]:
        logger.info("DynamicPricingAgent: running on %d rows", len(df))
        pricing_analysis: dict[str, Any] = {}
        simulation_table: list[dict] = []

        # Price elasticity
        if "price" in df.columns and "units_sold" in df.columns:
            corr = df["price"].corr(df["units_sold"])
            pricing_analysis["price_elasticity_correlation"] = round(float(corr), 4)
            avg_price = float(df["price"].mean())
            avg_units = float(df["units_sold"].mean())
            elasticity = (corr * avg_price / avg_units) if avg_units != 0 else 0
            pricing_analysis["elasticity_estimate"] = round(elasticity, 4)
            pricing_analysis["optimal_price"] = round(avg_price * (1 + 1 / abs(elasticity)) if abs(elasticity) > 0.01 else avg_price, 2)
        else:
            logger.warning("Missing 'price' or 'units_sold' columns for elasticity")

        # Margin analysis
        if "revenue" in df.columns and "cost" in df.columns:
            df = df.copy()
            df["margin"] = (df["revenue"] - df["cost"]) / df["revenue"]
            pricing_analysis["avg_margin"] = round(float(df["margin"].mean()), 4)
            if "product" in df.columns:
                margin_by_seg = df.groupby("product")["margin"].mean().round(4).to_dict()
                pricing_analysis["margin_by_segment"] = margin_by_seg
        else:
            logger.warning("Missing 'revenue' or 'cost' columns for margin analysis")

        # Competitor gap
        if "price" in df.columns and "competitor_price" in df.columns:
            df_c = df.copy()
            df_c["price_gap"] = df_c["price"] - df_c["competitor_price"]
            df_c["gap_pct"] = ((df_c["price_gap"] / df_c["competitor_price"]) * 100).round(2)
            pricing_analysis["avg_competitor_gap_pct"] = round(float(df_c["gap_pct"].mean()), 2)
        else:
            logger.warning("Missing 'competitor_price' column for gap analysis")

        # Discount simulation
        if "price" in df.columns and "units_sold" in df.columns:
            base_rev = float((df["price"] * df["units_sold"]).sum())
            for disc in DISCOUNT_SCENARIOS:
                new_price = df["price"] * (1 - disc)
                lift = 1 + disc * 2
                new_units = df["units_sold"] * lift
                new_rev = float((new_price * new_units).sum())
                simulation_table.append({
                    "discount_pct": f"{int(disc * 100)}%",
                    "base_revenue": round(base_rev, 2),
                    "simulated_revenue": round(new_rev, 2),
                    "revenue_change_pct": round((new_rev - base_rev) / base_rev * 100, 2),
                })
            pricing_analysis["discount_simulation"] = simulation_table

        # LLM recommendations
        summary = "; ".join(f"{k}: {v}" for k, v in pricing_analysis.items() if not isinstance(v, (dict, list)))
        prompt = (
            f"You are a pricing strategist. Given this analysis:\n{summary}\n"
            f"User question: {query}\n\n"
            f"Generate 3-5 concise pricing recommendation bullets. Be specific with numbers.\n"
            f"IMPORTANT: Output ONLY the bullet points. Do NOT include any reasoning, thinking, or explanation of your thought process."
        )
        raw = call_llm("quantitative", prompt)
        recommendations = [line.strip().lstrip("•-* ") for line in raw.strip().split("\n") if line.strip() and len(line.strip()) > 5]

        return {
            "pricing_analysis": pricing_analysis,
            "recommendations": recommendations,
            "simulation_table": simulation_table,
            "insights": recommendations,
        }
