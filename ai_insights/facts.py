"""Compute the verified numbers (facts) that the summary is allowed to talk about."""
from __future__ import annotations

import pandas as pd

REQUIRED = {"period", "year", "region", "category_name", "category_type", "amount", "status"}


def compute_facts(df: pd.DataFrame) -> dict:
    """Return headline KPIs. Only 'Completed' transactions count, matching the DAX measures."""
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    ok = df[df["status"] == "Completed"]
    rev = ok[ok["category_type"] == "Revenue"]
    exp = ok[ok["category_type"] == "Expense"]
    if rev.empty:
        raise ValueError("No completed revenue transactions found")

    total_rev, total_exp = float(rev["amount"].sum()), float(exp["amount"].sum())
    net = total_rev - total_exp

    by_year = rev.groupby("year")["amount"].sum()
    years = sorted(by_year.index)
    yoy = None
    if len(years) >= 2 and by_year[years[-2]] > 0:
        yoy = (by_year[years[-1]] / by_year[years[-2]] - 1) * 100

    def top_share(frame: pd.DataFrame, col: str, total: float) -> tuple[str, float]:
        s = frame.groupby(col)["amount"].sum().sort_values(ascending=False)
        return str(s.index[0]), float(s.iloc[0] / total * 100)

    top_cat, top_cat_pct = top_share(rev, "category_name", total_rev)
    top_reg, top_reg_pct = top_share(rev, "region", total_rev)
    top_exp, top_exp_pct = top_share(exp, "category_name", total_exp) if total_exp > 0 else ("n/a", 0.0)

    monthly = rev.groupby("period")["amount"].sum()
    return {
        "total_revenue": total_rev,
        "total_expenses": total_exp,
        "net_profit": net,
        "profit_margin_pct": net / total_rev * 100,
        "yoy_growth_pct": yoy,
        "latest_year": int(years[-1]),
        "previous_year": int(years[-2]) if len(years) >= 2 else None,
        "top_revenue_category": top_cat,
        "top_revenue_category_pct": top_cat_pct,
        "top_region": top_reg,
        "top_region_pct": top_reg_pct,
        "top_expense_category": top_exp,
        "top_expense_category_pct": top_exp_pct,
        "best_month": str(monthly.idxmax()),
        "worst_month": str(monthly.idxmin()),
    }
