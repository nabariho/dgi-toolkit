"""Segregated repository interfaces following Interface Segregation Principle.

This module provides focused interfaces that don't force clients to depend on
methods they don't use, following the ISP principle.
"""

from collections.abc import Iterator
from typing import Protocol

from dgi.models import CompanyData


class ReadOnlyRepository(Protocol):
    """Protocol for read-only data access."""

    def get_rows(self) -> list[CompanyData]:
        """Get all company data rows."""
        ...


class AsyncReadOnlyRepository(Protocol):
    """Protocol for async read-only data access."""

    async def get_rows_async(self) -> list[CompanyData]:
        """Get all company data rows asynchronously."""
        ...


class WriteableRepository(Protocol):
    """Protocol for write operations."""

    def save_rows(self, companies: list[CompanyData]) -> None:
        """Save company data rows."""
        ...

    def save_row(self, company: CompanyData) -> None:
        """Save a single company data row."""
        ...


class AsyncWriteableRepository(Protocol):
    """Protocol for async write operations."""

    async def save_rows_async(self, companies: list[CompanyData]) -> None:
        """Save company data rows asynchronously."""
        ...

    async def save_row_async(self, company: CompanyData) -> None:
        """Save a single company data row asynchronously."""
        ...


class CacheableRepository(Protocol):
    """Protocol for repositories that support caching."""

    def clear_cache(self) -> None:
        """Clear the repository cache."""
        ...

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        ...


class StreamingRepository(Protocol):
    """Protocol for streaming data access."""

    def stream_rows(self, batch_size: int = 1000) -> Iterator[list[CompanyData]]:
        """Stream company data in batches."""
        ...


class QueryableRepository(Protocol):
    """Protocol for repositories that support querying."""

    def find_by_symbol(self, symbol: str) -> CompanyData | None:
        """Find company by symbol."""
        ...

    def find_by_sector(self, sector: str) -> list[CompanyData]:
        """Find companies by sector."""
        ...

    def count_rows(self) -> int:
        """Count total number of rows."""
        ...


class TransactionalRepository(Protocol):
    """Protocol for repositories that support transactions."""

    def begin_transaction(self) -> None:
        """Begin a transaction."""
        ...

    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        ...

    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        ...


class MetadataRepository(Protocol):
    """Protocol for repository metadata operations."""

    def get_schema(self) -> dict[str, str]:
        """Get the data schema."""
        ...

    def get_last_updated(self) -> str:
        """Get last update timestamp."""
        ...

    def validate_data_integrity(self) -> bool:
        """Validate data integrity."""
        ...


# Composed interfaces for common use cases
class BasicRepository(ReadOnlyRepository, Protocol):
    """Basic repository for simple read-only access."""


class StandardRepository(ReadOnlyRepository, WriteableRepository, Protocol):
    """Standard repository with read and write capabilities."""


class AsyncRepository(AsyncReadOnlyRepository, AsyncWriteableRepository, Protocol):
    """Async repository with read and write capabilities."""


class CachedRepository(ReadOnlyRepository, CacheableRepository, Protocol):
    """Repository with caching capabilities."""


class FullFeaturedRepository(
    ReadOnlyRepository,
    WriteableRepository,
    QueryableRepository,
    CacheableRepository,
    MetadataRepository,
    Protocol,
):
    """Full-featured repository with all capabilities."""


# Backwards compatibility adapter
class LegacyRepositoryAdapter:
    """Adapter to maintain backwards compatibility with existing repository interface."""

    def __init__(self, read_repo: ReadOnlyRepository) -> None:
        """Initialize adapter with segregated repositories.

        Args:
            read_repo: Repository for read operations
        """
        self._read_repo = read_repo

    def get_rows(self) -> list[CompanyData]:
        """Get all company data rows (delegated to read repository)."""
        return self._read_repo.get_rows()

    async def get_rows_async(self) -> list[CompanyData]:
        """Get all company data rows asynchronously."""
        import asyncio
        import logging

        logger = logging.getLogger(__name__)

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.get_rows)
        except Exception as e:
            logger.error(f"Async data loading failed: {e}")
            raise
