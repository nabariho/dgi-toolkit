# screener.py

import pandas as pd
from pandas import DataFrame
import logging
from typing import Callable, Any, Optional, List
from dgi.models import CompanyData
from dgi.validation import DgiRowValidator
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository

logger = logging.getLogger(__name__)


class Screener:
    """
    Enterprise-ready screener for Dividend Growth Investing (DGI).
    Encapsulates universe loading, filtering, and scoring with pluggable validation and scoring strategies.
    """

    def __init__(
        self,
        repository: CompanyDataRepository,
        scorer: Optional[Callable[[CompanyData], float]] = None,
    ) -> None:
        self.repository = repository
        self.scorer = scorer or Screener.default_score

    @staticmethod
    def rows_to_dataframe(rows: List[CompanyData]) -> DataFrame:
        df = pd.DataFrame([row.dict() for row in rows])
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
            f"Loading universe from repository: {type(self.repository).__name__}"
        )
        rows = self.repository.get_rows()
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
        filtered = df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]
        logger.info(f"Filtered universe to {len(filtered)} rows")
        return filtered

    def add_scores(self, df: DataFrame) -> DataFrame:
        logger.info("Scoring DataFrame rows")
        df = df.copy()
        df["score"] = df.apply(self.scorer, axis=1)
        return df

    @staticmethod
    def default_score(row: Any) -> float:
        cagr_norm = min(max(row["dividend_cagr"] / 20.0, 0.0), 1.0)
        fcf_norm = min(max(row["fcf_yield"] / 20.0, 0.0), 1.0)
        payout_norm = min(max(row["payout"] / 100.0, 0.0), 1.0)
        composite = cagr_norm + fcf_norm - payout_norm
        composite = composite / 3.0
        result = max(0.0, min(composite, 1.0))
        return float(result)


# For backward compatibility, provide functional API using CSV repository
_default_validator = DgiRowValidator()
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


def score(row: Any) -> float:
    return _default_screener.default_score(row)
