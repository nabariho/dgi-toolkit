"""Screening service for business logic separation."""

import logging
from typing import Any

from pandas import DataFrame

from dgi.exceptions import DataValidationError, ScreeningError
from dgi.models import CompanyData

logger = logging.getLogger(__name__)


class ScreeningService:
    """Service class for screening business logic."""

    @staticmethod
    def validate_screening_parameters(
        min_yield: float, max_payout: float, min_cagr: float, top_n: int
    ) -> None:
        """Validate screening parameters using business rules."""
        if min_yield < 0:
            raise DataValidationError("Minimum yield must be non-negative")
        if max_payout < 0 or max_payout > 200:
            raise DataValidationError("Maximum payout ratio must be between 0 and 200")
        if min_cagr < -100 or min_cagr > 100:
            raise DataValidationError("Minimum CAGR must be between -100 and 100")
        if top_n < 1:
            raise DataValidationError("Top N must be at least 1")

    @staticmethod
    def apply_dgi_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply DGI criteria to DataFrame."""
        if df.empty:
            return df

        # Get the actual column names from the DataFrame
        payout_col = "payout" if "payout" in df.columns else "payout_ratio"
        cagr_col = (
            "dividend_cagr" if "dividend_cagr" in df.columns else "dividend_growth_5y"
        )

        # Check if required columns exist
        required_columns = ["dividend_yield", payout_col, cagr_col]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # Return empty DataFrame with same structure if columns are missing
            return df[df.index.isin([])]

        return df[
            (df["dividend_yield"] >= min_yield)
            & (df[payout_col] <= max_payout)
            & (df[cagr_col] >= min_cagr)
        ]

    @staticmethod
    def score_dataframe(df: DataFrame) -> DataFrame:
        """Score all rows in DataFrame."""
        df = df.copy()

        if df.empty:
            return df

        # Convert each row to CompanyData and score
        def score_row(row: Any) -> float:
            try:
                company = CompanyData(**row.to_dict())
                return ScreeningService.calculate_composite_score(company)
            except Exception as e:
                logger.error(f"Error scoring row: {e}")
                return 0.0

        df["score"] = df.apply(score_row, axis=1)
        return df

    @staticmethod
    def get_top_stocks(df: DataFrame, top_n: int) -> DataFrame:
        """Get top N stocks by score."""
        if len(df) > 0 and "score" in df.columns:
            return df.nlargest(top_n, "score")
        return df.head(top_n)

    @staticmethod
    def validate_screening_results(df: DataFrame) -> None:
        """Validate screening results according to business rules."""
        if not isinstance(df, DataFrame):
            raise ScreeningError("Screening results must be a DataFrame")

        # For empty results, that's valid
        if df.empty:
            return

        required_columns = ["symbol", "dividend_yield", "payout", "dividend_cagr"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ScreeningError(f"Missing required columns: {missing_columns}")

    @staticmethod
    def calculate_composite_score(company: CompanyData) -> float:
        """Calculate composite DGI score for a company."""
        from dgi.scoring_config import get_scoring_config

        config = get_scoring_config()

        # Calculate yield score with configurable weight
        yield_score = float(company.dividend_yield) * config.weights.yield_weight

        # Calculate growth score with configurable weight
        growth_score = float(company.dividend_growth_5y) * config.weights.growth_weight

        # Calculate payout penalty with configurable threshold and weight
        payout_penalty = (
            max(
                0, float(company.payout_ratio) - config.weights.payout_penalty_threshold
            )
            * config.weights.payout_penalty_weight
        )

        # Calculate FCF yield score with configurable weight
        fcf_score = float(company.fcf_yield) * config.weights.fcf_yield_weight

        # Calculate sector bonus
        sector_bonus = (
            config.weights.sector_bonus
            if company.sector in config.preferred_sectors
            else 0.0
        )

        # Calculate industry bonus
        industry_bonus = (
            config.weights.industry_bonus
            if company.industry in config.preferred_industries
            else 0.0
        )

        # Calculate total score
        total_score = (
            yield_score
            + growth_score
            + payout_penalty
            + fcf_score
            + sector_bonus
            + industry_bonus
        )

        # Apply normalization and bounds
        return max(0.0, min(1.0, total_score))

    @staticmethod
    def rows_to_dataframe(rows: list[CompanyData] | list[dict[str, Any]]) -> DataFrame:
        """Convert list of CompanyData objects or dictionaries to DataFrame with proper column names."""
        if not rows:
            return DataFrame()

        # Check if we're dealing with CompanyData objects or dictionaries
        if isinstance(rows[0], CompanyData):
            # Convert CompanyData objects to dictionaries with the correct column names
            data = []
            for row in rows:
                data.append(
                    {
                        "symbol": row.symbol,
                        "name": row.name,
                        "sector": row.sector,
                        "industry": row.industry,
                        "dividend_yield": row.dividend_yield,
                        "payout": row.payout,  # Use the alias property
                        "dividend_cagr": row.dividend_cagr,  # Use the alias property
                        "fcf_yield": row.fcf_yield,
                    }
                )
        else:
            # Handle dictionaries directly
            data = rows

        return DataFrame(data)

    @staticmethod
    def apply_screening_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply screening criteria to DataFrame."""
        if df.empty:
            return df

        filtered_df = df.copy()

        # Apply yield filter
        if "dividend_yield" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["dividend_yield"] >= min_yield]

        # Apply payout filter
        if "payout" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["payout"] <= max_payout]

        # Apply CAGR filter
        if "dividend_cagr" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["dividend_cagr"] >= min_cagr]

        return filtered_df

    @staticmethod
    def convert_to_response_format(df: DataFrame) -> list[dict[str, Any]]:
        """Convert DataFrame to response format."""
        if df.empty:
            return []

        # Convert DataFrame to list of dictionaries
        records = df.to_dict("records")

        # Ensure all numeric values are properly formatted
        for record in records:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    record[key] = float(value)

        return records
