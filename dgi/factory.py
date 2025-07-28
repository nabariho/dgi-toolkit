"""Factory pattern implementation for DGI Toolkit dependencies.

This module provides a centralized factory for creating all dependencies,
following the Abstract Factory pattern and Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from dgi.exceptions import FactoryError
from dgi.filtering import BaseFilter, DefaultFilter
from dgi.models.company import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring, ScoringStrategy
from dgi.screener import Screener
from dgi.validation import DgiRowValidator, PydanticRowValidation


class RepositoryFactory(Protocol):
    """Protocol for repository factory."""

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a data repository."""
        ...


class ScoringStrategyFactory(Protocol):
    """Protocol for scoring strategy factory."""

    def create_scoring_strategy(self) -> ScoringStrategy:
        """Create a scoring strategy."""
        ...


class FilterStrategyFactory(Protocol):
    """Protocol for filter strategy factory."""

    def create_filter_strategy(self) -> BaseFilter:
        """Create a filter strategy."""
        ...


class ValidatorFactory(Protocol):
    """Protocol for validator factory."""

    def create_validator(self) -> DgiRowValidator:
        """Create a validator."""
        ...


class ScreenerFactory(Protocol):
    """Protocol for screener factory."""

    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener."""
        ...


class DependencyFactory(ABC):
    """Abstract factory for creating DGI Toolkit dependencies."""

    @abstractmethod
    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a data repository."""

    @abstractmethod
    def create_scoring_strategy(self) -> ScoringStrategy:
        """Create a scoring strategy."""

    @abstractmethod
    def create_filter_strategy(self) -> BaseFilter:
        """Create a filter strategy."""

    @abstractmethod
    def create_validator(self) -> DgiRowValidator:
        """Create a validator."""

    @abstractmethod
    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener."""


class ProductionDependencyFactory(DependencyFactory):
    """Production factory for creating dependencies."""

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a CSV repository for production use."""
        validator = self.create_validator()
        return CsvCompanyDataRepository(data_path, validator)

    def create_scoring_strategy(self) -> ScoringStrategy:
        """Create the default scoring strategy for production."""
        return DefaultScoring()

    def create_filter_strategy(self) -> BaseFilter:
        """Create the default filter strategy for production."""
        return DefaultFilter()

    def create_validator(self) -> DgiRowValidator:
        """Create a validator for production use."""
        return DgiRowValidator(PydanticRowValidation(CompanyData))

    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener with production configuration."""
        if scoring_strategy is None:
            scoring_strategy = self.create_scoring_strategy()
        if filter_strategy is None:
            filter_strategy = self.create_filter_strategy()

        return Screener(
            repository=repository,
            scoring_strategy=scoring_strategy,
            filter_strategy=filter_strategy,
        )


class TestDependencyFactory(DependencyFactory):
    """Test factory for creating dependencies with test configuration."""

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a CSV repository for testing."""
        validator = self.create_validator()
        return CsvCompanyDataRepository(data_path, validator)

    def create_scoring_strategy(self) -> ScoringStrategy:
        """Create the default scoring strategy for testing."""
        return DefaultScoring()

    def create_filter_strategy(self) -> BaseFilter:
        """Create the default filter strategy for testing."""
        return DefaultFilter()

    def create_validator(self) -> DgiRowValidator:
        """Create a validator for testing."""
        return DgiRowValidator(PydanticRowValidation(CompanyData))

    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener with test configuration."""
        if scoring_strategy is None:
            scoring_strategy = self.create_scoring_strategy()
        if filter_strategy is None:
            filter_strategy = self.create_filter_strategy()

        return Screener(
            repository=repository,
            scoring_strategy=scoring_strategy,
            filter_strategy=filter_strategy,
        )


class MockDependencyFactory(DependencyFactory):
    """Mock factory for creating test dependencies with mocked components."""

    def __init__(
        self,
        mock_repository: CompanyDataRepository | None = None,
        mock_scoring: ScoringStrategy | None = None,
        mock_filter: BaseFilter | None = None,
    ) -> None:
        """Initialize mock factory with optional mock components."""
        self.mock_repository = mock_repository
        self.mock_scoring = mock_scoring
        self.mock_filter = mock_filter

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a mock repository for testing."""
        if self.mock_repository:
            return self.mock_repository
        repository: CompanyDataRepository = CsvCompanyDataRepository(
            data_path, self.create_validator()
        )
        return repository

    def create_scoring_strategy(self) -> ScoringStrategy:
        """Create a mock scoring strategy for testing."""
        if self.mock_scoring:
            return self.mock_scoring
        strategy: ScoringStrategy = DefaultScoring()
        return strategy

    def create_filter_strategy(self) -> BaseFilter:
        """Create a mock filter strategy for testing."""
        if self.mock_filter:
            return self.mock_filter
        filter_strategy: BaseFilter = DefaultFilter()
        return filter_strategy

    def create_validator(self) -> DgiRowValidator:
        """Create a validator for testing."""
        return DgiRowValidator(PydanticRowValidation(CompanyData))

    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener with mock configuration."""
        if scoring_strategy is None:
            scoring_strategy = self.create_scoring_strategy()
        if filter_strategy is None:
            filter_strategy = self.create_filter_strategy()

        return Screener(
            repository=repository,
            scoring_strategy=scoring_strategy,
            filter_strategy=filter_strategy,
        )


# Factory registry and configuration
class FactoryRegistry:
    """Registry for managing dependency factories."""

    def __init__(self) -> None:
        """Initialize factory registry."""
        self._factories = {
            "production": ProductionDependencyFactory(),
            "test": TestDependencyFactory(),
            "mock": MockDependencyFactory(),
        }
        self._current_factory = "production"

    def register_factory(self, name: str, factory: DependencyFactory) -> None:
        """Register a new factory."""
        self._factories[name] = factory

    def get_factory(self, name: str | None = None) -> DependencyFactory:
        """Get a factory by name."""
        factory_name = name or self._current_factory
        if factory_name not in self._factories:
            raise FactoryError(
                f"Factory '{factory_name}' not found", factory_name=factory_name
            )
        return self._factories[factory_name]

    def set_current_factory(self, name: str) -> None:
        """Set the current factory."""
        if name not in self._factories:
            raise FactoryError(f"Factory '{name}' not found", factory_name=name)
        self._current_factory = name

    def get_current_factory(self) -> DependencyFactory:
        """Get the current factory."""
        return self.get_factory()


# Global factory registry
_factory_registry = FactoryRegistry()


def get_factory_registry() -> FactoryRegistry:
    """Get the global factory registry."""
    return _factory_registry


def get_dependency_factory(name: str | None = None) -> DependencyFactory:
    """Get a dependency factory by name."""
    return _factory_registry.get_factory(name)


def set_dependency_factory(name: str) -> None:
    """Set the current dependency factory."""
    _factory_registry.set_current_factory(name)


# Convenience functions for creating dependencies
def create_repository(
    data_path: str, factory_name: str | None = None
) -> CompanyDataRepository:
    """Create a repository using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_repository(data_path)


def create_screener(
    repository: CompanyDataRepository,
    scoring_strategy: ScoringStrategy | None = None,
    filter_strategy: BaseFilter | None = None,
    factory_name: str | None = None,
) -> Screener:
    """Create a screener using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_screener(repository, scoring_strategy, filter_strategy)


def create_validator(factory_name: str | None = None) -> DgiRowValidator:
    """Create a validator using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_validator()


def create_scoring_strategy(factory_name: str | None = None) -> ScoringStrategy:
    """Create a scoring strategy using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_scoring_strategy()


def create_filter_strategy(factory_name: str | None = None) -> BaseFilter:
    """Create a filter strategy using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_filter_strategy()
