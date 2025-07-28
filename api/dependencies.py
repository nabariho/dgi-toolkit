"""Dependency injection container for DGI Toolkit API."""

from fastapi import Depends

from dgi.models.company import CompanyData
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring
from dgi.screener import Screener
from dgi.validation import DgiRowValidator, PydanticRowValidation

from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


def get_settings_dependency():
    """Get settings dependency.

    Returns:
        APISettings instance
    """
    return get_settings()


def get_data_repository() -> CsvCompanyDataRepository:
    """Get data repository dependency.

    Returns:
        Configured CsvCompanyDataRepository instance
    """
    settings = get_settings()

    # Create validator
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))

    # Create repository with configured data path
    repository = CsvCompanyDataRepository(settings.data_path, validator)

    logger.info(f"Created data repository with path: {settings.data_path}")
    return repository


def get_screener(
    repository: CsvCompanyDataRepository = Depends(get_data_repository),
) -> Screener:
    """Get screener dependency.

    Args:
        repository: Data repository dependency

    Returns:
        Configured Screener instance
    """
    # Create scoring strategy
    scoring_strategy = DefaultScoring()

    # Create screener with dependencies
    screener = Screener(repository=repository, scoring_strategy=scoring_strategy)

    logger.info("Created screener with default scoring strategy")
    return screener


def get_validator() -> DgiRowValidator:
    """Get validator dependency.

    Returns:
        Configured DgiRowValidator instance
    """
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    logger.debug("Created data validator")
    return validator


def get_scoring_strategy() -> DefaultScoring:
    """Get scoring strategy dependency.

    Returns:
        DefaultScoring instance
    """
    return DefaultScoring()


# Dependency providers for different configurations
def get_production_screener() -> Screener:
    """Get production screener with optimized configuration.

    Returns:
        Screener configured for production use
    """
    settings = get_settings()

    # Create validator
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))

    # Create repository
    repository = CsvCompanyDataRepository(settings.data_path, validator)

    # Create scoring strategy
    scoring_strategy = DefaultScoring()

    # Create screener
    screener = Screener(repository=repository, scoring_strategy=scoring_strategy)

    logger.info("Created production screener")
    return screener


def get_test_screener() -> Screener:
    """Get test screener with test configuration.

    Returns:
        Screener configured for testing
    """
    # For testing, we might want different configuration
    # This could be overridden in test fixtures
    return get_screener()


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
