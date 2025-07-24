# screener.py

import logging
from typing import Any, Protocol

import pandas as pd
from pandas import DataFrame

from dgi.filtering import DefaultFilter, FilterStrategy
from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import ScoringStrategy
from dgi.validation import DgiRowValidator, PydanticRowValidation

logger = logging.getLogger(__name__)


class CompanyFilter(Protocol):
    """Protocol for company filtering strategies."""

    def filter(self, companies: list[CompanyData]) -> list[CompanyData]: ...


class Screener:
    """Screen companies based on DGI criteria."""

    def __init__(
        self,
        repository: CompanyDataRepository,
        filters: list[CompanyFilter] | None = None,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: FilterStrategy | None = None,
    ) -> None:
        self._repository = repository
        self._filters = filters or []
        self._scoring_strategy = scoring_strategy
        self._filter_strategy = filter_strategy or DefaultFilter()

    def default_score(self, company: CompanyData) -> float:
        """Calculate a default score for a company."""
        # Simple scoring based on yield and growth
        # Convert to decimals if needed - assume input is already in correct format
        yield_score = float(company.dividend_yield) * 1.0  # Use yield as-is
        growth_score = float(company.dividend_growth_5y) * 0.5  # Scale growth
        payout_penalty = (
            max(0, float(company.payout_ratio) - 60.0) * -0.1
        )  # Penalize high payout over 60%
        return float(yield_score + growth_score + payout_penalty)

    @staticmethod
    def rows_to_dataframe(rows: list[CompanyData]) -> DataFrame:
        # Convert to dict and then create mapping to use alias names
        data_for_df = []
        for row in rows:
            row_dict = row.model_dump()
            # Map back to alias names for DataFrame columns
            mapped_dict = {
                "symbol": row_dict["symbol"],
                "name": row_dict["name"],
                "sector": row_dict["sector"],
                "industry": row_dict["industry"],
                "dividend_yield": row_dict["dividend_yield"],
                "payout": row_dict["payout_ratio"],  # Map back to alias
                "dividend_cagr": row_dict["dividend_growth_5y"],  # Map back to alias
                "fcf_yield": row_dict["fcf_yield"],
            }
            data_for_df.append(mapped_dict)

        df = pd.DataFrame(data_for_df)
        expected_columns = [
            "symbol",
            "name",
            "sector",
            "industry",
            "dividend_yield",
            "payout",
            "dividend_cagr",
            "fcf_yield",
        ]
        if df.empty or any(col not in df.columns for col in expected_columns):
            missing = [col for col in expected_columns if col not in df.columns]
            raise ValueError(
                "Missing expected columns in validated data: "
                f"{', '.join(missing)} or no valid rows found."
            )
        df = df[expected_columns]
        return df

    def load_universe(self) -> DataFrame:
        """
        Load and validate the raw fundamentals universe for DGI analysis from the repository.
        Returns a DataFrame with correct types, ready for screening.
        Raises ValueError if validation fails or no valid rows are found.
        """
        logger.info(
            f"Loading universe from repository: {type(self._repository).__name__}"
        )
        rows = self._repository.get_rows()
        logger.info(f"Successfully loaded {len(rows)} valid rows from repository")
        return self.rows_to_dataframe(rows)

    def apply_filters(
        self,
        df: DataFrame,
        min_yield: float = 0.0,
        max_payout: float = 100.0,
        min_cagr: float = 0.0,
    ) -> DataFrame:
        logger.info(
            "Applying filters: min_yield=%s, max_payout=%s, min_cagr=%s",
            min_yield,
            max_payout,
            min_cagr,
        )
        # Use the filter strategy instead of hardcoded logic
        filtered = self._filter_strategy.filter(df, min_yield, max_payout, min_cagr)
        logger.info(f"Filtered to {len(filtered)} rows from {len(df)} rows")
        return filtered

    def add_scores(self, df: DataFrame) -> DataFrame:
        logger.info("Scoring DataFrame rows")
        df = df.copy()

        # Handle empty DataFrame
        if df.empty:
            df["score"] = []  # Add empty score column
            return df

        # Convert each row to CompanyData and score
        def score_row(row: Any) -> float:
            try:
                company = CompanyData(**row.to_dict())
                if self._scoring_strategy:
                    score = self._scoring_strategy.score(company)
                else:
                    score = self.default_score(company)
                return float(score)  # Ensure we return a scalar float
            except Exception as e:
                logger.error(f"Error scoring row: {e}")
                return 0.0

        df["score"] = df.apply(score_row, axis=1)
        return df


# For backward compatibility, provide functional API using CSV repository
_default_validator = DgiRowValidator(PydanticRowValidation(CompanyData))
_default_repo = CsvCompanyDataRepository(
    "data/fundamentals_small.csv", _default_validator
)
_default_screener = Screener(_default_repo)


def load_universe(csv_path: str = "data/fundamentals_small.csv") -> DataFrame:
    repo = CsvCompanyDataRepository(csv_path, _default_validator)
    screener = Screener(repo)
    return screener.load_universe()


def apply_filters(
    df: DataFrame,
    min_yield: float = 0.0,
    max_payout: float = 100.0,
    min_cagr: float = 0.0,
) -> DataFrame:
    return _default_screener.apply_filters(df, min_yield, max_payout, min_cagr)


def score(company: CompanyData) -> float:
    return _default_screener.default_score(company)
