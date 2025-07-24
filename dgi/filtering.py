from abc import ABC, abstractmethod

from pandas import DataFrame


class FilterStrategy(ABC):
    @abstractmethod
    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        pass


class DefaultFilter(FilterStrategy):
    """Standard DGI filter based on yield, payout ratio, and dividend growth."""

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        return df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]


class SectorFilter(FilterStrategy):
    """Filter stocks by allowed sectors, then apply DGI criteria."""

    def __init__(self, allowed_sectors: list[str]):
        self.allowed_sectors = allowed_sectors

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        # First apply base DGI filters
        base_filtered = df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]

        # Then apply sector filter if sector column exists
        if "sector" in base_filtered.columns:
            return base_filtered[base_filtered["sector"].isin(self.allowed_sectors)]

        return base_filtered


class CompositeFilter(FilterStrategy):
    """Combines multiple filter strategies in sequence."""

    def __init__(self, *filters: FilterStrategy):
        self.filters = filters

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        result = df
        for filter_strategy in self.filters:
            result = filter_strategy.filter(result, min_yield, max_payout, min_cagr)
        return result


class TopNFilter(FilterStrategy):
    """Filter to top N stocks after applying DGI criteria, requires 'score' column."""

    def __init__(self, top_n: int, base_filter: FilterStrategy | None = None):
        self.top_n = top_n
        self.base_filter = base_filter or DefaultFilter()

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        # First apply base filtering
        filtered = self.base_filter.filter(df, min_yield, max_payout, min_cagr)

        # If score column exists, sort by it and take top N
        if "score" in filtered.columns and len(filtered) > 0:
            return filtered.nlargest(self.top_n, "score")

        # Otherwise just take first N rows
        return filtered.head(self.top_n)
