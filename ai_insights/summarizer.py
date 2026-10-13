"""Executive-summary generation: LLM first, validated, with a safe template fallback."""
from __future__ import annotations

import os
from typing import Callable

import requests

from .formatting import fmt_inr, fmt_pct
from .validator import validate_summary

DEFAULT_MODEL = "gemini-2.5-flash"  # override with GEMINI_MODEL if Google renames it


def template_summary(f: dict) -> str:
    """Deterministic summary. Built only from verified facts, so it always passes validation."""
    parts = [
        f"Between {f['previous_year'] or f['latest_year']} and {f['latest_year']}, the business earned "
        f"{fmt_inr(f['total_revenue'])} in revenue against {fmt_inr(f['total_expenses'])} in expenses, "
        f"leaving a net profit of {fmt_inr(f['net_profit'])} ({fmt_pct(f['profit_margin_pct'])} margin)."
    ]
    if f.get("yoy_growth_pct") is not None:
        direction = "grew" if f["yoy_growth_pct"] >= 0 else "fell"
        parts.append(f"Revenue {direction} {fmt_pct(abs(f['yoy_growth_pct']))} in {f['latest_year']} compared with {f['previous_year']}.")
    parts.append(
        f"{f['top_revenue_category']} is the largest revenue source ({fmt_pct(f['top_revenue_category_pct'])}), "
        f"and the {f['top_region']} region contributes the most ({fmt_pct(f['top_region_pct'])})."
    )
    parts.append(f"{f['top_expense_category']} is the biggest cost at {fmt_pct(f['top_expense_category_pct'])} of expenses.")
    parts.append(f"Revenue peaked in {f['best_month']} and was lowest in {f['worst_month']}.")
    return " ".join(parts)


def build_prompt(f: dict) -> str:
    facts = {
        "Total revenue": fmt_inr(f["total_revenue"]),
        "Total expenses": fmt_inr(f["total_expenses"]),
        "Net profit": fmt_inr(f["net_profit"]),
        "Profit margin": fmt_pct(f["profit_margin_pct"]),
        "Revenue growth, latest year vs previous": fmt_pct(f["yoy_growth_pct"]) if f["yoy_growth_pct"] is not None else "n/a",
        "Largest revenue category": f"{f['top_revenue_category']} ({fmt_pct(f['top_revenue_category_pct'])} of revenue)",
        "Largest region": f"{f['top_region']} ({fmt_pct(f['top_region_pct'])} of revenue)",
        "Largest expense": f"{f['top_expense_category']} ({fmt_pct(f['top_expense_category_pct'])} of expenses)",
        "Best month": f["best_month"],
        "Weakest month": f["worst_month"],
    }
    lines = "\n".join(f"- {k}: {v}" for k, v in facts.items())
    return (
        "You are a financial analyst writing for a business manager.\n"
        "Write a 4-5 sentence executive summary using ONLY the facts below.\n"
        "Copy every number exactly as written. Do not add any other numbers, "
        "forecasts or causes. Plain English, no bullet points.\n\n" + lines
    )


def call_gemini(prompt: str, api_key: str, model: str | None = None, timeout: int = 30) -> str:
    model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    resp = requests.post(url, params={"key": api_key}, timeout=timeout,
                         json={"contents": [{"parts": [{"text": prompt}]}]})
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def generate_summary(facts: dict, llm: Callable[[str], str] | None = None) -> dict:
    """Return {summary, source, validated, issues}. Never returns unvalidated AI text."""
    fallback = template_summary(facts)
    if llm is None:
        key = os.getenv("GEMINI_API_KEY")
        if key:
            llm = lambda p: call_gemini(p, key)  # noqa: E731
    if llm is None:
        return {"summary": fallback, "source": "template", "validated": True, "issues": []}

    try:
        text = llm(build_prompt(facts))
    except Exception as exc:  # network, quota, bad response ...
        return {"summary": fallback, "source": "template (LLM unavailable)", "validated": True,
                "issues": [f"LLM call failed: {type(exc).__name__}"]}

    result = validate_summary(text, facts)
    if result.ok:
        return {"summary": text, "source": "llm", "validated": True, "issues": []}
    return {"summary": fallback, "source": "template (LLM output rejected)", "validated": True, "issues": result.issues}
