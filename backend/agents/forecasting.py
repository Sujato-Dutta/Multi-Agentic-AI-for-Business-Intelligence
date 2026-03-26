"""Demand forecasting agent — trends, seasonality, stockout risk."""

import logging
from typing import Any

import numpy as np
import pandas as pd

from config import FORECAST_DAYS, CONFIDENCE_INTERVAL_MULTIPLIER
from utils.llm import call_llm

logger = logging.getLogger(__name__)


class DemandForecastingAgent:
    """Forecasts demand with trend decomposition, seasonality detection, and stockout risk."""

    def run(self, df: pd.DataFrame, query: str) -> dict[str, Any]:
        logger.info("DemandForecastingAgent: running on %d rows", len(df))
        forecast_data: dict[str, Any] = {}
        seasonal_flags: list[str] = []

        # Find date and demand columns
        date_col = self._find_col(df, ["date", "timestamp", "day"])
        demand_col = self._find_col(df, ["demand", "units_sold", "quantity", "sales"])

        if not date_col or not demand_col:
            logger.warning("Missing date or demand columns, falling back to basic analysis")
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                forecast_data["basic_stats"] = {c: {"mean": round(float(df[c].mean()), 2), "std": round(float(df[c].std()), 2)} for c in numeric_cols[:5]}
            prompt = f"Analyze this data with {len(df)} rows and columns {list(df.columns)} for user question: {query}. Give 3-5 insights."
            raw = call_llm("quantitative", prompt)
            insights = [l.strip().lstrip("•-* ") for l in raw.strip().split("\n") if l.strip() and len(l.strip()) > 5]
            return {"forecast_df": forecast_data, "insights": insights, "seasonal_flags": []}

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        daily = df.sort_values(date_col).groupby(date_col)[demand_col].sum().reset_index()
        values = daily[demand_col].values.astype(float)

        # Rolling average decomposition
        window = min(7, len(values))
        trend = pd.Series(values).rolling(window, min_periods=1).mean().values
        seasonal_component = values - trend
        forecast_data["trend_last_10"] = trend[-10:].round(2).tolist()

        # Polyfit forecast
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, deg=min(2, len(values) - 1))
        poly = np.poly1d(coeffs)
        std = float(np.std(values))

        forecasts = {}
        for days in FORECAST_DAYS:
            future_x = np.arange(len(values), len(values) + days)
            predicted = poly(future_x)
            ci = CONFIDENCE_INTERVAL_MULTIPLIER * std
            forecasts[f"{days}_day"] = {
                "mean_forecast": round(float(predicted.mean()), 2),
                "final_value": round(float(predicted[-1]), 2),
                "confidence_interval": round(ci, 2),
            }
        forecast_data["forecasts"] = forecasts

        # MoM / WoW variance
        if len(daily) >= 14:
            daily["week"] = daily[date_col].dt.isocalendar().week.astype(int)
            weekly_avg = daily.groupby("week")[demand_col].mean()
            wow_var = float(weekly_avg.std() / weekly_avg.mean()) if weekly_avg.mean() != 0 else 0
            forecast_data["wow_variance_pct"] = round(wow_var * 100, 2)
            if wow_var > 0.15:
                seasonal_flags.append("High weekly variance detected — possible strong seasonality")

        if len(daily) >= 60:
            daily["month"] = daily[date_col].dt.month
            monthly_avg = daily.groupby("month")[demand_col].mean()
            mom_var = float(monthly_avg.std() / monthly_avg.mean()) if monthly_avg.mean() != 0 else 0
            forecast_data["mom_variance_pct"] = round(mom_var * 100, 2)
            if mom_var > 0.2:
                seasonal_flags.append("High monthly variance — seasonal demand pattern confirmed")

        # Stockout risk
        if "inventory" in df.columns:
            df_inv = df.copy()
            avg_demand = float(df_inv[demand_col].mean())
            low_inv = df_inv[df_inv["inventory"] < avg_demand * 1.2]
            forecast_data["stockout_risk_days"] = len(low_inv)
            forecast_data["avg_demand"] = round(avg_demand, 2)

        forecast_data["historical_values"] = values[-30:].tolist()
        forecast_data["dates"] = [str(pd.Timestamp(d).date()) for d in daily[date_col].values[-30:]] if len(daily) > 0 else []

        # LLM insights
        summary = "; ".join(f"{k}: {v}" for k, v in forecast_data.items() if not isinstance(v, (dict, list)))
        prompt = (
            f"You are a demand planning expert. Given this forecast analysis:\n{summary}\n"
            f"Seasonal flags: {seasonal_flags}\n"
            f"User question: {query}\n\n"
            f"Generate 3-5 concise demand forecasting insight bullets. Be specific with numbers.\n"
            f"IMPORTANT: Output ONLY the bullet points. Do NOT include any reasoning, thinking, or explanation of your thought process."
        )
        raw = call_llm("quantitative", prompt)
        insights = [l.strip().lstrip("•-* ") for l in raw.strip().split("\n") if l.strip() and len(l.strip()) > 5]

        return {"forecast_df": forecast_data, "insights": insights, "seasonal_flags": seasonal_flags}

    def _find_col(self, df: pd.DataFrame, candidates: list[str]) -> str | None:
        for c in candidates:
            for col in df.columns:
                if c in col.lower():
                    return col
        return None
