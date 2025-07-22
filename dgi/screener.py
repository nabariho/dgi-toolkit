# screener.py

import pandas as pd
from pandas import DataFrame

# from typing import Any  # Remove unused import


def load_universe(csv_path: str = "data/fundamentals_small.csv") -> DataFrame:
    """
    Load the raw fundamentals universe for dividend growth investing analysis.

    Business use:
    This function ingests a CSV of stock fundamentals (including yield, payout,
    and dividend CAGR) into a DataFrame for further screening and analysis. It
    ensures all columns are loaded with the correct types, providing a reliable
    starting point for building DGI watchlists and running filters.

    Expects columns: symbol, name, sector, industry, dividend_yield, payout,
    dividend_cagr, fcf_yield
    Raises ValueError if any required columns are missing.
    """
    required_columns = [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    dtype = {
        col: (
            "float64"
            if col in {"dividend_yield", "payout", "dividend_cagr", "fcf_yield"}
            else "str"
        )
        for col in required_columns
    }
    df = pd.read_csv(csv_path, dtype=dtype)  # type: ignore[arg-type]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")
    return df


def apply_filters(
    df: DataFrame,
    min_yield: float = 0.0,
    max_payout: float = 100.0,
    min_cagr: float = 0.0,
) -> DataFrame:
    """
    Filter stocks by key dividend growth criteria for DGI portfolio selection.

    Business use:
    This function screens the universe for stocks that meet minimum yield,
    maximum payout ratio, and minimum dividend CAGR requirements. It helps
    analysts and investors quickly narrow down to candidates that fit a DGI
    strategy, supporting repeatable, rules-based watchlist construction.
    """
    filtered = df[
        (df["dividend_yield"] >= min_yield)
        & (df["payout"] <= max_payout)
        & (df["dividend_cagr"] >= min_cagr)
    ]
    return filtered


def score(row: pd.Series) -> float:  # type: ignore[type-arg]
    """
    Calculate a composite score for DGI stock quality based on growth, payout,
    and free cash flow yield.

    Business use:
    This scoring function enables ranking and comparison of stocks by combining
    dividend growth (CAGR), free cash flow yield, and payout ratio into a single
    normalized metric. It supports quantitative screening, ranking, and
    prioritization of DGI candidates for further research or portfolio inclusion.
    """
    cagr_norm = min(max(row["dividend_cagr"] / 20.0, 0.0), 1.0)
    fcf_norm = min(max(row["fcf_yield"] / 20.0, 0.0), 1.0)
    payout_norm = min(max(row["payout"] / 100.0, 0.0), 1.0)
    composite = cagr_norm + fcf_norm - payout_norm
    composite = composite / 3.0
    result = max(0.0, min(composite, 1.0))
    return float(result)
