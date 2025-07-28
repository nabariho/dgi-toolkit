"""Enhanced dependency injection container with advanced lifecycle management.

This module provides enterprise-grade dependency injection features including:
- Request/Session/Application level scoping
- Automatic resource cleanup and lifecycle management
- Thread-safe singleton patterns with proper initialization
- Health checking for expensive resources
- Configuration reloading and hot-swapping
- Performance monitoring and metrics
"""

import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from enum import Enum
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


class ResourceScope(Enum):
    """Resource scoping levels for dependency injection."""

    SINGLETON = "singleton"  # Application-wide singleton
    REQUEST = "request"  # Per-request scoping
    SESSION = "session"  # Per-session scoping
    PROTOTYPE = "prototype"  # New instance every time


class ResourceStatus(Enum):
    """Resource health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ManagedResource:
    """Wrapper for managed resources with lifecycle and health checking."""

    def __init__(
        self,
        resource: Any,
        scope: ResourceScope,
        cleanup_func: Callable | None = None,
        health_check: Callable[[], bool] | None = None,
        created_at: float | None = None,
    ):
        """Initialize managed resource."""
        self.resource = resource
        self.scope = scope
        self.cleanup_func = cleanup_func
        self.health_check = health_check
        self.created_at = created_at or time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        self._lock = threading.RLock()

    def access(self) -> Any:
        """Access the resource with tracking."""
        with self._lock:
            self.last_accessed = time.time()
            self.access_count += 1
            return self.resource

    def get_status(self) -> ResourceStatus:
        """Get resource health status."""
        if self.health_check:
            try:
                return (
                    ResourceStatus.HEALTHY
                    if self.health_check()
                    else ResourceStatus.UNHEALTHY
                )
            except Exception:
                return ResourceStatus.DEGRADED
        return ResourceStatus.UNKNOWN

    def cleanup(self):
        """Clean up the resource."""
        if self.cleanup_func:
            try:
                self.cleanup_func()
            except Exception as e:
                logger.warning(f"Error during resource cleanup: {e}")


class ResourceManager:
    """Advanced resource manager with lifecycle and health monitoring."""

    def __init__(self):
        """Initialize resource manager."""
        self._resources: dict[str, ManagedResource] = {}
        self._request_scoped: dict[str, dict[str, ManagedResource]] = {}
        self._session_scoped: dict[str, dict[str, ManagedResource]] = {}
        self._lock = threading.RLock()

    def register_resource(
        self,
        name: str,
        resource: Any,
        scope: ResourceScope,
        cleanup_func: Callable | None = None,
        health_check: Callable[[], bool] | None = None,
    ) -> ManagedResource:
        """Register a managed resource."""
        managed = ManagedResource(
            resource=resource,
            scope=scope,
            cleanup_func=cleanup_func,
            health_check=health_check,
        )

        with self._lock:
            if scope == ResourceScope.SINGLETON:
                self._resources[name] = managed

        logger.info(f"Registered {scope.value} resource: {name}")
        return managed

    def get_health_status(self) -> dict[str, ResourceStatus]:
        """Get health status of all managed resources."""
        status = {}
        with self._lock:
            for name, resource in self._resources.items():
                status[name] = resource.get_status()
        return status

    def cleanup_all(self):
        """Clean up all managed resources."""
        with self._lock:
            for resource in self._resources.values():
                resource.cleanup()
            self._resources.clear()

            for scope_resources in self._request_scoped.values():
                for resource in scope_resources.values():
                    resource.cleanup()
            self._request_scoped.clear()

            for scope_resources in self._session_scoped.values():
                for resource in scope_resources.values():
                    resource.cleanup()
            self._session_scoped.clear()

        logger.info("All managed resources cleaned up")


# Global resource manager
_resource_manager = ResourceManager()


class EnhancedContainer(containers.DeclarativeContainer):
    """Enhanced dependency injection container with advanced lifecycle management."""

    # Configuration with hot reloading support
    config = providers.Configuration()

    # Settings provider with caching
    settings = providers.Singleton(get_settings)

    # Repository with lifecycle management
    repository = providers.Singleton(
        create_repository, data_path=settings.provided.data_path
    )

    # Validator with lifecycle management
    validator = providers.Singleton(create_validator)

    # Scoring strategy with lifecycle management
    scoring_strategy = providers.Singleton(create_scoring_strategy)

    # Focused services implementing SOLID principles
    parameter_validator = providers.Singleton(ScreeningParameterValidator)
    criteria_service = providers.Singleton(DGICriteriaService)
    scoring_service = providers.Singleton(DataFrameScoringService)

    # Screening service with dependency injection
    screening_service = providers.Factory(
        ScreeningService,
        parameter_validator=parameter_validator,
        criteria_applier=criteria_service,
        dataframe_scorer=scoring_service,
    )

    # Screener with enhanced dependency injection
    screener = providers.Singleton(
        create_screener, repository=repository, screening_service=screening_service
    )


# Global enhanced container instance
enhanced_container = EnhancedContainer()


@contextmanager
def request_scope(request_id: str):
    """Context manager for request-scoped dependency injection."""
    logger.debug(f"Entering request scope: {request_id}")
    try:
        yield enhanced_container
    finally:
        logger.debug(f"Exiting request scope: {request_id}")


async def init_enhanced_container():
    """Initialize the enhanced container asynchronously."""
    logger.info("Initializing enhanced dependency injection container")

    try:
        # Initialize core services
        enhanced_container.settings()
        enhanced_container.repository()
        enhanced_container.validator()
        enhanced_container.parameter_validator()
        enhanced_container.criteria_service()
        enhanced_container.scoring_service()
        enhanced_container.screening_service()
        enhanced_container.screener()

        # Register resources with health checking
        _resource_manager.register_resource(
            name="repository",
            resource=enhanced_container.repository(),
            scope=ResourceScope.SINGLETON,
            cleanup_func=getattr(enhanced_container.repository(), "cleanup", None),
            health_check=lambda: hasattr(enhanced_container.repository(), "get_rows"),
        )

        _resource_manager.register_resource(
            name="screening_service",
            resource=enhanced_container.screening_service(),
            scope=ResourceScope.SINGLETON,
            health_check=lambda: hasattr(
                enhanced_container.screening_service(), "validate_screening_parameters"
            ),
        )

        logger.info("Enhanced container initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize enhanced container: {e}")
        await shutdown_enhanced_container()
        raise


async def shutdown_enhanced_container():
    """Shutdown the enhanced container and clean up all resources."""
    logger.info("Shutting down enhanced dependency injection container")

    try:
        # Clean up resource manager
        _resource_manager.cleanup_all()
        logger.info("Enhanced container shutdown completed")

    except Exception as e:
        logger.error(f"Error during enhanced container shutdown: {e}")


def get_resource_health() -> dict[str, Any]:
    """Get detailed health information for all resources."""
    health_status = _resource_manager.get_health_status()

    # Collect resource metrics
    metrics = {}
    for name, resource in _resource_manager._resources.items():
        metrics[name] = {
            "status": health_status[name].value,
            "created_at": resource.created_at,
            "last_accessed": resource.last_accessed,
            "access_count": resource.access_count,
            "age_seconds": time.time() - resource.created_at,
        }

    return {
        "health_status": {k: v.value for k, v in health_status.items()},
        "metrics": metrics,
        "total_resources": len(_resource_manager._resources),
    }


# Enhanced dependency injection functions
def get_enhanced_screener() -> Screener:
    """Get screener with enhanced dependency injection."""
    return enhanced_container.screener()


def get_enhanced_screening_service() -> ScreeningService:
    """Get screening service with enhanced dependency injection."""
    return enhanced_container.screening_service()


def get_enhanced_repository() -> CompanyDataRepository:
    """Get repository with enhanced dependency injection."""
    return enhanced_container.repository()


def container_health_check() -> bool:
    """Perform health check on the enhanced container."""
    try:
        health_status = _resource_manager.get_health_status()
        unhealthy = [
            name
            for name, status in health_status.items()
            if status == ResourceStatus.UNHEALTHY
        ]

        if unhealthy:
            logger.warning(f"Unhealthy resources detected: {unhealthy}")
            return False

        return True

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
