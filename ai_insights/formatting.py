"""Indian-style number formatting (crore / lakh)."""
from __future__ import annotations

CRORE, LAKH = 10_000_000, 100_000


def fmt_inr(x: float) -> str:
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= CRORE:
        return f"{sign}₹{x / CRORE:.2f} crore"
    if x >= LAKH:
        return f"{sign}₹{x / LAKH:.2f} lakh"
    return f"{sign}₹{x:,.0f}"


def fmt_pct(x: float) -> str:
    return f"{x:.1f}%"
