from abc import ABC, abstractmethod
from typing import Protocol

from pandas import DataFrame


class BaseFilter(ABC):
    """Base interface for all filter operations."""

    @abstractmethod
    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply filter to DataFrame."""


class YieldFilter(Protocol):
    """Protocol for yield-based filtering."""

    def filter_by_yield(self, df: DataFrame, min_yield: float) -> DataFrame:
        """Filter by minimum dividend yield."""
        ...


class PayoutFilter(Protocol):
    """Protocol for payout-based filtering."""

    def filter_by_payout(self, df: DataFrame, max_payout: float) -> DataFrame:
        """Filter by maximum payout ratio."""
        ...


class GrowthFilter(Protocol):
    """Protocol for growth-based filtering."""

    def filter_by_growth(self, df: DataFrame, min_cagr: float) -> DataFrame:
        """Filter by minimum dividend growth."""
        ...


class SectorFilter(Protocol):
    """Protocol for sector-based filtering."""

    def filter_by_sector(self, df: DataFrame, allowed_sectors: list[str]) -> DataFrame:
        """Filter by allowed sectors."""
        ...


class CompositeFilter(Protocol):
    """Protocol for composite filtering."""

    def add_filter(self, filter_strategy: BaseFilter) -> None:
        """Add a filter to the composite."""
        ...


class RankingFilter(Protocol):
    """Protocol for ranking-based filtering."""

    def filter_by_rank(self, df: DataFrame, top_n: int, sort_column: str) -> DataFrame:
        """Filter by ranking criteria."""
        ...


# Specific filter interfaces that implement only what they need


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


# Legacy implementations for backward compatibility


class YieldFilterImpl:
    """Implementation of yield filter only."""

    def filter_by_yield(self, df: DataFrame, min_yield: float) -> DataFrame:
        """Filter by minimum dividend yield."""
        if df.empty or "dividend_yield" not in df.columns:
            return df
        return df[df["dividend_yield"] >= min_yield]


class PayoutFilterImpl:
    """Implementation of payout filter only."""

    def filter_by_payout(self, df: DataFrame, max_payout: float) -> DataFrame:
        """Filter by maximum payout ratio."""
        if df.empty or "payout" not in df.columns:
            return df
        return df[df["payout"] <= max_payout]


class GrowthFilterImpl:
    """Implementation of growth filter only."""

    def filter_by_growth(self, df: DataFrame, min_cagr: float) -> DataFrame:
        """Filter by minimum dividend growth."""
        if df.empty or "dividend_cagr" not in df.columns:
            return df
        return df[df["dividend_cagr"] >= min_cagr]


class SectorFilterImpl:
    """Implementation of sector filter only."""

    def __init__(self, allowed_sectors: list[str]):
        self.allowed_sectors = allowed_sectors

    def filter_by_sector(self, df: DataFrame, allowed_sectors: list[str]) -> DataFrame:
        """Filter by allowed sectors."""
        if df.empty or "sector" not in df.columns:
            return df
        return df[df["sector"].isin(allowed_sectors)]


class RankingFilterImpl:
    """Implementation of ranking filter only."""

    def filter_by_rank(self, df: DataFrame, top_n: int, sort_column: str) -> DataFrame:
        """Filter by ranking criteria."""
        if df.empty or sort_column not in df.columns:
            return df
        return df.nlargest(top_n, sort_column)
