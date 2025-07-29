"""DGI Screener with modern service architecture using dependency injection."""

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
from dgi.services.api_response_mapper_service import ScreeningResponseMapper
from dgi.services.data_loader_service import DataLoader, RepositoryDataLoader
from dgi.services.resource_manager_service import ResourceManager
from dgi.services.screening_service import ScreeningService
from dgi.validation_utils import DgiRowValidator, PydanticRowValidation

# Get configuration for default values
config = get_config()

logger = logging.getLogger(__name__)


class CompanyFilter(Protocol):
    """Protocol for company filtering strategies."""

    def filter(self, companies: list[CompanyData]) -> list[CompanyData]: ...


class Screener:
    """Screen companies based on DGI criteria using modern service architecture."""

    def __init__(
        self,
        repository: CompanyDataRepository,
        filters: list[CompanyFilter] | None = None,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
        screening_service: ScreeningService | None = None,
        data_loader: DataLoader | None = None,
        resource_manager: ResourceManager | None = None,
        response_mapper: ScreeningResponseMapper | None = None,
    ) -> None:
        """Initialize screener with dependency injection.

        Args:
            repository: Data repository for loading company data
            filters: Optional list of company filters
            scoring_strategy: Optional scoring strategy
            filter_strategy: Optional filter strategy
            screening_service: Injected screening service (creates default if None)
            data_loader: Injected data loader service (creates default if None)
            resource_manager: Injected resource manager (creates default if None)
            response_mapper: Injected response mapper (creates default if None)
        """
        self._repository = repository
        self._filters = filters or []
        self._scoring_strategy = scoring_strategy
        self._filter_strategy = filter_strategy or DefaultFilter()

        # Use dependency injection for focused services
        self._screening_service = screening_service or ScreeningService()
        self._data_loader = data_loader or RepositoryDataLoader(repository)
        self._resource_manager = resource_manager or ResourceManager()
        self._response_mapper = response_mapper or ScreeningResponseMapper()

    # Compatibility methods for backward compatibility during refactoring
    def load_universe(self) -> DataFrame:
        """Load and validate the raw fundamentals universe (compatibility method).

        This method is maintained for backward compatibility during refactoring.
        It delegates to the focused data loader service.
        """
        return self._data_loader.load_universe()

    async def load_universe_async(self) -> DataFrame:
        """Load and validate the raw fundamentals universe asynchronously (compatibility method).

        This method is maintained for backward compatibility during refactoring.
        It delegates to the focused data loader service.
        """
        return await self._data_loader.load_universe_async()

    def default_score(self, company: CompanyData) -> float:
        """Calculate a default score for a company (compatibility method).

        This method is maintained for backward compatibility during refactoring.
        It delegates to the screening service.
        """
        return ScreeningService.calculate_composite_score(company)

    def rows_to_dataframe(self, rows: list[CompanyData]) -> DataFrame:
        """Convert CompanyData objects to DataFrame (compatibility method).

        This method is maintained for backward compatibility during refactoring.
        It delegates to the screening service.
        """
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

        # Validate parameters using injected service
        self._screening_service.validate_screening_parameters(
            min_yield, max_payout, min_cagr, top_n
        )

        # Load universe using focused data loader service
        df = self._data_loader.load_universe()

        # Track resource usage
        self._resource_manager.track_resource(df)

        # Apply filters using injected service
        filtered = self._screening_service.apply_dgi_criteria(
            df, min_yield, max_payout, min_cagr
        )

        # Add scores using injected service
        scored = self._screening_service.score_dataframe(filtered)

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

        # Validate parameters using injected service
        self._screening_service.validate_screening_parameters(
            min_yield, max_payout, min_cagr, top_n
        )

        try:
            # Load universe asynchronously using focused data loader service
            df = await self._data_loader.load_universe_async()

            # Track resource usage
            self._resource_manager.track_resource(df)

            # Apply filters (this is CPU-bound, so we run it in thread pool)
            loop = asyncio.get_event_loop()
            filtered = await loop.run_in_executor(
                None,
                self._screening_service.apply_dgi_criteria,
                df,
                min_yield,
                max_payout,
                min_cagr,
            )

            # Add scores (this is CPU-bound, so we run it in thread pool)
            scored = await loop.run_in_executor(
                None, self._screening_service.score_dataframe, filtered
            )

            # Return top N using service layer
            return await loop.run_in_executor(
                None, ScreeningService.get_top_stocks, scored, top_n
            )

        except Exception as e:
            logger.error(f"Async screening failed: {e}")
            raise

    def apply_filters(
        self,
        df: DataFrame,
        min_yield: float = config.DEFAULT_SCREEN_MIN_YIELD,
        max_payout: float = config.DEFAULT_SCREEN_MAX_PAYOUT,
        min_cagr: float = config.DEFAULT_SCREEN_MIN_CAGR,
    ) -> DataFrame:
        """Apply filters using the configured filter strategy."""
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
        """Add scores to DataFrame using injected service."""
        logger.info("Scoring DataFrame rows")
        return self._screening_service.score_dataframe(df)


# For backward compatibility, provide functional API using CSV repository
_default_validator = DgiRowValidator(PydanticRowValidation(CompanyData))
_default_repo = CsvCompanyDataRepository(
    "data/fundamentals_small.csv", _default_validator
)
_default_screener = Screener(_default_repo)


def load_universe(csv_path: str = "data/fundamentals_small.csv") -> DataFrame:
    """Load universe from CSV file with validation."""
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
    """Load universe from CSV file asynchronously with validation."""
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
