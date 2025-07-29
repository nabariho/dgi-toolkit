from abc import ABC, abstractmethod
from typing import Protocol

from dgi.models import CompanyData


class CompanyDataRepository(ABC):
    """Abstract base class for company data repositories."""

    @abstractmethod
    def get_rows(self) -> list[CompanyData]:
        """Get all company data rows synchronously."""

    async def get_rows_async(self) -> list[CompanyData]:
        """Get all company data rows asynchronously.

        Default implementation runs the sync method in a thread pool.
        Override for better async performance if needed.
        """
        import asyncio
        import logging

        logger = logging.getLogger(__name__)

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.get_rows)
        except Exception as e:
            logger.error(f"Async data loading failed: {e}")
            raise


class AsyncCompanyDataRepository(Protocol):
    """Protocol for async company data repositories."""

    async def get_rows_async(self) -> list[CompanyData]:
        """Get all company data rows asynchronously."""
        ...
