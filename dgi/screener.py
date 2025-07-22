# screener.py

import pandas as pd
from pandas import DataFrame
from typing import Any


def load_universe(csv_path: str = "data/fundamentals_small.csv") -> DataFrame:
    """
    Load the fundamentals universe from a CSV file into a DataFrame with correct dtypes.
    Expects columns: symbol, name, sector, industry, dividend_yield, payout,
    dividend_cagr, fcf_yield
    """
    dtype = {
        "symbol": "str",
        "name": "str",
        "sector": "str",
        "industry": "str",
        "dividend_yield": "float64",
        "payout": "float64",
        "dividend_cagr": "float64",
        "fcf_yield": "float64",
    }
    df = pd.read_csv(csv_path, dtype=dtype)  # type: ignore[arg-type]
    return df


def apply_filters(
    df: DataFrame,
    min_yield: float = 0.0,
    max_payout: float = 100.0,
    min_cagr: float = 0.0,
) -> DataFrame:
    """
    Filter the DataFrame by minimum yield, maximum payout, and minimum dividend CAGR.
    """
    filtered = df[
        (df["dividend_yield"] >= min_yield)
        & (df["payout"] <= max_payout)
        & (df["dividend_cagr"] >= min_cagr)
    ]
    return filtered


def score(row: pd.Series[Any]) -> float:
    """
    Compute a 0-1 composite score: (1/3 * CAGR + 1/3 * FCF-yield - 1/3 * payout),
    normalized to 0-1.
    Assumes input row has dividend_cagr, fcf_yield, payout as floats (0-100 scale).
    """
    cagr_norm = min(max(row["dividend_cagr"] / 20.0, 0.0), 1.0)
    fcf_norm = min(max(row["fcf_yield"] / 20.0, 0.0), 1.0)
    payout_norm = min(max(row["payout"] / 100.0, 0.0), 1.0)
    composite = cagr_norm + fcf_norm - payout_norm
    composite = composite / 3.0
    result = max(0.0, min(composite, 1.0))
    return float(result)


def screener_placeholder() -> None:
    pass
