"""CLI:  python -m ai_insights.run [--source csv|mysql]"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from .data_loader import load
from .facts import compute_facts
from .summarizer import generate_summary

OUT_DIR = Path(__file__).resolve().parent / "output"


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description="AI-generated executive summary of the financial data")
    ap.add_argument("--source", choices=["csv", "mysql"], default="csv")
    args = ap.parse_args(argv)

    facts = compute_facts(load(args.source))
    result = generate_summary(facts)
    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    (OUT_DIR / "executive_summary.md").write_text(
        f"# Executive Summary\n\n{result['summary']}\n\n_Generated {stamp} | source: {result['source']}_\n",
        encoding="utf-8")
    with open(OUT_DIR / "executive_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["generated_at", "source", "validated", "summary"])
        w.writerow([stamp, result["source"], result["validated"], result["summary"]])

    print(result["summary"])
    print(f"\n[source: {result['source']}]")
    for issue in result["issues"]:
        print(f"[note] {issue}")
    return result


if __name__ == "__main__":
    main()
