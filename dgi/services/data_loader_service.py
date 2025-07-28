"""Data loading service with single responsibility for data access operations."""

import logging
from abc import ABC, abstractmethod

from pandas import DataFrame

from dgi.exceptions import DataLoadError
from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository

logger = logging.getLogger(__name__)


class DataLoader(ABC):
    """Abstract base class for data loading operations."""

    @abstractmethod
    def load_universe(self) -> DataFrame:
        """Load company universe data."""

    @abstractmethod
    async def load_universe_async(self) -> DataFrame:
        """Load company universe data asynchronously."""

    @abstractmethod
    def load_company_data(self) -> list[CompanyData]:
        """Load company data as structured objects."""

    @abstractmethod
    async def load_company_data_async(self) -> list[CompanyData]:
        """Load company data as structured objects asynchronously."""


class AsyncDataLoader(ABC):
    """Abstract base class for async data loading operations."""

    @abstractmethod
    async def load_universe_async(self) -> DataFrame:
        """Load company universe data asynchronously."""

    @abstractmethod
    async def load_company_data_async(self) -> list[CompanyData]:
        """Load company data as structured objects asynchronously."""


class RepositoryDataLoader(DataLoader):
    """Data loader that uses repository pattern for data access."""

    def __init__(self, repository: CompanyDataRepository):
        """Initialize with a data repository.

        Args:
            repository: Repository for data access operations
        """
        self._repository = repository

    def load_universe(self) -> DataFrame:
        """Load company universe data as DataFrame.

        Returns:
            DataFrame containing company data

        Raises:
            DataLoadError: If data loading fails
        """
        try:
            logger.info("Loading company universe data")
            company_data = self._repository.get_rows()

            if not company_data:
                logger.warning("No company data found")
                return DataFrame()

            # Convert to DataFrame using service layer
            from dgi.services.screening_service import ScreeningService

            df = ScreeningService.rows_to_dataframe(company_data)

            logger.info(f"Successfully loaded {len(df)} companies")
            return df

        except Exception as e:
            logger.error(f"Failed to load company universe: {e}")
            raise DataLoadError(f"Data loading failed: {e}") from e

    async def load_universe_async(self) -> DataFrame:
        """Load company universe data asynchronously.

        Returns:
            DataFrame containing company data

        Raises:
            DataLoadError: If data loading fails
        """
        try:
            logger.info("Loading company universe data asynchronously")
            company_data = await self._repository.get_rows_async()

            if not company_data:
                logger.warning("No company data found")
                return DataFrame()

            # Convert to DataFrame using service layer
            from dgi.services.screening_service import ScreeningService

            df = ScreeningService.rows_to_dataframe(company_data)

            logger.info(f"Successfully loaded {len(df)} companies asynchronously")
            return df

        except Exception as e:
            logger.error(f"Failed to load company universe asynchronously: {e}")
            raise DataLoadError(f"Async data loading failed: {e}") from e

    def load_company_data(self) -> list[CompanyData]:
        """Load company data as structured objects.

        Returns:
            List of CompanyData objects

        Raises:
            DataLoadError: If data loading fails
        """
        try:
            logger.info("Loading company data as structured objects")
            company_data = self._repository.get_rows()

            logger.info(f"Successfully loaded {len(company_data)} company objects")
            return company_data

        except Exception as e:
            logger.error(f"Failed to load company data: {e}")
            raise DataLoadError(f"Company data loading failed: {e}") from e

    async def load_company_data_async(self) -> list[CompanyData]:
        """Load company data as structured objects asynchronously.

        Returns:
            List of CompanyData objects

        Raises:
            DataLoadError: If data loading fails
        """
        try:
            logger.info("Loading company data as structured objects asynchronously")
            company_data = await self._repository.get_rows_async()

            logger.info(
                f"Successfully loaded {len(company_data)} company objects asynchronously"
            )
            return company_data

        except Exception as e:
            logger.error(f"Failed to load company data asynchronously: {e}")
            raise DataLoadError(f"Async company data loading failed: {e}") from e


class CachedDataLoader(DataLoader):
    """Data loader with caching capabilities."""

    def __init__(self, data_loader: DataLoader, cache_ttl: int = 300):
        """Initialize with underlying data loader and cache TTL.

        Args:
            data_loader: Underlying data loader
            cache_ttl: Cache time-to-live in seconds
        """
        self._data_loader = data_loader
        self._cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid.

        Args:
            key: Cache key

        Returns:
            True if cache is valid, False otherwise
        """
        if key not in self._cache_timestamps:
            return False

        import time

        return time.time() - self._cache_timestamps[key] < self._cache_ttl

    def load_universe(self) -> DataFrame:
        """Load company universe data with caching.

        Returns:
            DataFrame containing company data
        """
        cache_key = "universe"

        if self._is_cache_valid(cache_key):
            logger.info("Returning cached universe data")
            return self._cache[cache_key]

        logger.info("Loading fresh universe data")
        df = self._data_loader.load_universe()

        import time

        self._cache[cache_key] = df
        self._cache_timestamps[cache_key] = time.time()

        return df

    async def load_universe_async(self) -> DataFrame:
        """Load company universe data asynchronously with caching.

        Returns:
            DataFrame containing company data
        """
        cache_key = "universe_async"

        if self._is_cache_valid(cache_key):
            logger.info("Returning cached async universe data")
            return self._cache[cache_key]

        logger.info("Loading fresh async universe data")
        df = await self._data_loader.load_universe_async()

        import time

        self._cache[cache_key] = df
        self._cache_timestamps[cache_key] = time.time()

        return df

    def load_company_data(self) -> list[CompanyData]:
        """Load company data as structured objects with caching.

        Returns:
            List of CompanyData objects
        """
        cache_key = "company_data"

        if self._is_cache_valid(cache_key):
            logger.info("Returning cached company data")
            return self._cache[cache_key]

        logger.info("Loading fresh company data")
        data = self._data_loader.load_company_data()

        import time

        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()

        return data

    async def load_company_data_async(self) -> list[CompanyData]:
        """Load company data as structured objects asynchronously with caching.

        Returns:
            List of CompanyData objects
        """
        cache_key = "company_data_async"

        if self._is_cache_valid(cache_key):
            logger.info("Returning cached async company data")
            return self._cache[cache_key]

        logger.info("Loading fresh async company data")
        data = await self._data_loader.load_company_data_async()

        import time

        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()

        return data

    def clear_cache(self) -> None:
        """Clear all cached data."""
        logger.info("Clearing data cache")
        self._cache.clear()
        self._cache_timestamps.clear()
