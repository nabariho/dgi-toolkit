"""Interfaces and abstractions for DGI Toolkit following Dependency Inversion Principle."""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from pandas import DataFrame

from dgi.models import CompanyData


class ScoringService(ABC):
    """Abstract interface for scoring services."""

    @abstractmethod
    def calculate_score(self, company: CompanyData) -> float:
        """Calculate a score for a company."""

    @abstractmethod
    def calculate_composite_score(self, company: CompanyData) -> float:
        """Calculate a composite score for a company."""

    @abstractmethod
    def score_dataframe(self, df: DataFrame) -> DataFrame:
        """Score all rows in a DataFrame."""


class FilteringService(ABC):
    """Abstract interface for filtering services."""

    @abstractmethod
    def apply_filters(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply filters to a DataFrame."""

    @abstractmethod
    def apply_dgi_criteria(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Apply DGI criteria to a DataFrame."""


class ValidationService(ABC):
    """Abstract interface for validation services."""

    @abstractmethod
    def validate_screening_parameters(
        self, min_yield: float, max_payout: float, min_cagr: float, top_n: int
    ) -> None:
        """Validate screening parameters."""

    @abstractmethod
    def validate_company_data(self, data: list[dict[str, Any]]) -> list[CompanyData]:
        """Validate company data."""


class PortfolioService(ABC):
    """Abstract interface for portfolio services."""

    @abstractmethod
    def build_portfolio(
        self, companies: list[CompanyData], target_value: float, max_companies: int
    ) -> dict[str, Any]:
        """Build a portfolio from companies."""

    @abstractmethod
    def calculate_portfolio_metrics(
        self, portfolio: dict[str, Any]
    ) -> dict[str, float]:
        """Calculate portfolio metrics."""


class DataRepository(ABC):
    """Abstract interface for data repositories."""

    @abstractmethod
    def get_rows(self) -> list[CompanyData]:
        """Get all rows from the repository."""

    @abstractmethod
    async def get_rows_async(self) -> list[CompanyData]:
        """Get all rows from the repository asynchronously."""


class ConfigurationService(ABC):
    """Abstract interface for configuration services."""

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Get configuration."""

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting."""

    @abstractmethod
    def reload_config(self) -> None:
        """Reload configuration."""


class LoggingService(ABC):
    """Abstract interface for logging services."""

    @abstractmethod
    def get_logger(self, name: str):
        """Get a logger instance."""

    @abstractmethod
    def log_business_event(self, event_name: str, **metadata) -> None:
        """Log a business event."""

    @abstractmethod
    def log_performance_metric(self, metric_name: str, value: float, **labels) -> None:
        """Log a performance metric."""


class MetricsService(ABC):
    """Abstract interface for metrics services."""

    @abstractmethod
    def record_metric(self, name: str, value: float, **labels) -> None:
        """Record a metric."""

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics."""

    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset all metrics."""


class CacheService(ABC):
    """Abstract interface for cache services."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Get a value from cache."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a value from cache."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache."""


class FactoryService(ABC):
    """Abstract interface for factory services."""

    @abstractmethod
    def create_scoring_service(self, strategy: str) -> ScoringService:
        """Create a scoring service."""

    @abstractmethod
    def create_filtering_service(self, strategy: str) -> FilteringService:
        """Create a filtering service."""

    @abstractmethod
    def create_data_repository(self, source: str, **kwargs) -> DataRepository:
        """Create a data repository."""

    @abstractmethod
    def create_configuration_service(self, **kwargs) -> ConfigurationService:
        """Create a configuration service."""


# Protocol-based interfaces for more flexible typing
class ScoringStrategy(Protocol):
    """Protocol for scoring strategies."""

    def score(self, company: CompanyData) -> float:
        """Score a company."""
        ...


class FilterStrategy(Protocol):
    """Protocol for filter strategies."""

    def filter(
        self, df: DataFrame, min_yield: float, max_payout: float, min_cagr: float
    ) -> DataFrame:
        """Filter a DataFrame."""
        ...


class DataValidator(Protocol):
    """Protocol for data validators."""

    def validate_rows(self, rows: list[dict[str, Any]]) -> list[CompanyData]:
        """Validate rows of data."""
        ...


class ResourceMonitor(Protocol):
    """Protocol for resource monitors."""

    def record_data_load(self, rows_count: int, memory_bytes: int) -> None:
        """Record data loading statistics."""
        ...

    def register_object(self, obj: Any) -> None:
        """Register an object for monitoring."""
        ...

    def get_stats(self) -> dict[str, Any]:
        """Get monitoring statistics."""
        ...


class ResponseMapper(Protocol):
    """Protocol for response mappers."""

    def to_api_response(self, df: DataFrame) -> list[dict[str, Any]]:
        """Convert DataFrame to API response format."""
        ...

    def to_company_data_response(
        self, companies: list[CompanyData]
    ) -> list[dict[str, Any]]:
        """Convert CompanyData objects to API response format."""
        ...


class DataLoader(Protocol):
    """Protocol for data loaders."""

    def load_universe(self) -> DataFrame:
        """Load company universe data."""
        ...

    async def load_universe_async(self) -> DataFrame:
        """Load company universe data asynchronously."""
        ...

    def load_company_data(self) -> list[CompanyData]:
        """Load company data as structured objects."""
        ...

    async def load_company_data_async(self) -> list[CompanyData]:
        """Load company data as structured objects asynchronously."""
        ...


class ResourceManager(Protocol):
    """Protocol for resource managers."""

    def track_resource(self, resource: Any) -> None:
        """Track a resource for lifecycle management."""
        ...

    def cleanup(self) -> None:
        """Clean up managed resources."""
        ...

    def get_resource_stats(self) -> dict[str, Any]:
        """Get resource statistics."""
        ...

    def check_health(self) -> bool:
        """Check resource health."""
        ...
