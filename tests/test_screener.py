import pandas as pd
from typing import Any
from dgi.screener import load_universe, apply_filters, score


def test_load_universe(tmp_path: Any) -> None:
    # Create a temporary CSV with all required columns
    csv = tmp_path / "fundamentals.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,0.6,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,0.8,35,10,7\n"
    )
    df = load_universe(str(csv))
    assert list(df.columns) == [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    assert df.shape[0] == 2
    assert df["dividend_yield"].dtype == float


def test_apply_filters() -> None:
    df = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "dividend_yield": [2.0, 1.0],
            "payout": [40.0, 60.0],
            "dividend_cagr": [7.0, 3.0],
            "name": ["n1", "n2"],
            "sector": ["s1", "s2"],
            "industry": ["i1", "i2"],
            "fcf_yield": [4.0, 2.0],
        }
    )
    filtered = apply_filters(df, min_yield=1.5, max_payout=50.0, min_cagr=5.0)
    assert filtered.shape[0] == 1
    assert filtered.iloc[0]["symbol"] == "A"


def test_score() -> None:
    row = pd.Series(
        {
            "dividend_cagr": 10.0,  # 0.5 normalized
            "fcf_yield": 10.0,  # 0.5 normalized
            "payout": 50.0,  # 0.5 normalized
        }
    )
    s = score(row)
    assert abs(s - 0.16666666666666666) < 1e-6  # (0.5 + 0.5 - 0.5) / 3
