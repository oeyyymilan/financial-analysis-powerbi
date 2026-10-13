"""Check AI-written text: every number it contains must match a verified fact.

This does not prove the *claims* are right (e.g. "grew" vs "fell"); it guarantees
the figures were not invented. Anything that fails is rejected by the pipeline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .formatting import CRORE, LAKH

MONTH_LABEL = re.compile(r"\b\d{4}-\d{2}\b")
NUMBER = re.compile(r"(₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(%|crore|cr\b|lakhs?)?", re.IGNORECASE)
NUMERIC_FACTS = {
    "total_revenue": "inr", "total_expenses": "inr", "net_profit": "inr",
    "profit_margin_pct": "pct", "yoy_growth_pct": "pct", "top_revenue_category_pct": "pct",
    "top_region_pct": "pct", "top_expense_category_pct": "pct",
}


@dataclass
class ValidationResult:
    ok: bool
    issues: list[str] = field(default_factory=list)


def _decimals(num_text: str) -> int:
    return len(num_text.split(".")[1]) if "." in num_text else 0


def _matches(value: float, decimals: int, fact: float) -> bool:
    return abs(round(fact, decimals) - value) < 1e-9


def validate_summary(text: str, facts: dict) -> ValidationResult:
    issues: list[str] = []
    years = {str(y) for y in (facts.get("latest_year"), facts.get("previous_year")) if y}
    cleaned = MONTH_LABEL.sub(" ", text)  # month labels like 2023-12 are checked below

    for label in MONTH_LABEL.findall(text):
        if label not in (facts.get("best_month"), facts.get("worst_month")):
            issues.append(f"Unknown month label: {label}")

    for m in NUMBER.finditer(cleaned):
        rupee, raw, unit = m.group(1), m.group(2), (m.group(3) or "").lower()
        if raw in years and not rupee and not unit:
            continue  # a plain year such as 2024
        value, dec = float(raw.replace(",", "")), _decimals(raw)
        shown = m.group(0).strip()

        if unit == "%":
            ok = any(_matches(value, dec, facts[k]) for k, kind in NUMERIC_FACTS.items()
                     if kind == "pct" and facts.get(k) is not None)
        elif unit in ("crore", "cr"):
            ok = any(_matches(value, dec, abs(facts[k]) / CRORE) for k, kind in NUMERIC_FACTS.items() if kind == "inr")
        elif unit.startswith("lakh"):
            ok = any(_matches(value, dec, abs(facts[k]) / LAKH) for k, kind in NUMERIC_FACTS.items() if kind == "inr")
        else:
            ok = any(_matches(value, dec, abs(facts[k])) for k, kind in NUMERIC_FACTS.items()
                     if kind == "inr" and facts.get(k) is not None)
        if not ok:
            issues.append(f"Number not backed by data: '{shown}'")
    return ValidationResult(ok=not issues, issues=issues)
