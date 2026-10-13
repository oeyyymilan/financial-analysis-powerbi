"""Load transaction data from the CSV files or from the MySQL view."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["period", "year", "region", "category_name", "category_type", "amount", "status"]


def load_from_csv(data_dir: Path | str = ROOT / "data") -> pd.DataFrame:
    """Join the star-schema CSVs into one flat frame (same shape as vw_transactions)."""
    data_dir = Path(data_dir)
    fact = pd.read_csv(data_dir / "fact_transactions.csv")
    cat = pd.read_csv(data_dir / "dim_category.csv")
    date = pd.read_csv(data_dir / "dim_date.csv")[["date_key", "year", "period"]]
    df = fact.merge(cat, on="category_id", how="left").merge(date, on="date_key", how="left")
    return df[COLUMNS].copy()


def load_from_mysql() -> pd.DataFrame:
    """Read vw_transactions. Connection settings come from environment variables."""
    import pymysql  # imported lazily so CSV mode needs no database driver

    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DB", "financial_analysis"),
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {', '.join(COLUMNS)} FROM vw_transactions")
            rows = cur.fetchall()
    finally:
        conn.close()
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["amount"] = df["amount"].astype(float)
    return df


def load(source: str = "csv") -> pd.DataFrame:
    if source == "csv":
        return load_from_csv()
    if source == "mysql":
        return load_from_mysql()
    raise ValueError(f"Unknown source '{source}' (use 'csv' or 'mysql')")
