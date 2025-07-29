"""DGI criteria application service."""

import logging

from pandas import DataFrame

from dgi.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class DGICriteriaService:
    """Service for applying DGI (Dividend Growth Investing) criteria to DataFrames."""

    @staticmethod
    def apply_dgi_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply DGI criteria to DataFrame.

        Args:
            df: DataFrame containing company data
            min_yield: Minimum dividend yield (decimal)
            max_payout: Maximum payout ratio (percentage)
            min_cagr: Minimum dividend CAGR (decimal)

        Returns:
            Filtered DataFrame containing only companies meeting DGI criteria

        Raises:
            DataValidationError: If required columns are missing
        """
        if df.empty:
            return df

        # Validate required columns exist
        required_columns = DGICriteriaService._get_required_columns(df)
        DGICriteriaService._validate_columns_exist(df, required_columns)

        # Apply filters
        return DGICriteriaService._apply_filters(df, min_yield, max_payout, min_cagr)

    @staticmethod
    def _get_required_columns(df: DataFrame) -> list[str]:
        """Get the required column names based on what's available in the DataFrame."""
        # Handle different column naming conventions
        payout_col = "payout" if "payout" in df.columns else "payout_ratio"
        cagr_col = (
            "dividend_cagr" if "dividend_cagr" in df.columns else "dividend_growth_5y"
        )

        return ["dividend_yield", payout_col, cagr_col]

    @staticmethod
    def _validate_columns_exist(df: DataFrame, required_columns: list[str]) -> None:
        """Validate that all required columns exist in the DataFrame."""
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise DataValidationError(
                f"Required columns missing from DataFrame: {missing_columns}"
            )

    @staticmethod
    def _apply_filters(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply the actual DGI filters to the DataFrame."""
        # Get column names
        payout_col = "payout" if "payout" in df.columns else "payout_ratio"
        cagr_col = (
            "dividend_cagr" if "dividend_cagr" in df.columns else "dividend_growth_5y"
        )

        # Apply filters step by step for better debugging
        filtered_df = df.copy()

        # Yield filter
        filtered_df = filtered_df[filtered_df["dividend_yield"] >= min_yield]
        logger.debug(f"After yield filter: {len(filtered_df)} companies")

        # Payout filter
        filtered_df = filtered_df[filtered_df[payout_col] <= max_payout]
        logger.debug(f"After payout filter: {len(filtered_df)} companies")

        # CAGR filter
        filtered_df = filtered_df[filtered_df[cagr_col] >= min_cagr]
        logger.debug(f"After CAGR filter: {len(filtered_df)} companies")

        return filtered_df
