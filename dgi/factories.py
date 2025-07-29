"""Factory services implementing Dependency Inversion Principle."""

import logging
from typing import Any

from dgi.config import get_config
from dgi.interfaces import (
    CacheService,
    ConfigurationService,
    DataValidator,
    LoggingService,
    MetricsService,
    ValidationService,
)
from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring, ScoringStrategy
from dgi.services.portfolio_service import PortfolioService as ConcretePortfolioService
from dgi.services.screening_service import ScreeningService
from dgi.services.validation_service import (
    ValidationService as ConcreteValidationService,
)
from dgi.validation_utils import DgiRowValidator, PydanticRowValidation

logger = logging.getLogger(__name__)


class ScoringStrategyAdapter:
    """Adapter to make ScoringStrategy compatible with ScoringService interface."""

    def __init__(self, strategy: ScoringStrategy):
        """Initialize with a scoring strategy."""
        self._strategy = strategy

    def calculate_score(self, company: CompanyData) -> float:
        """Calculate a score for a company."""
        return self._strategy.score(company)

    def calculate_composite_score(self, company: CompanyData) -> float:
        """Calculate a composite score for a company."""
        return self._strategy.score(company)

    def score_dataframe(self, df: Any) -> Any:
        """Score all rows in a DataFrame."""
        # This is a simplified implementation - in practice, you'd want to convert
        # DataFrame rows to CompanyData objects and score them
        if df.empty:
            return df

        # For now, return the DataFrame as-is
        # In a real implementation, you'd apply the scoring strategy to each row
        return df


