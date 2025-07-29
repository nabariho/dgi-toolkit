"""Screening service for business logic coordination."""

import logging
from typing import Any, Protocol

from pandas import DataFrame

from dgi.exceptions import ScreeningError
from dgi.models import CompanyData
from dgi.services.dgi_criteria_service import DGICriteriaService
from dgi.services.scoring_service import DataFrameScoringService
from dgi.services.screening_parameter_validator import ScreeningParameterValidator

logger = logging.getLogger(__name__)


class ParameterValidator(Protocol):
    """Protocol for parameter validation services."""

    @staticmethod
    def validate_screening_parameters(
        min_yield: float, max_payout: float, min_cagr: float, top_n: int
    ) -> None:
        """Validate screening parameters."""
        ...


class CriteriaApplier(Protocol):
    """Protocol for criteria application services."""

    @staticmethod
    def apply_dgi_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply DGI criteria to DataFrame."""
        ...


class DataFrameScorer(Protocol):
    """Protocol for DataFrame scoring services."""

    @staticmethod
    def score_dataframe(df: DataFrame) -> DataFrame:
        """Score all rows in DataFrame."""
        ...


class ScreeningService:
    """Service class that coordinates screening business logic using injected dependencies."""

    def __init__(
        self,
        parameter_validator: ParameterValidator = ScreeningParameterValidator,
        criteria_applier: CriteriaApplier = DGICriteriaService,
        dataframe_scorer: DataFrameScorer = DataFrameScoringService,
    ) -> None:
        """Initialize the screening service with injected dependencies.

        Args:
            parameter_validator: Service for validating screening parameters
            criteria_applier: Service for applying DGI criteria
            dataframe_scorer: Service for scoring DataFrames
        """
        self._parameter_validator = parameter_validator
        self._criteria_applier = criteria_applier
        self._dataframe_scorer = dataframe_scorer

    def validate_screening_parameters(
        self, min_yield: float, max_payout: float, min_cagr: float, top_n: int
    ) -> None:
        """Validate screening parameters using injected validator."""
        self._parameter_validator.validate_screening_parameters(
            min_yield, max_payout, min_cagr, top_n
        )

    def apply_dgi_criteria(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply DGI criteria using injected criteria applier."""
        return self._criteria_applier.apply_dgi_criteria(
            df, min_yield, max_payout, min_cagr
        )

    def score_dataframe(self, df: DataFrame) -> DataFrame:
        """Score all rows in DataFrame using injected scoring service."""
        return self._dataframe_scorer.score_dataframe(df)

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
    def rows_to_dataframe(rows: list[CompanyData] | list[dict[str, Any]]) -> DataFrame:
        """Convert list of CompanyData objects or dictionaries to DataFrame with proper column names."""
        if not rows:
            return DataFrame()

        # Check if we're dealing with CompanyData objects or dictionaries
        data: list[dict[str, Any]] = []
        if isinstance(rows[0], CompanyData):
            # Convert CompanyData objects to dictionaries with the correct column names
            for row in rows:
                if isinstance(row, CompanyData):  # Type guard for mypy
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
            data = [dict(row) for row in rows]

        return DataFrame(data)

    @staticmethod
    def apply_screening_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply screening criteria to DataFrame using vectorized operations for better performance."""
        if df.empty:
            return df

        # Build boolean mask for vectorized filtering
        mask: Any = True  # Start with all rows included

        # Apply yield filter
        if "dividend_yield" in df.columns:
            mask &= df["dividend_yield"] >= min_yield

        # Apply payout filter
        if "payout" in df.columns:
            mask &= df["payout"] <= max_payout

        # Apply CAGR filter
        if "dividend_cagr" in df.columns:
            mask &= df["dividend_cagr"] >= min_cagr

        # Apply all filters at once
        filtered_df: DataFrame = df[mask]
        return filtered_df

    @staticmethod
    def convert_to_response_format(df: DataFrame) -> list[dict[str, Any]]:
        """Convert DataFrame to response format."""
        if df.empty:
            return []

        # Convert DataFrame to list of dictionaries
        raw_records = df.to_dict("records")
        records: list[dict[str, Any]] = []

        # Ensure all numeric values are properly formatted
        for record in raw_records:
            formatted_record: dict[str, Any] = {}
            for key, value in record.items():
                if isinstance(value, int | float):
                    formatted_record[str(key)] = float(value)
                else:
                    formatted_record[str(key)] = value
            records.append(formatted_record)

        return records

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

        metrics: dict[str, Any] = {
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
