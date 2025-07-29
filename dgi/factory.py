"""Factory pattern implementation for DGI Toolkit dependencies.

This module provides a centralized factory for creating all dependencies,
following the Abstract Factory pattern and Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, cast

from dgi.exceptions import FactoryError
from dgi.filtering import BaseFilter, DefaultFilter
from dgi.interfaces import DataRepository, ScoringService, ValidationService
from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring, ScoringStrategy
from dgi.screener import CompanyFilter, Screener


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


class RepositoryFactory(Protocol):
    """Protocol for repository factory."""

    def create_repository(self, data_path: str) -> DataRepository:
        """Create a data repository."""
        ...


class ScoringStrategyFactory(Protocol):
    """Protocol for scoring strategy factory."""

    def create_scoring_strategy(self) -> ScoringService:
        """Create a scoring strategy."""
        ...


class FilterStrategyFactory(Protocol):
    """Protocol for filter strategy factory."""

    def create_filter_strategy(self) -> BaseFilter:
        """Create a filter strategy."""
        ...


class ValidatorFactory(Protocol):
    """Protocol for validator factory."""

    def create_validator(self) -> ValidationService:
        """Create a validator."""
        ...


class ScreenerFactory(Protocol):
    """Protocol for screener factory."""

    def create_screener(
        self,
        repository: DataRepository,
        scoring_strategy: ScoringService | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener."""
        ...


