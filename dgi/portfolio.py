# portfolio.py

import logging
from abc import ABC, abstractmethod
from typing import Any

from pandas import DataFrame

logger = logging.getLogger(__name__)


class WeightingStrategy(ABC):
    @abstractmethod
    def compute_weights(self, df: DataFrame) -> DataFrame:
        pass


class EqualWeighting(WeightingStrategy):
    def compute_weights(self, df: DataFrame) -> DataFrame:
        n = len(df)
        df = df.copy()
        df["weight"] = 1.0 / n if n > 0 else 0.0
        return df


class ScoreWeighting(WeightingStrategy):
    def compute_weights(self, df: DataFrame) -> DataFrame:
        df = df.copy()
        total_score = df["score"].sum()
        if total_score == 0:
            df["weight"] = 1.0 / len(df) if len(df) > 0 else 0.0
        else:
            df["weight"] = df["score"] / total_score
        return df


def build(
    df: DataFrame,
    top_n: int,
    weighting: str = "equal",
    ticker_col: str | None = None,
) -> DataFrame:
    """
    Build a portfolio by selecting top-N stocks and applying a weighting strategy.

    Args:
        df: DataFrame with at least columns 'symbol' (or 'ticker') and 'score'.
        top_n: Number of top stocks to select.
        weighting: 'equal' or 'score'.
        ticker_col: Optional override for ticker column name.

    Returns:
        DataFrame with columns: 'ticker', 'weight', 'score'.

    Raises:
        ValueError: If top_n > len(df), missing columns, or invalid weighting.
    """
    if top_n > len(df):
        logger.error("top_n (%d) > number of stocks (%d)", top_n, len(df))
        raise ValueError("top_n cannot be greater than number of stocks")
    if "score" not in df.columns:
        logger.error("Missing 'score' column in DataFrame")
        raise ValueError("Missing 'score' column in DataFrame")
    if not ticker_col:
        ticker_col = "ticker" if "ticker" in df.columns else "symbol"
    if ticker_col not in df.columns:
        logger.error("Missing ticker column: %s", ticker_col)
        raise ValueError(f"Missing ticker column: {ticker_col}")

    top = df.sort_values("score", ascending=False).head(top_n).copy()

    strategies = {
        "equal": EqualWeighting(),
        "score": ScoreWeighting(),
    }
    if weighting not in strategies:
        logger.error("Invalid weighting: %s", weighting)
        raise ValueError("weighting must be 'equal' or 'score'")

    weighted = strategies[weighting].compute_weights(top)
    return weighted[[ticker_col, "weight", "score"]].rename(
        columns={ticker_col: "ticker"}
    )


def summary_stats(df: DataFrame) -> dict[str, Any]:
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
