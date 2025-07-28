"""Enhanced factory implementation using strategy registry.

This module extends the existing factory pattern to use strategy registries,
allowing new strategies to be added without modifying existing factory code.
"""

import logging
from typing import Any

from dgi.filtering import BaseFilter, DefaultFilter
from dgi.models.company import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring, ScoringStrategy
from dgi.screener import Screener
from dgi.strategy_registry import get_strategy_registry
from dgi.validation_utils import DgiRowValidator, PydanticRowValidation

from .factory import DependencyFactory

logger = logging.getLogger(__name__)


class RegistryBasedFactory(DependencyFactory):
    """Factory that uses strategy registries for extensibility."""

    def __init__(self, factory_type: str = "default") -> None:
        """Initialize registry-based factory.

        Args:
            factory_type: Type of factory (default, test, production)
        """
        self.factory_type = factory_type
        self._initialize_registries()

    def _initialize_registries(self) -> None:
        """Initialize strategy registries with default strategies."""
        # Register default scoring strategies
        scoring_registry = get_strategy_registry("scoring")
        scoring_registry.register(
            "default",
            lambda: DefaultScoring(),
            description="Default DGI scoring strategy",
            tags=["default", "dgi"],
            is_default=True,
        )

        # Register default filtering strategies
        filtering_registry = get_strategy_registry("filtering")
        filtering_registry.register(
            "default",
            lambda: DefaultFilter(),
            description="Default DGI filter strategy",
            tags=["default", "dgi"],
            is_default=True,
        )

        # Register repository strategies
        repository_registry = get_strategy_registry("repository")
        repository_registry.register(
            "csv",
            lambda data_path, validator: CsvCompanyDataRepository(data_path, validator),
            description="CSV-based data repository",
            tags=["csv", "file"],
            is_default=True,
        )

        # Register validator strategies
        validator_registry = get_strategy_registry("validator")
        validator_registry.register(
            "pydantic",
            lambda: DgiRowValidator(PydanticRowValidation(CompanyData)),
            description="Pydantic-based row validation",
            tags=["pydantic", "validation"],
            is_default=True,
        )

    def create_repository(self, data_path: str) -> CompanyDataRepository:
        """Create a repository using strategy registry."""
        repository_registry = get_strategy_registry("repository")
        validator = self.create_validator()

        return repository_registry.get_strategy(
            name="csv",  # Could be configurable
            data_path=data_path,
            validator=validator,
        )

    def create_scoring_strategy(
        self, strategy_name: str | None = None
    ) -> ScoringStrategy:
        """Create a scoring strategy using strategy registry.

        Args:
            strategy_name: Name of strategy to create, uses default if None

        Returns:
            ScoringStrategy instance
        """
        scoring_registry = get_strategy_registry("scoring")
        return scoring_registry.get_strategy(name=strategy_name)

    def create_filter_strategy(self, strategy_name: str | None = None) -> BaseFilter:
        """Create a filter strategy using strategy registry.

        Args:
            strategy_name: Name of strategy to create, uses default if None

        Returns:
            BaseFilter instance
        """
        filtering_registry = get_strategy_registry("filtering")
        return filtering_registry.get_strategy(name=strategy_name)

    def create_validator(self, strategy_name: str | None = None) -> DgiRowValidator:
        """Create a validator using strategy registry.

        Args:
            strategy_name: Name of strategy to create, uses default if None

        Returns:
            DgiRowValidator instance
        """
        validator_registry = get_strategy_registry("validator")
        return validator_registry.get_strategy(name=strategy_name)

    def create_screener(
        self,
        repository: CompanyDataRepository,
        scoring_strategy: ScoringStrategy | None = None,
        filter_strategy: BaseFilter | None = None,
        scoring_strategy_name: str | None = None,
        filter_strategy_name: str | None = None,
    ) -> Screener:
        """Create a screener with flexible strategy selection.

        Args:
            repository: Data repository
            scoring_strategy: Specific scoring strategy instance
            filter_strategy: Specific filter strategy instance
            scoring_strategy_name: Name of scoring strategy to create
            filter_strategy_name: Name of filter strategy to create

        Returns:
            Screener instance
        """
        # Use provided instances or create from registry
        if scoring_strategy is None:
            scoring_strategy = self.create_scoring_strategy(scoring_strategy_name)

        if filter_strategy is None:
            filter_strategy = self.create_filter_strategy(filter_strategy_name)

        return Screener(
            repository=repository,
            scoring_strategy=scoring_strategy,
            filter_strategy=filter_strategy,
        )

    def list_available_strategies(self, strategy_type: str) -> list[str]:
        """List available strategies for a given type.

        Args:
            strategy_type: Type of strategy (scoring, filtering, repository, validator)

        Returns:
            List of available strategy names
        """
        registry = get_strategy_registry(strategy_type)
        return registry.list_strategies()

    def get_strategy_metadata(self, strategy_type: str, strategy_name: str) -> Any:
        """Get metadata for a strategy.

        Args:
            strategy_type: Type of strategy
            strategy_name: Name of strategy

        Returns:
            Strategy metadata or None
        """
        registry = get_strategy_registry(strategy_type)
        return registry.get_metadata(strategy_name)


