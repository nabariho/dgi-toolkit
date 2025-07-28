"""Service layer for DGI Toolkit business logic.

This module contains pure business logic extracted from infrastructure concerns,
following the Single Responsibility Principle and Clean Architecture patterns.
"""

import logging
from typing import Any

from pandas import DataFrame

from dgi.exceptions import DataValidationError, PortfolioError, ScreeningError
from dgi.models import CompanyData
from dgi.scoring_config import get_scoring_config

logger = logging.getLogger(__name__)


class ScreeningService:
    """Service for stock screening business logic."""

    @staticmethod
    def calculate_composite_score(company: CompanyData) -> float:
        """Calculate composite DGI score for a company.

        This is pure business logic extracted from the screener.
        """
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
    def validate_screening_parameters(
        min_yield: float, max_payout: float, min_cagr: float, top_n: int
    ) -> None:
        """Validate screening parameters according to business rules."""
        if min_yield < 0:
            raise DataValidationError(
                "Minimum yield must be non-negative", field="min_yield", value=min_yield
            )
        if max_payout < 0 or max_payout > 200:
            raise DataValidationError(
                "Maximum payout ratio must be between 0 and 200",
                field="max_payout",
                value=max_payout,
            )
        if min_cagr < -100 or min_cagr > 100:
            raise DataValidationError(
                "Minimum CAGR must be between -100 and 100",
                field="min_cagr",
                value=min_cagr,
            )
        if top_n < 1:
            raise DataValidationError(
                "Top N must be at least 1", field="top_n", value=top_n
            )

    @staticmethod
    def apply_dgi_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply DGI criteria to DataFrame.

        This is pure business logic for filtering stocks.
        """
        # Handle empty DataFrame gracefully
        if df.empty:
            return df

        # Check if required columns exist
        required_columns = ["dividend_yield", "payout", "dividend_cagr"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # Return empty DataFrame with same structure if columns are missing
            return df[df.index.isin([])]

        return df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]

    @staticmethod
    def score_dataframe(df: DataFrame) -> DataFrame:
        """Score all rows in DataFrame.

        This is pure business logic for scoring stocks.
        """
        df = df.copy()

        # Handle empty DataFrame
        if df.empty:
            df["score"] = []  # Add empty score column
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
        """Get top N stocks by score.

        This is pure business logic for ranking stocks.
        """
        if len(df) > 0 and "score" in df.columns:
            return df.nlargest(top_n, "score")
        return df.head(top_n)

    @staticmethod
    def validate_screening_results(df: DataFrame) -> None:
        """Validate screening results according to business rules."""
        if not isinstance(df, DataFrame):
            raise ScreeningError(
                "Screening results must be a DataFrame", operation="validation"
            )

        # For empty results, that's valid
        if df.empty:
            return

        required_columns = ["symbol", "dividend_yield", "payout", "dividend_cagr"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ScreeningError(
                f"Missing required columns: {missing_columns}", operation="validation"
            )

    @staticmethod
    def calculate_screening_metrics(df: DataFrame) -> dict[str, Any]:
        """Calculate business metrics from screening results."""
        if df.empty:
            return {
                "total_stocks": 0,
                "average_yield": 0.0,
                "average_payout": 0.0,
                "average_cagr": 0.0,
                "average_score": 0.0,
                "sector_distribution": {},
                "industry_distribution": {},
            }

        metrics = {
            "total_stocks": len(df),
            "average_yield": (
                float(df["dividend_yield"].mean())
                if "dividend_yield" in df.columns
                else 0.0
            ),
            "average_payout": (
                float(df["payout"].mean()) if "payout" in df.columns else 0.0
            ),
            "average_cagr": (
                float(df["dividend_cagr"].mean())
                if "dividend_cagr" in df.columns
                else 0.0
            ),
            "average_score": (
                float(df["score"].mean()) if "score" in df.columns else 0.0
            ),
        }

        # Calculate sector distribution
        if "sector" in df.columns:
            metrics["sector_distribution"] = df["sector"].value_counts().to_dict()
        else:
            metrics["sector_distribution"] = {}

        # Calculate industry distribution
        if "industry" in df.columns:
            metrics["industry_distribution"] = df["industry"].value_counts().to_dict()
        else:
            metrics["industry_distribution"] = {}

        return metrics

    @staticmethod
    def rows_to_dataframe(rows: list[dict[str, Any]]) -> DataFrame:
        """Convert list of row dictionaries to DataFrame.

        This is pure business logic for data transformation.
        """
        if not rows:
            return DataFrame()

        return DataFrame(rows)

    @staticmethod
    def apply_screening_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply screening criteria to DataFrame.

        This is pure business logic for filtering stocks.
        """
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
        """Convert DataFrame to response format.

        This is pure business logic for data transformation.
        """
        if df.empty:
            return []

        # Convert DataFrame to list of dictionaries
        records = df.to_dict("records")

        # Ensure all numeric values are properly formatted
        for record in records:
            for key, value in record.items():
                if isinstance(value, int | float):
                    record[key] = float(value)

        return records


