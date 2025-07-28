"""Portfolio service for business logic separation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pandas import DataFrame

logger = logging.getLogger(__name__)


class WeightingStrategy(ABC):
    """Abstract base class for portfolio weighting strategies."""

    @abstractmethod
    def compute_weights(self, df: DataFrame) -> DataFrame:
        """Compute portfolio weights using business rules."""


class EqualWeighting(WeightingStrategy):
    """Equal weighting strategy - each stock gets equal weight."""

    def compute_weights(self, df: DataFrame) -> DataFrame:
        """Compute equal weights for all stocks."""
        df = df.copy()
        n = len(df)
        df["weight"] = 1.0 / n if n > 0 else 0.0
        return df


class ScoreWeighting(WeightingStrategy):
    """Score-based weighting strategy - weight proportional to score."""

    def compute_weights(self, df: DataFrame) -> DataFrame:
        """Compute weights proportional to stock scores."""
        df = df.copy()
        total_score = df["score"].sum()

        if total_score == 0:
            # Fallback to equal weighting if no scores
            df["weight"] = 1.0 / len(df) if len(df) > 0 else 0.0
        else:
            df["weight"] = df["score"] / total_score

        return df


class PortfolioService:
    """Service class for portfolio business logic."""

    _strategies: ClassVar[dict[str, WeightingStrategy]] = {
        "equal": EqualWeighting(),
        "score": ScoreWeighting(),
    }

    @staticmethod
    def calculate_equal_weights(df: DataFrame) -> DataFrame:
        """Calculate equal weights for all stocks in DataFrame."""
        if df.empty:
            return df

        df = df.copy()
        n = len(df)
        df["weight"] = 1.0 / n
        return df

    @staticmethod
    def calculate_score_weights(df: DataFrame) -> DataFrame:
        """Calculate score-based weights for all stocks in DataFrame."""
        if df.empty:
            return df

        df = df.copy()
        total_score = df["score"].sum()

        if total_score == 0:
            # Fallback to equal weighting if no scores
            df["weight"] = 1.0 / len(df)
        else:
            df["weight"] = df["score"] / total_score

        return df

    @staticmethod
    def validate_portfolio_parameters(
        df: DataFrame, top_n: int, weighting: str, ticker_col: str | None = None
    ) -> str:
        """Validate portfolio construction parameters."""
        if top_n > len(df):
            raise ValueError("top_n cannot be greater than number of stocks")

        if "score" not in df.columns:
            raise ValueError("Missing 'score' column in DataFrame")

        if not ticker_col:
            ticker_col = "ticker" if "ticker" in df.columns else "symbol"

        if ticker_col not in df.columns:
            raise ValueError(f"Missing ticker column: {ticker_col}")

        if weighting not in PortfolioService._strategies:
            raise ValueError("weighting must be 'equal' or 'score'")

        return ticker_col

    @staticmethod
    def build_portfolio(
        df: DataFrame,
        top_n: int,
        weighting: str = "equal",
        ticker_col: str | None = None,
    ) -> DataFrame:
        """Build a portfolio using business rules."""
        # Validate parameters
        ticker_col = PortfolioService.validate_portfolio_parameters(
            df, top_n, weighting, ticker_col
        )

        # Business logic: Select top N stocks by score
        top = df.sort_values("score", ascending=False).head(top_n).copy()

        # Apply weighting strategy
        strategy = PortfolioService._strategies[weighting]
        weighted: DataFrame = strategy.compute_weights(top)

        # Return standardized format
        return weighted[[ticker_col, "weight", "score"]].rename(
            columns={ticker_col: "ticker"}
        )

    @staticmethod
    def calculate_summary_statistics(df: DataFrame) -> dict[str, Any]:
        """Calculate portfolio summary statistics using business rules."""
        if df.empty:
            return {
                "yield": float("nan"),
                "median_cagr": float("nan"),
                "mean_payout": float("nan"),
            }

        return {
            "yield": float(df["dividend_yield"].mean()),
            "median_cagr": float(df["dividend_cagr"].median()),
            "mean_payout": float(df["payout"].mean()),
        }

    @staticmethod
    def get_available_weighting_strategies() -> dict[str, str]:
        """Get available weighting strategies with descriptions."""
        return {
            "equal": "Equal weighting - each stock gets equal weight",
            "score": "Score-based weighting - weight proportional to composite score",
        }

    @staticmethod
    def validate_weighting_strategy(weighting: str) -> bool:
        """Validate if a weighting strategy is supported."""
        return weighting in PortfolioService._strategies
