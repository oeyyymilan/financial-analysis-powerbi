import pandas as pd
import pytest

from ai_insights.data_loader import load_from_csv
from ai_insights.facts import compute_facts
from ai_insights.formatting import fmt_inr
from ai_insights.summarizer import generate_summary, template_summary
from ai_insights.validator import validate_summary


def small_df():
    rows = [
        # period, year, region, category, type, amount, status
        ("2023-01", 2023, "North", "Product Sales", "Revenue", 1000.0, "Completed"),
        ("2023-02", 2023, "South", "Service Fees", "Revenue", 500.0, "Completed"),
        ("2024-01", 2024, "North", "Product Sales", "Revenue", 1800.0, "Completed"),
        ("2024-01", 2024, "North", "Product Sales", "Revenue", 9999.0, "Failed"),   # must be ignored
        ("2024-01", 2024, "South", "Salaries", "Expense", 600.0, "Completed"),
        ("2023-01", 2023, "South", "Marketing", "Expense", 200.0, "Pending"),      # must be ignored
    ]
    return pd.DataFrame(rows, columns=["period", "year", "region", "category_name",
                                       "category_type", "amount", "status"])


def test_facts_known_values():
    f = compute_facts(small_df())
    assert f["total_revenue"] == 3300.0
    assert f["total_expenses"] == 600.0
    assert f["net_profit"] == 2700.0
    assert f["yoy_growth_pct"] == pytest.approx((1800 / 1500 - 1) * 100)
    assert f["top_revenue_category"] == "Product Sales"
    assert f["best_month"] == "2024-01" and f["worst_month"] == "2023-02"


def test_facts_rejects_missing_columns():
    with pytest.raises(ValueError):
        compute_facts(small_df().drop(columns=["status"]))


def test_facts_requires_revenue():
    df = small_df()
    df = df[df["category_type"] == "Expense"]
    with pytest.raises(ValueError):
        compute_facts(df)


def test_real_dataset_matches_dashboard():
    f = compute_facts(load_from_csv())
    assert f["total_revenue"] == pytest.approx(17_774_193, rel=1e-4)
    assert f["profit_margin_pct"] == pytest.approx(35.5, abs=0.1)


def test_template_passes_validator():
    f = compute_facts(load_from_csv())
    assert validate_summary(template_summary(f), f).ok


def test_validator_accepts_correct_numbers():
    f = compute_facts(load_from_csv())
    text = "Revenue was ₹1.78 crore with a 35.5% margin and 19.0% growth in 2024."
    assert validate_summary(text, f).ok


def test_validator_rejects_invented_numbers():
    f = compute_facts(load_from_csv())
    bad = validate_summary("Revenue was ₹2.50 crore and margin hit 80.0%.", f)
    assert not bad.ok and len(bad.issues) == 2


def test_validator_rejects_unknown_month():
    f = compute_facts(load_from_csv())
    assert not validate_summary("Sales peaked in 2024-07.", f).ok


def test_pipeline_rejects_hallucinating_llm():
    f = compute_facts(load_from_csv())
    out = generate_summary(f, llm=lambda prompt: "Revenue exploded to ₹9.99 crore!")
    assert out["source"] == "template (LLM output rejected)"
    assert out["issues"]


def test_pipeline_accepts_faithful_llm():
    f = compute_facts(load_from_csv())
    out = generate_summary(f, llm=lambda prompt: "Net profit stood at ₹63.13 lakh, a 35.5% margin.")
    assert out["source"] == "llm"


def test_pipeline_survives_llm_failure():
    f = compute_facts(load_from_csv())

    def boom(prompt):
        raise TimeoutError("no network")

    out = generate_summary(f, llm=boom)
    assert out["source"].startswith("template") and out["validated"]


def test_fmt_inr():
    assert fmt_inr(17_774_193) == "₹1.78 crore"
    assert fmt_inr(6_312_819) == "₹63.13 lakh"
    assert fmt_inr(950) == "₹950"