class DependencyFactory(ABC):
    """Abstract factory for creating DGI Toolkit dependencies."""

    @abstractmethod
    def create_repository(self, data_path: str) -> DataRepository:
        """Create a data repository."""

    @abstractmethod
    def create_scoring_strategy(self) -> ScoringService:
        """Create a scoring strategy."""

    @abstractmethod
    def create_filter_strategy(self) -> BaseFilter:
        """Create a filter strategy."""

    @abstractmethod
    def create_validator(self) -> ValidationService:
        """Create a validator."""

    @abstractmethod
    def create_screener(
        self,
        repository: DataRepository,
        scoring_strategy: ScoringService | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener."""


class ProductionDependencyFactory(DependencyFactory):
    """Production factory for creating dependencies."""

    def create_repository(self, data_path: str) -> DataRepository:
        """Create a CSV repository for production use."""
        # Create adapter to make ValidationService compatible with CSV repository
        from dgi.models import CompanyData
        from dgi.validation_utils import DgiRowValidator, PydanticRowValidation

        # Create the row validator that the CSV repository expects
        row_validator = DgiRowValidator(PydanticRowValidation(CompanyData))

        repository = CsvCompanyDataRepository(data_path, row_validator)
        return cast(DataRepository, repository)

    def create_scoring_strategy(self) -> ScoringService:
        """Create a scoring strategy for production use."""
        scoring_strategy = DefaultScoring()
        adapter = ScoringStrategyAdapter(scoring_strategy)
        return cast(ScoringService, adapter)

    def create_filter_strategy(self) -> BaseFilter:
        """Create a filter strategy for production use."""
        return DefaultFilter()

    def create_validator(self) -> ValidationService:
        """Create a validation service for production use."""
        from dgi.services.validation_service import ValidationService

        return ValidationService()

    def create_screener(
        self,
        repository: DataRepository,
        scoring_strategy: ScoringService | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener for production use."""
        if scoring_strategy is None:
            scoring_strategy = self.create_scoring_strategy()
        if filter_strategy is None:
            filter_strategy = self.create_filter_strategy()

        # Convert DataRepository to CompanyDataRepository
        company_repository = cast(CompanyDataRepository, repository)

        # Create a list of filters from the scoring strategy
        filters: list[CompanyFilter] = []

        # Create a scoring strategy from the scoring service
        scoring_strategy_obj = cast(ScoringStrategy, scoring_strategy)

        return Screener(
            repository=company_repository,
            filters=filters,
            scoring_strategy=scoring_strategy_obj,
            filter_strategy=filter_strategy,
        )


class TestDependencyFactory(DependencyFactory):
    """Test factory for creating dependencies with test-specific configurations."""

    def create_repository(self, data_path: str) -> DataRepository:
        """Create a CSV repository for testing."""
        # Create adapter to make ValidationService compatible with CSV repository
        from dgi.models import CompanyData
        from dgi.validation_utils import DgiRowValidator, PydanticRowValidation

        # Create the row validator that the CSV repository expects
        row_validator = DgiRowValidator(PydanticRowValidation(CompanyData))

        repository = CsvCompanyDataRepository(data_path, row_validator)
        return cast(DataRepository, repository)

    def create_scoring_strategy(self) -> ScoringService:
        """Create a scoring strategy for testing."""
        scoring_strategy = DefaultScoring()
        adapter = ScoringStrategyAdapter(scoring_strategy)
        return cast(ScoringService, adapter)

    def create_filter_strategy(self) -> BaseFilter:
        """Create a filter strategy for testing."""
        return DefaultFilter()

    def create_validator(self) -> ValidationService:
        """Create a validation service for testing."""
        from dgi.services.validation_service import ValidationService

        return ValidationService()

    def create_screener(
        self,
        repository: DataRepository,
        scoring_strategy: ScoringService | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a screener for testing."""
        if scoring_strategy is None:
            scoring_strategy = self.create_scoring_strategy()
        if filter_strategy is None:
            filter_strategy = self.create_filter_strategy()

        # Convert DataRepository to CompanyDataRepository
        company_repository = cast(CompanyDataRepository, repository)

        # Create a list of filters from the scoring strategy
        filters: list[CompanyFilter] = []

        # Create a scoring strategy from the scoring service
        scoring_strategy_obj = cast(ScoringStrategy, scoring_strategy)

        return Screener(
            repository=company_repository,
            filters=filters,
            scoring_strategy=scoring_strategy_obj,
            filter_strategy=filter_strategy,
        )


class MockDependencyFactory(DependencyFactory):
    """Mock factory for creating dependencies with mock objects for testing."""

    def __init__(
        self,
        mock_repository: DataRepository | None = None,
        mock_scoring: ScoringService | None = None,
        mock_filter: BaseFilter | None = None,
    ) -> None:
        """Initialize with optional mock objects."""
        self._mock_repository = mock_repository
        self._mock_scoring = mock_scoring
        self._mock_filter = mock_filter

    def create_repository(self, data_path: str) -> DataRepository:
        """Create a mock repository."""
        if self._mock_repository is not None:
            return self._mock_repository
        raise FactoryError("Mock repository not provided")

    def create_scoring_strategy(self) -> ScoringService:
        """Create a mock scoring strategy."""
        if self._mock_scoring is not None:
            return self._mock_scoring
        raise FactoryError("Mock scoring strategy not provided")

    def create_filter_strategy(self) -> BaseFilter:
        """Create a mock filter strategy."""
        if self._mock_filter is not None:
            return self._mock_filter
        raise FactoryError("Mock filter strategy not provided")

    def create_validator(self) -> ValidationService:
        """Create a mock validation service."""
        from dgi.services.validation_service import ValidationService

        return ValidationService()

    def create_screener(
        self,
        repository: DataRepository,
        scoring_strategy: ScoringService | None = None,
        filter_strategy: BaseFilter | None = None,
    ) -> Screener:
        """Create a mock screener."""
        if scoring_strategy is None:
            scoring_strategy = self.create_scoring_strategy()
        if filter_strategy is None:
            filter_strategy = self.create_filter_strategy()

        # Convert DataRepository to CompanyDataRepository
        company_repository = cast(CompanyDataRepository, repository)

        # Create a list of filters from the scoring strategy
        filters: list[CompanyFilter] = []

        # Create a scoring strategy from the scoring service
        scoring_strategy_obj = cast(ScoringStrategy, scoring_strategy)

        return Screener(
            repository=company_repository,
            filters=filters,
            scoring_strategy=scoring_strategy_obj,
            filter_strategy=filter_strategy,
        )


class FactoryRegistry:
    """Registry for managing dependency factories."""

    def __init__(self) -> None:
        """Initialize the factory registry."""
        self._factories: dict[str, DependencyFactory] = {}
        self._current_factory: str | None = None

        # Register default factories
        self.register_factory("production", ProductionDependencyFactory())
        self.register_factory("test", TestDependencyFactory())
        self.set_current_factory("production")

    def register_factory(self, name: str, factory: DependencyFactory) -> None:
        """Register a factory with a name."""
        self._factories[name] = factory

    def get_factory(self, name: str | None = None) -> DependencyFactory:
        """Get a factory by name."""
        factory_name = name or self._current_factory
        if factory_name is None:
            raise FactoryError("No factory name specified and no current factory set")
        if factory_name not in self._factories:
            raise FactoryError(f"Factory '{factory_name}' not found")
        return self._factories[factory_name]

    def set_current_factory(self, name: str) -> None:
        """Set the current factory."""
        if name not in self._factories:
            raise FactoryError(f"Factory '{name}' not found")
        self._current_factory = name

    def get_current_factory(self) -> DependencyFactory:
        """Get the current factory."""
        if self._current_factory is None:
            raise FactoryError("No current factory set")
        return self.get_factory(self._current_factory)


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


def create_repository(
    data_path: str, factory_name: str | None = None
) -> DataRepository:
    """Create a repository using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_repository(data_path)


def create_screener(
    repository: DataRepository,
    scoring_strategy: ScoringService | None = None,
    filter_strategy: BaseFilter | None = None,
    screening_service: Any = None,
    factory_name: str | None = None,
) -> Screener:
    """Create a screener using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_screener(repository, scoring_strategy, filter_strategy)


def create_validator(factory_name: str | None = None) -> ValidationService:
    """Create a validator using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_validator()


def create_scoring_strategy(factory_name: str | None = None) -> ScoringService:
    """Create a scoring strategy using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_scoring_strategy()


def create_filter_strategy(factory_name: str | None = None) -> BaseFilter:
    """Create a filter strategy using the specified factory."""
    factory = get_dependency_factory(factory_name)
    return factory.create_filter_strategy()
