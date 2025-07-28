# screener.py

import asyncio
import logging
from typing import Protocol

from pandas import DataFrame

from dgi.config import get_config
from dgi.filtering import BaseFilter, DefaultFilter
from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import ScoringStrategy
from dgi.services.screening_service import ScreeningService
from dgi.validation import DgiRowValidator, PydanticRowValidation

# Get configuration for default values
config = get_config()

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
        filter_strategy: BaseFilter | None = None,
    ) -> None:
        self._repository = repository
        self._filters = filters or []
        self._scoring_strategy = scoring_strategy
        self._filter_strategy = filter_strategy or DefaultFilter()

    def default_score(self, company: CompanyData) -> float:
        """Calculate a default score for a company using the service layer."""
        return ScreeningService.calculate_composite_score(company)

    @staticmethod
    def rows_to_dataframe(rows: list[CompanyData]) -> DataFrame:
        """Convert CompanyData objects to DataFrame using service layer."""
        return ScreeningService.rows_to_dataframe(rows)

    def screen(
        self,
        min_yield: float = config.DEFAULT_SCREEN_MIN_YIELD,
        max_payout: float = config.DEFAULT_SCREEN_MAX_PAYOUT,
        min_cagr: float = config.DEFAULT_SCREEN_MIN_CAGR,
        top_n: int = config.DEFAULT_TOP_N,
    ) -> DataFrame:
        """Screen companies using DGI criteria and return top N results."""
        logger.info(
            "Screening with parameters: min_yield=%s, max_payout=%s, min_cagr=%s, top_n=%s",
            min_yield,
            max_payout,
            min_cagr,
            top_n,
        )

        # Validate parameters using service layer
        ScreeningService.validate_screening_parameters(
            min_yield, max_payout, min_cagr, top_n
        )

        # Load universe
        df = self.load_universe()

        # Apply filters
        filtered = self.apply_filters(df, min_yield, max_payout, min_cagr)

        # Add scores
        scored = self.add_scores(filtered)

        # Return top N using service layer
        return ScreeningService.get_top_stocks(scored, top_n)

    async def screen_async(
        self,
        min_yield: float = config.DEFAULT_SCREEN_MIN_YIELD,
        max_payout: float = config.DEFAULT_SCREEN_MAX_PAYOUT,
        min_cagr: float = config.DEFAULT_SCREEN_MIN_CAGR,
        top_n: int = config.DEFAULT_TOP_N,
    ) -> DataFrame:
        """Screen companies asynchronously using DGI criteria and return top N results."""
        logger.info(
            "Async screening with parameters: min_yield=%s, max_payout=%s, min_cagr=%s, top_n=%s",
            min_yield,
            max_payout,
            min_cagr,
            top_n,
        )

        # Validate parameters using service layer
        ScreeningService.validate_screening_parameters(
            min_yield, max_payout, min_cagr, top_n
        )

        try:
            # Load universe asynchronously
            df = await self.load_universe_async()

            # Apply filters (this is CPU-bound, so we run it in thread pool)
            loop = asyncio.get_event_loop()
            filtered = await loop.run_in_executor(
                None, self.apply_filters, df, min_yield, max_payout, min_cagr
            )

            # Add scores (this is CPU-bound, so we run it in thread pool)
            scored = await loop.run_in_executor(None, self.add_scores, filtered)

            # Return top N using service layer
            return await loop.run_in_executor(
                None, ScreeningService.get_top_stocks, scored, top_n
            )

        except Exception as e:
            logger.error(f"Async screening failed: {e}")
            raise

    def load_universe(self) -> DataFrame:
        """
        Load and validate the raw fundamentals universe.
        Returns a DataFrame with correct types, ready for screening.
        Raises ValueError if validation fails or no valid rows are found.
        """
        logger.info(
            f"Loading universe from repository: {type(self._repository).__name__}"
        )
        rows = self._repository.get_rows()
        logger.info(f"Successfully loaded {len(rows)} valid rows from repository")
        return self.rows_to_dataframe(rows)

    async def load_universe_async(self) -> DataFrame:
        """
        Load and validate the raw fundamentals universe asynchronously.
        Returns a DataFrame with correct types, ready for screening.
        Raises ValueError if validation fails or no valid rows are found.
        """
        logger.info(
            f"Loading universe asynchronously from repository: {type(self._repository).__name__}"
        )
        rows = await self._repository.get_rows_async()
        logger.info(f"Successfully loaded {len(rows)} valid rows from repository")
        return self.rows_to_dataframe(rows)

    def apply_filters(
        self,
        df: DataFrame,
        min_yield: float = config.DEFAULT_SCREEN_MIN_YIELD,
        max_payout: float = config.DEFAULT_SCREEN_MAX_PAYOUT,
        min_cagr: float = config.DEFAULT_SCREEN_MIN_CAGR,
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
        """Add scores to DataFrame using service layer."""
        logger.info("Scoring DataFrame rows")
        return ScreeningService.score_dataframe(df)


# For backward compatibility, provide functional API using CSV repository
_default_validator = DgiRowValidator(PydanticRowValidation(CompanyData))
_default_repo = CsvCompanyDataRepository(
    "data/fundamentals_small.csv", _default_validator
)
_default_screener = Screener(_default_repo)


def load_universe(csv_path: str = "data/fundamentals_small.csv") -> DataFrame:
    # Validate the CSV path before creating the repository
    from dgi.validation_utils import PathValidationError, validate_file_path

    try:
        validated_path = validate_file_path(csv_path, allowed_extensions=[".csv"])
    except PathValidationError as e:
        raise ValueError(f"Invalid CSV file path: {e.message}") from e

    repo = CsvCompanyDataRepository(validated_path, _default_validator)
    screener = Screener(repo)
    return screener.load_universe()


async def load_universe_async(
    csv_path: str = "data/fundamentals_small.csv",
) -> DataFrame:
    # Validate the CSV path before creating the repository
    from dgi.validation_utils import PathValidationError, validate_file_path

    try:
        validated_path = validate_file_path(csv_path, allowed_extensions=[".csv"])
    except PathValidationError as e:
        raise ValueError(f"Invalid CSV file path: {e.message}") from e

    repo = CsvCompanyDataRepository(validated_path, _default_validator)
    screener = Screener(repo)
    return await screener.load_universe_async()


def score(company: CompanyData) -> float:
    """Calculate a default score for a company using the service layer."""
    return ScreeningService.calculate_composite_score(company)
