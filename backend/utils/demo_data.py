"""Seeded demo dataset generators for all 6 built-in datasets."""

import numpy as np
import pandas as pd

from config import DEMO_DATASETS

_RNG = np.random.RandomState(42)


def _sales() -> pd.DataFrame:
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    regions = _RNG.choice(["North", "South", "East", "West"], n)
    products = _RNG.choice(["Widget A", "Widget B", "Widget C", "Gadget X"], n)
    units = _RNG.randint(10, 500, n)
    price = _RNG.uniform(5, 50, n).round(2)
    revenue = (units * price).round(2)
    cost = (revenue * _RNG.uniform(0.4, 0.75, n)).round(2)
    return pd.DataFrame({
        "date": dates, "region": regions, "product": products,
        "revenue": revenue, "units_sold": units, "cost": cost,
    })


def _hr() -> pd.DataFrame:
    n = 200
    departments = _RNG.choice(["Engineering", "Sales", "Marketing", "HR", "Finance", "Support"], n)
    tenure = _RNG.uniform(0.5, 15, n).round(1)
    satisfaction = _RNG.uniform(1, 5, n).round(1)
    salary = _RNG.randint(35000, 120000, n)
    churned = (_RNG.random(n) < (0.6 - satisfaction / 10)).astype(int)
    return pd.DataFrame({
        "employee_id": range(1, n + 1), "department": departments,
        "tenure_years": tenure, "satisfaction_score": satisfaction,
        "salary": salary, "churned": churned,
    })


def _marketing() -> pd.DataFrame:
    n = 30
    channels = _RNG.choice(["Google Ads", "Facebook", "LinkedIn", "Email", "SEO", "Referral"], n)
    spend = _RNG.randint(500, 20000, n)
    leads = (spend * _RNG.uniform(0.01, 0.08, n)).astype(int)
    conversions = (leads * _RNG.uniform(0.05, 0.3, n)).astype(int)
    cac = np.where(conversions > 0, (spend / conversions).round(2), 0)
    return pd.DataFrame({
        "channel": channels, "spend": spend, "leads": leads,
        "conversions": conversions, "cac": cac,
    })


def _pricing() -> pd.DataFrame:
    n = 50
    products = _RNG.choice(["Pro Plan", "Basic Plan", "Enterprise", "Starter", "Premium"], n)
    price = _RNG.uniform(10, 200, n).round(2)
    competitor_price = (price * _RNG.uniform(0.8, 1.3, n)).round(2)
    units = _RNG.randint(20, 1000, n)
    cost = (price * _RNG.uniform(0.3, 0.6, n) * units).round(2)
    revenue = (price * units).round(2)
    return pd.DataFrame({
        "product": products, "price": price,
        "competitor_price": competitor_price, "units_sold": units,
        "cost": cost, "revenue": revenue,
    })


def _demand() -> pd.DataFrame:
    n = 365
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    products = _RNG.choice(["SKU-001", "SKU-002", "SKU-003"], n)
    day_idx = np.arange(n)
    base = 100 + 0.15 * day_idx
    seasonal = 30 * np.sin(2 * np.pi * day_idx / 365)
    noise = _RNG.normal(0, 10, n)
    demand = (base + seasonal + noise).clip(10).astype(int)
    inventory = (demand * _RNG.uniform(0.8, 1.5, n)).astype(int)
    price = _RNG.uniform(8, 25, n).round(2)
    return pd.DataFrame({
        "date": dates, "product": products, "demand": demand,
        "inventory": inventory, "price": price,
    })


def _employee_satisfaction() -> pd.DataFrame:
    n = 150
    departments = _RNG.choice(["Engineering", "Sales", "Marketing", "HR", "Operations"], n)
    manager = _RNG.uniform(1, 5, n).round(1)
    workload = _RNG.uniform(1, 5, n).round(1)
    satisfaction = ((manager * 0.4 + (6 - workload) * 0.3 + _RNG.normal(0, 0.5, n))).clip(1, 5).round(1)
    risk = np.where(satisfaction < 2.5, "High", np.where(satisfaction < 3.5, "Medium", "Low"))
    return pd.DataFrame({
        "employee_id": range(1, n + 1), "department": departments,
        "manager_score": manager, "workload_score": workload,
        "satisfaction_score": satisfaction, "attrition_risk": risk,
    })


_GENERATORS = {
    "Sales": _sales,
    "HR": _hr,
    "Marketing": _marketing,
    "Pricing": _pricing,
    "Demand": _demand,
    "Employee Satisfaction": _employee_satisfaction,
}


def get_demo_dataset(name: str) -> pd.DataFrame:
    """Return a demo DataFrame by name. Names must match DEMO_DATASETS."""
    gen = _GENERATORS.get(name)
    if gen is None:
        raise ValueError(f"Unknown demo dataset '{name}'. Choose from: {DEMO_DATASETS}")
    return gen()
