"""Dependency injection container for DGI Toolkit API."""

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
    """Container for managing dependency lifecycle."""

    def __init__(self):
        """Initialize dependency container."""
        self._screener = None
        self._repository = None
        self._validator = None

    def get_screener(self) -> Screener:
        """Get screener with singleton pattern.

        Returns:
            Screener instance
        """
        if self._screener is None:
            self._screener = get_production_screener()
        return self._screener

    def get_repository(self) -> CsvCompanyDataRepository:
        """Get repository with singleton pattern.

        Returns:
            CsvCompanyDataRepository instance
        """
        if self._repository is None:
            self._repository = get_data_repository()
        return self._repository

    def reset(self) -> None:
        """Reset all dependencies (useful for testing)."""
        self._screener = None
        self._repository = None
        self._validator = None
        logger.info("Dependency container reset")


# Global dependency container
dependency_container = DependencyContainer()


def get_dependency_container() -> DependencyContainer:
    """Get global dependency container.

    Returns:
        DependencyContainer instance
    """
    return dependency_container
