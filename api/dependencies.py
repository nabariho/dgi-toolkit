"""Dependency injection container for DGI Toolkit API."""

import threading
from typing import Any

from fastapi import Depends

from dgi.factory import create_repository, create_screener
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.screener import Screener

from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


def get_settings_dependency():
    """Get settings dependency.

    Returns:
        APISettings instance
    """
    return get_settings()


def get_data_repository() -> CompanyDataRepository:
    """Get data repository dependency.

    Returns:
        Configured CompanyDataRepository instance
    """
    settings = get_settings()

    # Use factory to create repository
    repository = create_repository(settings.data_path, "production")

    logger.info(f"Created data repository with path: {settings.data_path}")
    return repository


def get_screener(
    repository: CompanyDataRepository = Depends(get_data_repository),
) -> Screener:
    """Get screener dependency.

    Args:
        repository: Data repository dependency

    Returns:
        Configured Screener instance
    """
    # Use factory to create screener
    screener = create_screener(repository, factory_name="production")

    logger.info("Created screener with default scoring strategy")
    return screener


def get_validator():
    """Get validator dependency.

    Returns:
        Configured DgiRowValidator instance
    """
    from dgi.factory import create_validator

    validator = create_validator("production")
    logger.debug("Created data validator")
    return validator


def get_scoring_strategy():
    """Get scoring strategy dependency.

    Returns:
        ScoringStrategy instance
    """
    from dgi.factory import create_scoring_strategy

    return create_scoring_strategy("production")


# Dependency providers for different configurations
def get_production_screener() -> Screener:
    """Get production screener with optimized configuration.

    Returns:
        Screener configured for production use
    """
    settings = get_settings()

    # Use factory to create production screener
    repository = create_repository(settings.data_path, "production")
    screener = create_screener(repository, factory_name="production")

    logger.info("Created production screener")
    return screener


def get_test_screener() -> Screener:
    """Get test screener with test configuration.

    Returns:
        Screener configured for testing
    """
    settings = get_settings()

    # Use factory to create test screener
    repository = create_repository(settings.data_path, "test")
    screener = create_screener(repository, factory_name="test")

    logger.info("Created test screener")
    return screener


# Dependency lifecycle management
class DependencyContainer:
    """Container for managing dependency lifecycle with thread safety."""

    def __init__(self):
        """Initialize dependency container with thread safety."""
        self._screener: Screener | None = None
        self._repository: CsvCompanyDataRepository | None = None
        self._validator: Any = None
        self._lock = threading.RLock()  # Reentrant lock for thread safety

    def get_screener(self) -> Screener:
        """Get screener with thread-safe singleton pattern.

        Returns:
            Screener instance
        """
        with self._lock:
            if self._screener is None:
                self._screener = get_production_screener()
            return self._screener

    def get_repository(self) -> CsvCompanyDataRepository:
        """Get repository with thread-safe singleton pattern.

        Returns:
            CsvCompanyDataRepository instance
        """
        with self._lock:
            if self._repository is None:
                self._repository = get_data_repository()
            return self._repository

    def get_validator(self) -> Any:
        """Get validator with thread-safe singleton pattern.

        Returns:
            Validator instance
        """
        with self._lock:
            if self._validator is None:
                self._validator = get_validator()
            return self._validator

    def reset(self) -> None:
        """Reset all dependencies (useful for testing) with thread safety."""
        with self._lock:
            self._screener = None
            self._repository = None
            self._validator = None
            logger.info("Dependency container reset")

    def cleanup(self) -> None:
        """Clean up resources and perform proper shutdown."""
        with self._lock:
            if self._repository is not None:
                try:
                    self._repository.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up repository: {e}")

            self._screener = None
            self._repository = None
            self._validator = None
            logger.info("Dependency container cleaned up")


# Global dependency container
dependency_container = DependencyContainer()


def get_dependency_container() -> DependencyContainer:
    """Get global dependency container.

    Returns:
        DependencyContainer instance
    """
    return dependency_container


# Dependency scoping utilities
class DependencyScope:
    """Context manager for dependency scoping."""

    def __init__(self, container: DependencyContainer):
        """Initialize dependency scope."""
        self.container = container
        self._original_screener = None
        self._original_repository = None

    def __enter__(self):
        """Enter dependency scope."""
        # Store original dependencies
        self._original_screener = self.container._screener
        self._original_repository = self.container._repository

        # Reset for new scope
        self.container._screener = None
        self.container._repository = None

        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit dependency scope."""
        # Restore original dependencies
        self.container._screener = self._original_screener
        self.container._repository = self._original_repository


def get_scoped_dependencies() -> DependencyScope:
    """Get scoped dependencies for request-level isolation.

    Returns:
        DependencyScope context manager
    """
    return DependencyScope(dependency_container)