class PortfolioService:
    """Service for portfolio construction business logic."""

    @staticmethod
    def calculate_equal_weights(df: DataFrame) -> DataFrame:
        """Calculate equal weights for portfolio allocation."""
        df = df.copy()
        if len(df) > 0:
            df["weight"] = 1.0 / len(df)
        else:
            df["weight"] = []
        return df

    @staticmethod
    def calculate_score_weights(df: DataFrame) -> DataFrame:
        """Calculate score-proportional weights for portfolio allocation."""
        df = df.copy()
        if len(df) > 0 and "score" in df.columns:
            total_score = df["score"].sum()
            if total_score > 0:
                df["weight"] = df["score"] / total_score
            else:
                df["weight"] = 1.0 / len(df)
        else:
            df["weight"] = 1.0 / len(df) if len(df) > 0 else []
        return df

    @staticmethod
    def validate_portfolio_weights(df: DataFrame) -> None:
        """Validate portfolio weights according to business rules."""
        if "weight" not in df.columns:
            raise PortfolioError("Portfolio must have weight column")

        if len(df) > 0:
            total_weight = df["weight"].sum()
            if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
                raise PortfolioError(
                    f"Portfolio weights must sum to 1.0, got {total_weight}"
                )

    @staticmethod
    def calculate_portfolio_metrics(df: DataFrame) -> dict[str, Any]:
        """Calculate portfolio-level metrics."""
        if df.empty:
            return {
                "total_weight": 0.0,
                "number_of_positions": 0,
                "concentration_risk": 0.0,
                "sector_concentration": {},
            }

        if "weight" not in df.columns:
            return {
                "total_weight": 0.0,
                "number_of_positions": len(df),
                "concentration_risk": 0.0,
                "sector_concentration": {},
            }

        # Calculate concentration risk (Herfindahl-Hirschman Index)
        weights_squared = df["weight"] ** 2
        concentration_risk = float(weights_squared.sum())

        # Calculate sector concentration
        sector_concentration = {}
        if "sector" in df.columns:
            sector_weights = df.groupby("sector")["weight"].sum()
            sector_concentration = sector_weights.to_dict()

        return {
            "total_weight": float(df["weight"].sum()),
            "number_of_positions": len(df),
            "concentration_risk": concentration_risk,
            "sector_concentration": sector_concentration,
        }


class ValidationService:
    """Service for data validation business logic."""

    @staticmethod
    def validate_company_data(company: CompanyData) -> None:
        """Validate company data according to business rules."""
        if company.dividend_yield < 0:
            raise DataValidationError(
                "Dividend yield cannot be negative",
                field="dividend_yield",
                value=company.dividend_yield,
            )
        if company.payout_ratio < 0 or company.payout_ratio > 200:
            raise DataValidationError(
                "Payout ratio must be between 0 and 200",
                field="payout_ratio",
                value=company.payout_ratio,
            )
        if company.dividend_growth_5y < -100 or company.dividend_growth_5y > 100:
            raise DataValidationError(
                "Dividend growth must be between -100 and 100",
                field="dividend_growth_5y",
                value=company.dividend_growth_5y,
            )
        if company.fcf_yield < -100 or company.fcf_yield > 100:
            raise DataValidationError(
                "FCF yield must be between -100 and 100",
                field="fcf_yield",
                value=company.fcf_yield,
            )

    @staticmethod
    def validate_screening_results(df: DataFrame) -> None:
        """Validate screening results according to business rules."""
        if not isinstance(df, DataFrame):
            raise ScreeningError(
                "Screening results must be a DataFrame", operation="validation"
            )

        # For empty results, that's valid
        if df.empty:
            return

        required_columns = ["symbol", "dividend_yield", "payout", "dividend_cagr"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ScreeningError(
                f"Missing required columns: {missing_columns}", operation="validation"
            )

    @staticmethod
    def sanitize_company_name(name: str) -> str:
        """Sanitize company name for safe display."""
        if not name:
            return "Unknown"

        # Remove any potentially dangerous characters
        sanitized = "".join(
            c for c in name if c.isalnum() or c.isspace() or c in ".-&,"
        )
        return sanitized.strip()

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate stock symbol format."""
        if not symbol:
            return False

        # Basic validation: alphanumeric, 1-5 characters
        if not symbol.isalnum() or len(symbol) > 5:
            return False

        return True


class DataTransformationService:
    """Service for data transformation business logic."""

    @staticmethod
    def normalize_percentage(value: float) -> float:
        """Normalize percentage value to decimal."""
        return value / 100.0

    @staticmethod
    def denormalize_percentage(value: float) -> float:
        """Convert decimal to percentage."""
        return value * 100.0

    @staticmethod
    def format_currency(value: float) -> str:
        """Format value as currency."""
        return f"${value:.2f}"

    @staticmethod
    def format_percentage(value: float) -> str:
        """Format value as percentage."""
        return f"{value:.2f}%"

    @staticmethod
    def calculate_compound_growth_rate(
        initial_value: float, final_value: float, years: int
    ) -> float:
        """Calculate compound annual growth rate."""
        if years <= 0 or initial_value <= 0:
            return 0.0

        if final_value <= 0:
            return -1.0  # Indicates negative growth

        growth_rate = (final_value / initial_value) ** (1.0 / years) - 1.0
        return growth_rate
