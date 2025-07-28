# portfolio.py

import logging
from typing import Any

from pandas import DataFrame

from dgi.services import PortfolioService

logger = logging.getLogger(__name__)


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
    return PortfolioService.build_portfolio(df, top_n, weighting, ticker_col)


def summary_stats(df: DataFrame) -> dict[str, Any]:
    """
    Compute summary statistics for a portfolio DataFrame.

    Args:
        df: DataFrame with columns 'dividend_yield', 'dividend_cagr', 'payout'.

    Returns:
        Dict with keys: 'yield', 'median_cagr', 'mean_payout'.
    """
    return PortfolioService.calculate_summary_statistics(df)