class ServiceFactory:
    """Factory for creating service instances following Dependency Inversion Principle."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the factory with optional configuration.

        Args:
            config: Configuration dictionary for service creation
        """
        self._config = config or get_config()
        if not isinstance(self._config, dict):
            # Convert Config object to dict
            config_obj = self._config
            self._config = {
                "DATA_PATH": config_obj.DATA_PATH,
                "LOG_LEVEL": config_obj.LOG_LEVEL,
                "DEFAULT_MIN_YIELD": config_obj.DEFAULT_MIN_YIELD,
                "DEFAULT_MAX_PAYOUT": config_obj.DEFAULT_MAX_PAYOUT,
                "DEFAULT_MIN_CAGR": config_obj.DEFAULT_MIN_CAGR,
                "DEFAULT_TOP_N": config_obj.DEFAULT_TOP_N,
                "DEFAULT_SCREEN_MIN_YIELD": config_obj.DEFAULT_SCREEN_MIN_YIELD,
                "DEFAULT_SCREEN_MAX_PAYOUT": config_obj.DEFAULT_SCREEN_MAX_PAYOUT,
                "DEFAULT_SCREEN_MIN_CAGR": config_obj.DEFAULT_SCREEN_MIN_CAGR,
            }
        self._cache: dict[str, Any] = {}

    def create_scoring_service(
        self, strategy: str = "default"
    ) -> ScoringStrategyAdapter:
        """Create a scoring service based on strategy.

        Args:
            strategy: Scoring strategy to use

        Returns:
            ScoringStrategyAdapter instance
        """
        cache_key = f"scoring_service_{strategy}"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        if strategy == "default":
            scoring_strategy = DefaultScoring()
        else:
            logger.warning(f"Unknown scoring strategy: {strategy}, using default")
            scoring_strategy = DefaultScoring()

        service = ScoringStrategyAdapter(scoring_strategy)
        self._cache[cache_key] = service
        return service

    def create_filtering_service(self, strategy: str = "default") -> ScreeningService:
        """Create a filtering service based on strategy.

        Args:
            strategy: Filtering strategy to use

        Returns:
            ScreeningService instance
        """
        cache_key = f"filtering_service_{strategy}"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        # For now, we'll use the screening service as the filtering service
        # In the future, this could be split into separate services
        service = ScreeningService()
        self._cache[cache_key] = service
        return service

    def create_validation_service(self, strategy: str = "default") -> ValidationService:
        """Create a validation service based on strategy.

        Args:
            strategy: Validation strategy to use

        Returns:
            ValidationService instance
        """
        cache_key = f"validation_service_{strategy}"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        if strategy == "default":
            service = ConcreteValidationService()
        else:
            logger.warning(f"Unknown validation strategy: {strategy}, using default")
            service = ConcreteValidationService()

        self._cache[cache_key] = service
        return service

    def create_portfolio_service(
        self, strategy: str = "default"
    ) -> ConcretePortfolioService:
        """Create a portfolio service based on strategy.

        Args:
            strategy: Portfolio strategy to use

        Returns:
            PortfolioService instance
        """
        cache_key = f"portfolio_service_{strategy}"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        if strategy == "default":
            service = ConcretePortfolioService()
        else:
            logger.warning(f"Unknown portfolio strategy: {strategy}, using default")
            service = ConcretePortfolioService()

        self._cache[cache_key] = service
        return service

    def create_data_repository(
        self, source: str = "csv", **kwargs: Any
    ) -> CompanyDataRepository:
        """Create a data repository based on source type.

        Args:
            source: Data source type (csv, database, api, etc.)
            **kwargs: Additional arguments for repository creation

        Returns:
            DataRepository instance
        """
        cache_key = f"data_repository_{source}_{hash(str(kwargs))}"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        if source == "csv":
            csv_path = kwargs.get("csv_path", "data/fundamentals_small.csv")
            validator = kwargs.get("validator")
            if validator is None:
                validator = DgiRowValidator(PydanticRowValidation(CompanyData))
            repository = CsvCompanyDataRepository(csv_path, validator)
        else:
            logger.warning(f"Unknown data source: {source}, using CSV")
            csv_path = kwargs.get("csv_path", "data/fundamentals_small.csv")
            validator = DgiRowValidator(PydanticRowValidation(CompanyData))
            repository = CsvCompanyDataRepository(csv_path, validator)

        self._cache[cache_key] = repository
        return repository

    def create_data_validator(self, strategy: str = "default") -> DataValidator:
        """Create a data validator based on strategy.

        Args:
            strategy: Validation strategy to use

        Returns:
            DataValidator instance
        """
        cache_key = f"data_validator_{strategy}"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        if strategy == "default":
            validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        else:
            logger.warning(f"Unknown validator strategy: {strategy}, using default")
            validator = DgiRowValidator(PydanticRowValidation(CompanyData))

        self._cache[cache_key] = validator
        return validator

    def create_configuration_service(self, **kwargs: Any) -> ConfigurationService:
        """Create a configuration service.

        Args:
            **kwargs: Configuration arguments

        Returns:
            ConfigurationService instance
        """
        cache_key = "configuration_service"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        # For now, we'll create a simple configuration service
        # In the future, this could use the config management system
        service = SimpleConfigurationService(self._config)  # type: ignore[arg-type]
        self._cache[cache_key] = service
        return service

    def create_logging_service(self, **kwargs: Any) -> LoggingService:
        """Create a logging service.

        Args:
            **kwargs: Logging arguments

        Returns:
            LoggingService instance
        """
        cache_key = "logging_service"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        service = SimpleLoggingService()
        self._cache[cache_key] = service
        return service

    def create_metrics_service(self, **kwargs: Any) -> MetricsService:
        """Create a metrics service.

        Args:
            **kwargs: Metrics arguments

        Returns:
            MetricsService instance
        """
        cache_key = "metrics_service"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        service = SimpleMetricsService()
        self._cache[cache_key] = service
        return service

    def create_cache_service(self, **kwargs: Any) -> CacheService:
        """Create a cache service.

        Args:
            **kwargs: Cache arguments

        Returns:
            CacheService instance
        """
        cache_key = "cache_service"
        if cache_key in self._cache:
            return self._cache[cache_key]  # type: ignore[no-any-return]

        service = SimpleCacheService()
        self._cache[cache_key] = service
        return service

    def clear_cache(self) -> None:
        """Clear the factory cache."""
        self._cache.clear()
        logger.info("Factory cache cleared")


