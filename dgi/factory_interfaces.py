"""Segregated factory interfaces following Interface Segregation Principle.

This module provides focused factory interfaces that don't force implementations
to support all creation methods, following the ISP principle.
"""

from typing import Protocol

from dgi.filtering import BaseFilter
from dgi.repositories.base import CompanyDataRepository
from dgi.scoring import ScoringStrategy
from dgi.screener import Screener
from dgi.validation_utils import DgiRowValidator


class RepositoryFactory(Protocol):
    """Factory for creating data repositories."""

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a data repository."""
        ...


class ScoringStrategyFactory(Protocol):
    """Factory for creating scoring strategies."""

    def create_scoring_strategy(
        self, strategy_name: str | None = None
    ) -> ScoringStrategy:
        """Create a scoring strategy."""
        ...


class FilterStrategyFactory(Protocol):
    """Factory for creating filter strategies."""

    def create_filter_strategy(self, strategy_name: str | None = None) -> BaseFilter:
        """Create a filter strategy."""
        ...


class ValidatorFactory(Protocol):
    """Factory for creating validators."""

    def create_validator(self, validator_name: str | None = None) -> DgiRowValidator:
        """Create a validator."""
        ...


class ScreenerFactory(Protocol):
    """Factory for creating screeners."""

    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener."""
        ...


class ConfigurableFactory(Protocol):
    """Factory that supports configuration."""

    def configure(self, config: dict[str, any]) -> None:
        """Configure the factory."""
        ...

    def get_configuration(self) -> dict[str, any]:
        """Get current configuration."""
        ...


class CacheableFactory(Protocol):
    """Factory that supports caching of created instances."""

    def clear_cache(self) -> None:
        """Clear the factory cache."""
        ...

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        ...


class MetricsFactory(Protocol):
    """Factory that provides creation metrics."""

    def get_creation_metrics(self) -> dict[str, int]:
        """Get factory creation metrics."""
        ...


# Composed interfaces for common use cases
class BasicComponentFactory(ScoringStrategyFactory, FilterStrategyFactory, Protocol):
    """Factory for basic scoring and filtering components."""


class DataAccessFactory(RepositoryFactory, ValidatorFactory, Protocol):
    """Factory for data access components."""


class ScreeningFactory(
    ScoringStrategyFactory, FilterStrategyFactory, ScreenerFactory, Protocol
):
    """Factory for screening-related components."""


class FullDependencyFactory(
    RepositoryFactory,
    ScoringStrategyFactory,
    FilterStrategyFactory,
    ValidatorFactory,
    ScreenerFactory,
    Protocol,
):
    """Full dependency factory with all creation methods."""


class EnhancedFactory(
    FullDependencyFactory, ConfigurableFactory, CacheableFactory, Protocol
):
    """Enhanced factory with configuration and caching."""


# Adapter for backwards compatibility
class LegacyFactoryAdapter:
    """Adapter to maintain backwards compatibility with existing factory interface."""

    def __init__(
        self,
        repository_factory: RepositoryFactory | None = None,
        scoring_factory: ScoringStrategyFactory | None = None,
        filter_factory: FilterStrategyFactory | None = None,
        validator_factory: ValidatorFactory | None = None,
        screener_factory: ScreenerFactory | None = None,
    ) -> None:
        """Initialize adapter with segregated factories.

        Args:
            repository_factory: Factory for repositories
            scoring_factory: Factory for scoring strategies
            filter_factory: Factory for filter strategies
            validator_factory: Factory for validators
            screener_factory: Factory for screeners
        """
        self._repository_factory = repository_factory
        self._scoring_factory = scoring_factory
        self._filter_factory = filter_factory
        self._validator_factory = validator_factory
        self._screener_factory = screener_factory

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a data repository."""
        if self._repository_factory is None:
            raise NotImplementedError("Repository factory not provided")
        return self._repository_factory.create_repository(data_path)

    def create_scoring_strategy(
        self, strategy_name: str | None = None
    ) -> ScoringStrategy:
        """Create a scoring strategy."""
        if self._scoring_factory is None:
            raise NotImplementedError("Scoring strategy factory not provided")
        return self._scoring_factory.create_scoring_strategy(strategy_name)

    def create_filter_strategy(self, strategy_name: str | None = None) -> BaseFilter:
        """Create a filter strategy."""
        if self._filter_factory is None:
            raise NotImplementedError("Filter strategy factory not provided")
        return self._filter_factory.create_filter_strategy(strategy_name)

    def create_validator(self, validator_name: str | None = None) -> DgiRowValidator:
        """Create a validator."""
        if self._validator_factory is None:
            raise NotImplementedError("Validator factory not provided")
        return self._validator_factory.create_validator(validator_name)

    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener."""
        if self._screener_factory is None:
            raise NotImplementedError("Screener factory not provided")
        return self._screener_factory.create_screener(
            repository, scoring_strategy, filter_strategy
        )


# Strategy-specific factory implementations
class SimpleScoringFactory:
    """Simple implementation of scoring strategy factory."""

    def __init__(self, default_strategy: str = "default") -> None:
        """Initialize with default strategy.

        Args:
            default_strategy: Name of default strategy to use
        """
        self.default_strategy = default_strategy

    def create_scoring_strategy(
        self, strategy_name: str | None = None
    ) -> ScoringStrategy:
        """Create a scoring strategy using strategy registry."""
        from dgi.strategy_registry import get_strategy_registry

        registry = get_strategy_registry("scoring")
        return registry.get_strategy(name=strategy_name or self.default_strategy)


class SimpleFilterFactory:
    """Simple implementation of filter strategy factory."""

    def __init__(self, default_strategy: str = "default") -> None:
        """Initialize with default strategy.

        Args:
            default_strategy: Name of default strategy to use
        """
        self.default_strategy = default_strategy

    def create_filter_strategy(self, strategy_name: str | None = None) -> BaseFilter:
        """Create a filter strategy using strategy registry."""
        from dgi.strategy_registry import get_strategy_registry

        registry = get_strategy_registry("filtering")
        return registry.get_strategy(name=strategy_name or self.default_strategy)


class SimpleRepositoryFactory:
    """Simple implementation of repository factory."""

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a CSV repository."""
        from dgi.repositories.csv import CsvCompanyDataRepository
        from dgi.strategy_registry import get_strategy_registry

        validator_registry = get_strategy_registry("validator")
        validator = validator_registry.get_strategy()

        return CsvCompanyDataRepository(data_path, validator)
