"""Smart column mapper — fuzzy-matches user column names to expected agent schemas."""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ─── Synonym registry ──────────────────────────────────────────────
# Each key is the canonical column name the agent expects.
# Values are a list of substrings/synonyms that should match.

PRICING_SCHEMA: dict[str, list[str]] = {
    "price":            ["price", "unit_price", "selling_price", "item_price", "cost_per_unit", "mrp", "rate"],
    "units_sold":       ["units_sold", "qty_sold", "quantity_sold", "volume", "qty", "units", "quantity"],
    "revenue":          ["revenue", "sales_amount", "total_sales", "income", "turnover", "gross_sales"],
    "cost":             ["cost", "cogs", "unit_cost", "production_cost", "expense", "total_cost"],
    "competitor_price": ["competitor_price", "comp_price", "rival_price", "market_price", "benchmark_price"],
    "product":          ["product", "item", "sku", "product_name", "item_name", "category"],
}

CHURN_SCHEMA: dict[str, list[str]] = {
    "department":         ["department", "dept", "division", "team", "business_unit", "org_unit"],
    "churned":            ["churned", "attrition", "left", "resigned", "terminated", "turnover", "is_churned"],
    "satisfaction_score": ["satisfaction_score", "satisfaction", "sat_score", "happiness", "engagement", "nps",
                           "employee_satisfaction", "job_satisfaction"],
    "tenure_years":       ["tenure_years", "tenure", "years_at_company", "experience", "service_years",
                           "years_employed", "employment_duration"],
    "salary":             ["salary", "compensation", "pay", "wage", "annual_salary", "monthly_salary", "income"],
    "employee_id":        ["employee_id", "emp_id", "id", "staff_id", "worker_id"],
    "attrition_risk":     ["attrition_risk", "risk_level", "churn_risk", "risk_score", "flight_risk"],
}

FORECASTING_SCHEMA: dict[str, list[str]] = {
    "date":      ["date", "timestamp", "day", "datetime", "period", "time", "order_date", "transaction_date"],
    "demand":    ["demand", "units_sold", "quantity", "sales", "volume", "orders", "qty", "units", "consumption"],
    "inventory": ["inventory", "stock", "stock_level", "on_hand", "available", "warehouse_qty"],
}

AGENT_SCHEMAS: dict[str, dict[str, list[str]]] = {
    "pricing":     PRICING_SCHEMA,
    "churn":       CHURN_SCHEMA,
    "forecasting": FORECASTING_SCHEMA,
}

# Minimum number of key columns that must match for a specialist to be viable
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "pricing":     ["price"],                  # At minimum need a price column
    "churn":       ["department"],             # At minimum need department
    "forecasting": ["date", "demand"],         # Need both date and demand columns
}


def _normalize(name: str) -> str:
    """Lowercase, strip whitespace, replace spaces/hyphens with underscores."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def map_columns(df: pd.DataFrame, agent_type: str) -> tuple[pd.DataFrame, dict[str, str], float]:
    """
    Attempt to map DataFrame columns to the expected schema for a specialist agent.

    Returns:
        - df_mapped: DataFrame with columns renamed to canonical names
        - mapping: dict of {canonical_name: original_column_name} for columns that matched
        - confidence: float 0.0-1.0 representing how many schema columns were matched
    """
    schema = AGENT_SCHEMAS.get(agent_type)
    if not schema:
        return df, {}, 0.0

    normalized_cols = {_normalize(col): col for col in df.columns}
    mapping: dict[str, str] = {}  # canonical -> original

    for canonical, synonyms in schema.items():
        # 1. Exact match on original column names (case-insensitive)
        matched = False
        for col_norm, col_orig in normalized_cols.items():
            if col_norm == canonical:
                mapping[canonical] = col_orig
                matched = True
                break

        if matched:
            continue

        # 2. Synonym substring matching
        for col_norm, col_orig in normalized_cols.items():
            if col_orig in mapping.values():
                continue  # Already mapped
            for synonym in synonyms:
                syn_norm = _normalize(synonym)
                if syn_norm == col_norm or syn_norm in col_norm or col_norm in syn_norm:
                    mapping[canonical] = col_orig
                    matched = True
                    break
            if matched:
                break

    # Calculate confidence
    confidence = len(mapping) / len(schema) if schema else 0.0

    # Rename columns
    if mapping:
        rename_map = {orig: canonical for canonical, orig in mapping.items()}
        df_mapped = df.rename(columns=rename_map)
        logger.info(
            "Column mapper [%s]: mapped %d/%d columns (%.0f%% confidence). Mapping: %s",
            agent_type, len(mapping), len(schema), confidence * 100, mapping
        )
    else:
        df_mapped = df
        logger.warning("Column mapper [%s]: no columns matched", agent_type)

    return df_mapped, mapping, confidence


def check_specialist_viable(df: pd.DataFrame, agent_type: str) -> tuple[bool, float, dict[str, str]]:
    """
    Check if a specialist agent is viable for the given DataFrame.

    Returns:
        - viable: bool — True if enough required columns are present
        - confidence: float 0.0-1.0
        - mapping: the column mapping dict
    """
    _, mapping, confidence = map_columns(df, agent_type)

    required = REQUIRED_COLUMNS.get(agent_type, [])
    if not required:
        return True, confidence, mapping

    has_required = all(col in mapping for col in required)

    if not has_required:
        missing = [col for col in required if col not in mapping]
        logger.warning(
            "Specialist [%s] not viable: missing required columns %s. Available: %s",
            agent_type, missing, list(df.columns)
        )

    return has_required, confidence, mapping