# Simple implementations of services for dependency injection
class SimpleConfigurationService(ConfigurationService):
    """Simple implementation of ConfigurationService."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize with configuration."""
        self._config = config

    def get_config(self) -> dict[str, Any]:
        """Get configuration."""
        return self._config

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting."""
        return getattr(self._config, key, default)

    def reload_config(self) -> None:
        """Reload configuration."""
        config_obj = get_config()
        self._config = {
            "DATA_PATH": config_obj.DATA_PATH,
            "LOG_LEVEL": config_obj.LOG_LEVEL,
            "DEFAULT_MIN_YIELD": config_obj.DEFAULT_MIN_YIELD,
            "DEFAULT_MAX_PAYOUT": config_obj.DEFAULT_MAX_PAYOUT,
            "DEFAULT_MIN_CAGR": config_obj.DEFAULT_MIN_CAGR,
            "DEFAULT_TOP_N": config_obj.DEFAULT_TOP_N,
            "DEFAULT_SCREEN_MIN_YIELD": config_obj.DEFAULT_SCREEN_MIN_YIELD,
            "DEFAULT_SCREEN_MAX_PAYOUT": config_obj.DEFAULT_SCREEN_MAX_PAYOUT,
            "DEFAULT_SCREEN_MIN_CAGR": config_obj.DEFAULT_SCREEN_MIN_CAGR,
        }


class SimpleLoggingService(LoggingService):
    """Simple implementation of LoggingService."""

    def get_logger(self, name: str) -> Any:
        """Get a logger instance."""
        return logging.getLogger(name)

    def log_business_event(self, event_name: str, **metadata: Any) -> None:
        """Log a business event."""
        logger.info(f"Business event: {event_name}", extra=metadata)

    def log_performance_metric(
        self, metric_name: str, value: float, **labels: Any
    ) -> None:
        """Log a performance metric."""
        logger.info(f"Performance metric: {metric_name} = {value}", extra=labels)


class SimpleMetricsService(MetricsService):
    """Simple implementation of MetricsService."""

    def __init__(self) -> None:
        """Initialize metrics storage."""
        self._metrics: dict[str, Any] = {}

    def record_metric(self, name: str, value: float, **labels: Any) -> None:
        """Record a metric."""
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append({"value": value, "labels": labels})

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics."""
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()


class SimpleCacheService(CacheService):
    """Simple implementation of CacheService."""

    def __init__(self) -> None:
        """Initialize cache storage."""
        self._cache: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache."""
        self._cache[key] = value

    def delete(self, key: str) -> None:
        """Delete a value from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()


# Global factory instance
_service_factory = ServiceFactory()


def get_service_factory() -> ServiceFactory:
    """Get the global service factory instance.

    Returns:
        ServiceFactory instance
    """
    return _service_factory


def create_scoring_service(strategy: str = "default") -> ScoringStrategyAdapter:
    """Create a scoring service using the global factory.

    Args:
        strategy: Scoring strategy to use

    Returns:
        ScoringStrategyAdapter instance
    """
    return _service_factory.create_scoring_service(strategy)


def create_filtering_service(strategy: str = "default") -> ScreeningService:
    """Create a filtering service using the global factory.

    Args:
        strategy: Filtering strategy to use

    Returns:
        ScreeningService instance
    """
    return _service_factory.create_filtering_service(strategy)


def create_validation_service(strategy: str = "default") -> ValidationService:
    """Create a validation service using the global factory.

    Args:
        strategy: Validation strategy to use

    Returns:
        ValidationService instance
    """
    return _service_factory.create_validation_service(strategy)


def create_portfolio_service(strategy: str = "default") -> ConcretePortfolioService:
    """Create a portfolio service using the global factory.

    Args:
        strategy: Portfolio strategy to use

    Returns:
        PortfolioService instance
    """
    return _service_factory.create_portfolio_service(strategy)


def create_data_repository(source: str = "csv", **kwargs: Any) -> CompanyDataRepository:
    """Create a data repository using the global factory.

    Args:
        source: Data source type
        **kwargs: Additional arguments

    Returns:
        DataRepository instance
    """
    return _service_factory.create_data_repository(source, **kwargs)
