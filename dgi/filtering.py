from abc import ABC, abstractmethod
from pandas import DataFrame


class FilterStrategy(ABC):
    @abstractmethod
    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        pass


class DefaultFilter(FilterStrategy):
    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        return df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]