# Example of how to extend the system without modifying existing code
def register_advanced_scoring_strategies() -> None:
    """Register advanced scoring strategies without modifying factory code."""
    from dgi.scoring import (
        CompositeScoringStrategy,
        DividendGrowthScoring,
        DividendYieldScoring,
        WeightedScoringStrategy,
    )

    scoring_registry = get_strategy_registry("scoring")

    # Register individual component strategies
    scoring_registry.register(
        "dividend_yield",
        lambda: DividendYieldScoring(),
        description="Focus on dividend yield",
        tags=["yield", "income"],
    )

    scoring_registry.register(
        "dividend_growth",
        lambda: DividendGrowthScoring(),
        description="Focus on dividend growth",
        tags=["growth", "appreciation"],
    )

    # Register composite strategies
    scoring_registry.register(
        "balanced",
        lambda: CompositeScoringStrategy(
            [
                DividendYieldScoring(),
                DividendGrowthScoring(),
            ]
        ),
        description="Balanced yield and growth strategy",
        tags=["balanced", "composite"],
    )

    scoring_registry.register(
        "weighted_balanced",
        lambda: WeightedScoringStrategy(
            [
                (DividendYieldScoring(), 0.6),
                (DividendGrowthScoring(), 0.4),
            ]
        ),
        description="Weighted balanced strategy favoring yield",
        tags=["weighted", "yield-focused"],
    )

    logger.info("Registered advanced scoring strategies")


def register_advanced_filtering_strategies() -> None:
    """Register advanced filtering strategies without modifying factory code."""
    from dgi.filtering import (
        CompositeFilter,
        SectorFilter,
        TopNFilter,
        YieldOnlyFilter,
    )

    filtering_registry = get_strategy_registry("filtering")

    # Register specific filters
    filtering_registry.register(
        "yield_only",
        lambda: YieldOnlyFilter(),
        description="Filter by yield criteria only",
        tags=["yield", "simple"],
    )

    filtering_registry.register(
        "tech_sector",
        lambda: SectorFilter(allowed_sectors=["Technology"]),
        description="Filter for technology sector only",
        tags=["sector", "tech"],
    )

    filtering_registry.register(
        "top_10",
        lambda: TopNFilter(n=10),
        description="Return top 10 stocks by score",
        tags=["ranking", "top"],
    )

    # Register composite filters
    filtering_registry.register(
        "tech_yield_top_10",
        lambda: CompositeFilter(
            [
                SectorFilter(allowed_sectors=["Technology"]),
                YieldOnlyFilter(),
                TopNFilter(n=10),
            ]
        ),
        description="Tech stocks with good yield, top 10",
        tags=["composite", "tech", "yield", "top"],
    )

    logger.info("Registered advanced filtering strategies")


# Initialize the enhanced factory
def get_enhanced_factory(factory_type: str = "default") -> RegistryBasedFactory:
    """Get an enhanced factory instance.

    Args:
        factory_type: Type of factory

    Returns:
        RegistryBasedFactory instance
    """
    factory = RegistryBasedFactory(factory_type)

    # Register advanced strategies on first use
    try:
        register_advanced_scoring_strategies()
        register_advanced_filtering_strategies()
    except Exception as e:
        logger.warning(f"Failed to register some advanced strategies: {e}")

    return factory
