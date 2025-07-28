"""Filtering strategies for DGI Toolkit.

This module implements the Strategy pattern for different filtering approaches
used in stock screening. All filters inherit from BaseFilter and can be
composed together for complex filtering logic.
"""

from abc import ABC, abstractmethod

from pandas import DataFrame


class BaseFilter(ABC):
    """Abstract base class for all filter strategies."""

    @abstractmethod
    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply filter to DataFrame."""


class YieldOnlyFilter(BaseFilter):
    """Filter that only applies yield criteria."""

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply only yield filter."""
        if df.empty:
            return df

        if "dividend_yield" not in df.columns:
            return df[df.index.isin([])]

        return df[df["dividend_yield"] >= min_yield]


class PayoutOnlyFilter(BaseFilter):
    """Filter that only applies payout criteria."""

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply only payout filter."""
        if df.empty:
            return df

        if "payout" not in df.columns:
            return df[df.index.isin([])]

        return df[df["payout"] <= max_payout]


class GrowthOnlyFilter(BaseFilter):
    """Filter that only applies growth criteria."""

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply only growth filter."""
        if df.empty:
            return df

        if "dividend_cagr" not in df.columns:
            return df[df.index.isin([])]

        return df[df["dividend_cagr"] >= min_cagr]


class DefaultFilter(BaseFilter):
    """Standard DGI filter based on yield, payout ratio, and dividend growth."""

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        # Handle empty DataFrame gracefully
        if df.empty:
            return df

        # Check if required columns exist
        required_columns = ["dividend_yield", "payout", "dividend_cagr"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # Return empty DataFrame with same structure if columns are missing
            return df[df.index.isin([])]  # Empty DataFrame with same columns

        return df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]


class SectorFilter(BaseFilter):
    """Filter that applies sector-based filtering."""

    def __init__(self, allowed_sectors: list[str]):
        self.allowed_sectors = allowed_sectors

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        # Handle empty DataFrame gracefully
        if df.empty:
            return df

        # Check if sector column exists
        if "sector" not in df.columns:
            return df[df.index.isin([])]

        return df[df["sector"].isin(self.allowed_sectors)]


class CompositeFilter(BaseFilter):
    """Composite filter that combines multiple filter strategies."""

    def __init__(self, *filters: BaseFilter):
        self.filters = list(filters)

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        # Handle empty DataFrame gracefully
        if df.empty:
            return df

        result = df
        for filter_strategy in self.filters:
            result = filter_strategy.filter(result, min_yield, max_payout, min_cagr)
        return result

    def add_filter(self, filter_strategy: BaseFilter) -> None:
        """Add a filter to the composite."""
        self.filters.append(filter_strategy)


class TopNFilter(BaseFilter):
    """Filter that returns top N results based on a sort column."""

    def __init__(self, top_n: int, base_filter: BaseFilter | None = None):
        self.top_n = top_n
        self.base_filter = base_filter

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        # Handle empty DataFrame gracefully
        if df.empty:
            return df

        # Apply base filter first if provided
        if self.base_filter:
            df = self.base_filter.filter(df, min_yield, max_payout, min_cagr)

        # Return top N
        return df.head(self.top_n)


class RankingFilter(BaseFilter):
    """Filter that ranks results by a specific column and returns top N."""

    def __init__(self, top_n: int, sort_column: str, ascending: bool = False):
        self.top_n = top_n
        self.sort_column = sort_column
        self.ascending = ascending

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        # Handle empty DataFrame gracefully
        if df.empty:
            return df

        # Check if sort column exists
        if self.sort_column not in df.columns:
            return df.head(self.top_n)

        # Sort and return top N
        return df.sort_values(self.sort_column, ascending=self.ascending).head(
            self.top_n
        )
