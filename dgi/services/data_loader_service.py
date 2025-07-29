"""Data loading service with single responsibility for data access operations."""

import logging
from abc import ABC, abstractmethod
from typing import Any, cast

from pandas import DataFrame

from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository

logger = logging.getLogger(__name__)


class DataLoader(ABC):
    """Abstract interface for data loading operations."""

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
    """Abstract interface for async data loading operations."""

    @abstractmethod
    async def load_universe_async(self) -> DataFrame:
        """Load company universe data asynchronously."""

    @abstractmethod
    async def load_company_data_async(self) -> list[CompanyData]:
        """Load company data as structured objects asynchronously."""


class RepositoryDataLoader(DataLoader):
    """Data loader that uses a repository for data access."""

    def __init__(self, repository: CompanyDataRepository):
        """Initialize with a repository.

        Args:
            repository: Repository for data access
        """
        self._repository = repository

    def load_universe(self) -> DataFrame:
        """Load company universe data from repository.

        Returns:
            DataFrame containing company data
        """
        try:
            companies = self._repository.get_rows()
            if not companies:
                logger.warning("No companies found in repository")
                return DataFrame()

            # Convert to DataFrame
            data = []
            for company in companies:
                data.append(company.model_dump())

            df = DataFrame(data)
            logger.info(f"Loaded {len(df)} companies from repository")
            return df

        except Exception as e:
            logger.error(f"Error loading universe data: {e}")
            raise

    async def load_universe_async(self) -> DataFrame:
        """Load company universe data asynchronously from repository.

        Returns:
            DataFrame containing company data
        """
        try:
            companies = await self._repository.get_rows_async()
            if not companies:
                logger.warning("No companies found in repository")
                return DataFrame()

            # Convert to DataFrame
            data = []
            for company in companies:
                data.append(company.model_dump())

            df = DataFrame(data)
            logger.info(f"Loaded {len(df)} companies from repository (async)")
            return df

        except Exception as e:
            logger.error(f"Error loading universe data (async): {e}")
            raise

    def load_company_data(self) -> list[CompanyData]:
        """Load company data as structured objects from repository.

        Returns:
            List of CompanyData objects
        """
        try:
            companies = self._repository.get_rows()
            logger.info(f"Loaded {len(companies)} company objects from repository")
            return companies

        except Exception as e:
            logger.error(f"Error loading company data: {e}")
            raise

    async def load_company_data_async(self) -> list[CompanyData]:
        """Load company data as structured objects asynchronously from repository.

        Returns:
            List of CompanyData objects
        """
        try:
            companies = await self._repository.get_rows_async()
            logger.info(
                f"Loaded {len(companies)} company objects from repository (async)"
            )
            return companies

        except Exception as e:
            logger.error(f"Error loading company data (async): {e}")
            raise


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
        self._cache: dict[str, Any] = {}
        self._cache_timestamps: dict[str, float] = {}

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
            return cast(DataFrame, self._cache[cache_key])

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
            return cast(DataFrame, self._cache[cache_key])

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
            return cast(list[CompanyData], self._cache[cache_key])

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
            return cast(list[CompanyData], self._cache[cache_key])

        logger.info("Loading fresh async company data")
        data = await self._data_loader.load_company_data_async()

        import time

        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()

        return data

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache cleared")
