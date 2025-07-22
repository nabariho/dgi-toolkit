# portfolio.py

from pandas import DataFrame
from typing import Dict, Any


def portfolio_placeholder() -> None:
    pass


def build(df: DataFrame, top_n: int, weighting: str) -> DataFrame:
    """
    Select top-N stocks by score and assign weights.

    Args:
        df: DataFrame with at least columns 'symbol' (or 'ticker') and 'score'.
        top_n: Number of top stocks to select.
        weighting: 'equal' or 'score'.

    Returns:
        DataFrame with columns: 'ticker', 'weight', 'score'.

    Raises:
        ValueError: If top_n > len(df) or weighting is invalid.
    """
    if top_n > len(df):
        raise ValueError(
            f"top_n ({top_n}) cannot be greater than number of stocks ({len(df)})"
        )
    if weighting not in ("equal", "score"):
        raise ValueError("weighting must be 'equal' or 'score'")

    # Accept both 'symbol' and 'ticker' as input
    ticker_col = "ticker" if "ticker" in df.columns else "symbol"
    top = df.sort_values("score", ascending=False).head(top_n).copy()
    if weighting == "equal":
        top["weight"] = 1.0 / top_n
    else:  # score-weighted
        total_score = top["score"].sum()
        if total_score == 0:
            top["weight"] = 1.0 / top_n
        else:
            top["weight"] = top["score"] / total_score
    return top[[ticker_col, "weight", "score"]].rename(columns={ticker_col: "ticker"})


def summary_stats(df: DataFrame) -> Dict[str, Any]:
    """
    Compute summary statistics for a portfolio DataFrame.

    Args:
        df: DataFrame with columns 'dividend_yield', 'dividend_cagr', 'payout'.

    Returns:
        Dict with keys: 'yield', 'median_cagr', 'mean_payout'.
    """
    return {
        "yield": float(df["dividend_yield"].mean()),
        "median_cagr": float(df["dividend_cagr"].median()),
        "mean_payout": float(df["payout"].mean()),
    }
