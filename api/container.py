"""Enhanced dependency injection container using dependency-injector framework."""

import threading
from typing import Any

from dependency_injector import containers, providers

from dgi.factory import (
    create_repository,
    create_scoring_strategy,
    create_screener,
    create_validator,
)
from dgi.repositories.base import CompanyDataRepository
from dgi.screener import Screener
from dgi.services.dgi_criteria_service import DGICriteriaService
from dgi.services.scoring_service import DataFrameScoringService
from dgi.services.screening_parameter_validator import ScreeningParameterValidator
from dgi.services.screening_service import ScreeningService

from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


class Container(containers.DeclarativeContainer):
    """Enhanced dependency injection container with proper lifecycle management."""

    # Configuration
    config = providers.Configuration()

    # Settings provider
    settings = providers.Singleton(get_settings)

    # Data repository with lifecycle management
    data_repository = providers.Singleton(
        create_repository,
        data_path=settings.provided.data_path,
    )

    # Validator with lifecycle management
    validator = providers.Singleton(
        create_validator,
    )

    # Scoring strategy with lifecycle management
    scoring_strategy = providers.Singleton(
        create_scoring_strategy,
    )

    # New focused services implementing SOLID principles
    parameter_validator = providers.Singleton(ScreeningParameterValidator)

    criteria_service = providers.Singleton(DGICriteriaService)

    scoring_service = providers.Singleton(DataFrameScoringService)

    # Coordinating service with dependency injection
    screening_service = providers.Factory(
        ScreeningService,
        parameter_validator=parameter_validator,
        criteria_applier=criteria_service,
        dataframe_scorer=scoring_service,
    )

    # Screener with dependency injection
    screener = providers.Singleton(
        create_screener,
        repository=data_repository,
        screening_service=screening_service,
    )

    # Test screener for testing environment
    test_screener = providers.Singleton(
        create_screener,
        repository=providers.Singleton(
            create_repository,
            data_path=settings.provided.data_path,
        ),
        screening_service=screening_service,
    )


# Global container instance
container = Container()

# Thread safety for container operations
_container_lock = threading.RLock()
_container_initialized = False


def get_container() -> Container:
    """Get the global container instance.

    Returns:
        Container instance
    """
    return container


def init_container():
    """Initialize the global container.

    This should be called during application startup.
    """
    global _container_initialized

    with _container_lock:
        if not _container_initialized:
            # Initialize all singleton providers
            container.settings()
            container.data_repository()
            container.validator()
            container.scoring_strategy()
            container.screener()

            # Initialize new focused services
            container.parameter_validator()
            container.criteria_service()
            container.scoring_service()
            container.screening_service()

            _container_initialized = True
            logger.info("Container resources initialized")


def shutdown_container():
    """Shutdown the global container.

    This should be called during application shutdown.
    """
    global _container_initialized

    with _container_lock:
        try:
            # Cleanup repository if it has cleanup method
            repository = container.data_repository()
            if hasattr(repository, "cleanup"):
                repository.cleanup()
                logger.info("Repository cleanup completed")
        except Exception as e:
            logger.error(f"Error during repository cleanup: {e}")

        # Reset initialization flag
        _container_initialized = False
        logger.info("Container shutdown completed")


# Dependency injection functions for FastAPI
def get_settings_dependency() -> Any:
    """Get settings dependency with injection.

    Returns:
        APISettings instance
    """
    return container.settings()


def get_data_repository_dependency() -> CompanyDataRepository:
    """Get data repository dependency with injection.

    Returns:
        Configured CompanyDataRepository instance
    """
    return container.data_repository()


def get_screener_dependency() -> Screener:
    """Get screener dependency with injection.

    Returns:
        Configured Screener instance
    """
    return container.screener()


def get_validator_dependency() -> Any:
    """Get validator dependency with injection.

    Returns:
        Configured validator instance
    """
    return container.validator()


def get_scoring_strategy_dependency() -> Any:
    """Get scoring strategy dependency with injection.

    Returns:
        ScoringStrategy instance
    """
    return container.scoring_strategy()


def get_test_screener_dependency() -> Screener:
    """Get test screener dependency with injection.

    Returns:
        Screener configured for testing
    """
    return container.test_screener()


def get_parameter_validator_dependency() -> ScreeningParameterValidator:
    """Get parameter validator dependency with injection.

    Returns:
        ScreeningParameterValidator instance
    """
    return container.parameter_validator()


def get_criteria_service_dependency() -> DGICriteriaService:
    """Get criteria service dependency with injection.

    Returns:
        DGICriteriaService instance
    """
    return container.criteria_service()


def get_scoring_service_dependency() -> DataFrameScoringService:
    """Get scoring service dependency with injection.

    Returns:
        DataFrameScoringService instance
    """
    return container.scoring_service()


def get_screening_service_dependency() -> ScreeningService:
    """Get screening service dependency with injection.

    Returns:
        ScreeningService instance with all dependencies injected
    """
    return container.screening_service()


# Context manager for dependency scoping
class DependencyScope:
    """Context manager for dependency scoping with proper lifecycle management."""

    def __init__(self, container_instance: Container | None = None):
        """Initialize dependency scope.

        Args:
            container_instance: Container instance to scope, defaults to global container
        """
        self.container = container_instance or container
        self._original_initialized = False

    def __enter__(self):
        """Enter dependency scope.

        Returns:
            Container instance for the scope
        """
        global _container_initialized

        # Store original initialization state
        self._original_initialized = _container_initialized

        # Reset initialization for new scope
        _container_initialized = False

        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit dependency scope.

        Args:
            exc_type: Exception type if any
            exc_val: Exception value if any
            exc_tb: Exception traceback if any
        """
        global _container_initialized

        # Restore original initialization state
        _container_initialized = self._original_initialized


def get_scoped_dependencies() -> DependencyScope:
    """Get scoped dependencies for request-level isolation.

    Returns:
        DependencyScope context manager
    """
    return DependencyScope()


# Backward compatibility functions
def get_data_repository() -> CompanyDataRepository:
    """Get data repository dependency (backward compatibility).

    Returns:
        Configured CompanyDataRepository instance
    """
    return get_data_repository_dependency()


def get_screener(repository=None) -> Screener:
    """Get screener dependency (backward compatibility).

    Args:
        repository: Data repository dependency (ignored, kept for compatibility)

    Returns:
        Configured Screener instance
    """
    return get_screener_dependency()


def get_validator() -> Any:
    """Get validator dependency (backward compatibility).

    Returns:
        Configured validator instance
    """
    return get_validator_dependency()


def get_scoring_strategy() -> Any:
    """Get scoring strategy dependency (backward compatibility).

    Returns:
        ScoringStrategy instance
    """
    return get_scoring_strategy_dependency()


def get_production_screener() -> Screener:
    """Get production screener (backward compatibility).

    Returns:
        Screener configured for production use
    """
    return get_screener_dependency()


def get_test_screener() -> Screener:
    """Get test screener (backward compatibility).

    Returns:
        Screener configured for testing
    """
    return get_test_screener_dependency()


def get_dependency_container() -> Container:
    """Get global dependency container (backward compatibility).

    Returns:
        Container instance
    """
    return get_container()
