"""DataFrame scoring service."""

import logging
from typing import Any

from pandas import DataFrame

from dgi.exceptions import ScreeningError

logger = logging.getLogger(__name__)


class DataFrameScoringService:
    """Service for scoring DataFrames using vectorized operations."""

    @staticmethod
    def score_dataframe(df: DataFrame) -> DataFrame:
        """Score all rows in DataFrame using vectorized operations for better performance.

        Args:
            df: DataFrame containing company data to score

        Returns:
            DataFrame with added 'score' column

        Raises:
            ScreeningError: If scoring configuration cannot be loaded or scoring fails
        """
        if df.empty:
            return df

        try:
            return DataFrameScoringService._apply_vectorized_scoring(df)
        except Exception as e:
            logger.error(f"Error during DataFrame scoring: {e}")
            raise ScreeningError(f"Failed to score DataFrame: {e}") from e

    @staticmethod
    def _apply_vectorized_scoring(df: DataFrame) -> DataFrame:
        """Apply vectorized scoring calculations to the DataFrame."""
        # Import scoring configuration
        from dgi.scoring_config import get_scoring_config

        config = get_scoring_config()

        # Get column names with fallbacks for different naming conventions
        column_mapping = DataFrameScoringService._get_column_mapping(df)

        # Calculate individual component scores using vectorized operations
        yield_score = (
            df[column_mapping["dividend_yield"]].fillna(0) * config.weights.yield_weight
        )

        growth_score = (
            df[column_mapping["dividend_cagr"]].fillna(0) * config.weights.growth_weight
        )

        payout_score = DataFrameScoringService._calculate_payout_score(
            df, column_mapping["payout"], config.weights.payout_penalty_weight
        )

        fcf_score = (
            df[column_mapping["fcf_yield"]].fillna(0) * config.weights.fcf_yield_weight
        )

        # Combine scores
        df_scored = df.copy()
        df_scored["score"] = yield_score + growth_score + payout_score + fcf_score

        # Normalize scores to 0-1 range
        df_scored["score"] = df_scored["score"].clip(0, 1)

        return df_scored

    @staticmethod
    def _get_column_mapping(df: DataFrame) -> dict[str, str]:
        """Get the mapping of logical column names to actual DataFrame column names."""
        return {
            "dividend_yield": "dividend_yield",
            "payout": "payout" if "payout" in df.columns else "payout_ratio",
            "dividend_cagr": (
                "dividend_cagr"
                if "dividend_cagr" in df.columns
                else "dividend_growth_5y"
            ),
            "fcf_yield": "fcf_yield",
        }

    @staticmethod
    def _calculate_payout_score(
        df: DataFrame, payout_col: str, payout_weight: float
    ) -> Any:  # Returns a pandas Series
        """Calculate payout score with proper handling of inverted scoring."""
        # Lower payout ratios are better, so we invert the score
        payout_series = df[payout_col].fillna(100)  # Default to high payout if missing

        # Normalize to 0-1 range where 0% payout = 1.0 score, 100% payout = 0.0 score
        normalized_payout = (100 - payout_series.clip(0, 100)) / 100

        return normalized_payout * payout_weight
