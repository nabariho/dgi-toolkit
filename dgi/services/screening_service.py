"""Screening service for business logic separation."""

import logging
from typing import Any

import pandas as pd
from pandas import DataFrame

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
            raise ValueError("min_yield must be non-negative")
        if max_payout < 0 or max_payout > 100:
            raise ValueError("max_payout must be between 0 and 100")
        if min_cagr < 0:
            raise ValueError("min_cagr must be non-negative")
        if top_n < 1:
            raise ValueError("top_n must be at least 1")

    @staticmethod
    def calculate_composite_score(company: CompanyData) -> float:
        """Calculate composite score for a company using business rules."""
        # Business logic: 40% yield, 30% payout sustainability, 30% growth
        yield_score = company.dividend_yield * 0.4
        payout_score = (1 - company.payout_ratio / 100) * 0.3
        growth_score = company.dividend_growth_5y * 0.3

        return yield_score + payout_score + growth_score

    @staticmethod
    def score_dataframe(df: DataFrame) -> DataFrame:
        """Score all companies in a DataFrame using business rules."""
        df = df.copy()

        # Handle empty DataFrame
        if df.empty:
            df["score"] = []
            return df

        # Apply business scoring logic
        df["score"] = (
            df["dividend_yield"] * 0.4
            + (1 - df["payout"] / 100) * 0.3
            + df["dividend_cagr"] * 0.3
        )

        return df

    @staticmethod
    def get_top_stocks(df: DataFrame, top_n: int) -> DataFrame:
        """Get top N stocks based on score using business rules."""
        if df.empty:
            return df

        # Business rule: Sort by score descending and take top N
        return df.nlargest(top_n, "score")

    @staticmethod
    def apply_screening_criteria(
        df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply screening criteria using business rules."""
        # Business logic: Apply DGI criteria filters
        mask = (
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        )

        return df[mask].copy()

    @staticmethod
    def convert_to_response_format(df: DataFrame) -> list[dict[str, Any]]:
        """Convert DataFrame to API response format using business rules."""
        return [
            {
                "symbol": row["symbol"],
                "name": row["name"],
                "sector": row["sector"],
                "industry": row["industry"],
                "dividend_yield": float(row["dividend_yield"]),
                "payout": float(row["payout"]),
                "dividend_cagr": float(row["dividend_cagr"]),
                "fcf_yield": float(row["fcf_yield"]),
                "score": float(row["score"]),
            }
            for _, row in df.iterrows()
        ]

    @staticmethod
    def rows_to_dataframe(rows: list[CompanyData]) -> DataFrame:
        """Convert CompanyData objects to DataFrame using business rules."""
        data = []
        for row in rows:
            data.append(
                {
                    "symbol": row.symbol,
                    "name": row.name,
                    "sector": row.sector,
                    "industry": row.industry,
                    "dividend_yield": row.dividend_yield,
                    "payout": row.payout_ratio,
                    "dividend_cagr": row.dividend_growth_5y,
                    "fcf_yield": row.fcf_yield,
                }
            )
        return pd.DataFrame(data)
