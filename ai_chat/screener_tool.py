"""LangChain tool wrapper for DGI screener functionality.

This module exposes the DGI stock screener as a LangChain tool that can be used
by GPT-4o and other LLMs via function calling.
"""

from typing import Any

from langchain.tools import tool

from dgi.models.company import CompanyData
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring
from dgi.screener import Screener
from dgi.validation import DgiRowValidator, PydanticRowValidation


@tool
def screen_dividends(
    min_yield: float = 0.0,
    max_payout: float = 100.0,
    min_cagr: float = 0.0,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Screen dividend growth stocks based on financial criteria.

    This tool filters and ranks dividend-paying stocks based on yield, payout ratio,
    and dividend growth rate, returning the top performers.

    Args:
        min_yield: Minimum dividend yield (as decimal, e.g., 0.02 for 2%)
        max_payout: Maximum payout ratio (as percentage, e.g., 80.0 for 80%)
        min_cagr: Minimum 5-year dividend CAGR (as decimal, e.g., 0.05 for 5%)
        top_n: Number of top stocks to return (default: 10)

    Returns:
        List of dictionaries containing stock information:
        - symbol: Stock ticker symbol
        - name: Company name
        - sector: Business sector
        - industry: Industry classification
        - dividend_yield: Current dividend yield (%)
        - payout_ratio: Dividend payout ratio (%)
        - dividend_growth_5y: 5-year dividend CAGR (%)
        - fcf_yield: Free cash flow yield (%)
        - score: Composite DGI score (0-1, higher is better)

    Example:
        screen_dividends(min_yield=0.03, max_payout=60.0, min_cagr=0.05, top_n=5)
        # Returns top 5 stocks with >3% yield, <60% payout, >5% dividend growth
    """
    try:
        # Set up the screener with default data source
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        repo = CsvCompanyDataRepository("data/fundamentals_small.csv", validator)
        screener = Screener(repo, scoring_strategy=DefaultScoring())

        # Load and filter the universe
        df = screener.load_universe()
        filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
        scored = screener.add_scores(filtered)

        if scored.empty:
            return []

        # Get top N stocks
        top_stocks = scored.sort_values("score", ascending=False).head(top_n)

        # Convert to list of dictionaries for JSON serialization
        results = []
        for _, row in top_stocks.iterrows():
            results.append(
                {
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "sector": row["sector"],
                    "industry": row["industry"],
                    "dividend_yield": float(row["dividend_yield"]),
                    "payout_ratio": float(
                        row["payout"]
                    ),  # Use alias name from DataFrame
                    "dividend_growth_5y": float(row["dividend_cagr"]),  # Use alias name
                    "fcf_yield": float(row["fcf_yield"]),
                    "score": float(row["score"]),
                }
            )

        return results

    except Exception as e:
        # Return error information for debugging
        return [{"error": f"Screening failed: {e!s}"}]
