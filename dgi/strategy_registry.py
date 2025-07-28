"""Strategy registry for dynamic strategy management.

This module implements a registry pattern that allows strategies to be registered
dynamically without violating the Open/Closed Principle. New strategies can be
added without modifying existing factory code.
"""

import logging
from collections.abc import Callable
from typing import Any, Protocol

from dgi.exceptions import FactoryError

logger = logging.getLogger(__name__)


class StrategyBuilder(Protocol):
    """Protocol for strategy builders."""

    def __call__(self, **kwargs: Any) -> Any:
        """Build a strategy instance."""
        ...


class StrategyMetadata:
    """Metadata for a registered strategy."""

    def __init__(
        self,
        name: str,
        builder: Callable[..., Any],
        description: str = "",
        tags: list[str] | None = None,
        **metadata: Any,
    ) -> None:
        """Initialize strategy metadata.

        Args:
            name: Strategy name
            builder: Function to build the strategy
            description: Strategy description
            tags: Strategy tags for categorization
            **metadata: Additional metadata
        """
        self.name = name
        self.builder = builder
        self.description = description
        self.tags = tags or []
        self.metadata = metadata


class StrategyRegistry:
    """Registry for managing strategies dynamically."""

    def __init__(self, registry_name: str) -> None:
        """Initialize strategy registry.

        Args:
            registry_name: Name of this registry
        """
        self.registry_name = registry_name
        self._strategies: dict[str, StrategyMetadata] = {}
        self._default_strategy: str | None = None

    def register(
        self,
        name: str,
        builder: Callable[..., Any],
        description: str = "",
        tags: list[str] | None = None,
        is_default: bool = False,
        **metadata: Any,
    ) -> None:
        """Register a strategy.

        Args:
            name: Strategy name
            builder: Function to build the strategy
            description: Strategy description
            tags: Strategy tags for categorization
            is_default: Whether this is the default strategy
            **metadata: Additional metadata
        """
        if name in self._strategies:
            logger.warning(f"Overwriting strategy '{name}' in {self.registry_name}")

        strategy_metadata = StrategyMetadata(
            name=name, builder=builder, description=description, tags=tags, **metadata
        )

        self._strategies[name] = strategy_metadata

        if is_default or self._default_strategy is None:
            self._default_strategy = name

        logger.info(f"Registered strategy '{name}' in {self.registry_name}")

    def get_strategy(self, name: str | None = None, **kwargs: Any) -> Any:
        """Get a strategy instance.

        Args:
            name: Strategy name, uses default if None
            **kwargs: Arguments to pass to strategy builder

        Returns:
            Strategy instance

        Raises:
            FactoryError: If strategy not found
        """
        strategy_name = name or self._default_strategy

        if strategy_name is None:
            raise FactoryError(f"No default strategy set in {self.registry_name}")

        if strategy_name not in self._strategies:
            available = list(self._strategies.keys())
            raise FactoryError(
                f"Strategy '{strategy_name}' not found in {self.registry_name}. "
                f"Available: {available}"
            )

        metadata = self._strategies[strategy_name]

        try:
            return metadata.builder(**kwargs)
        except Exception as e:
            raise FactoryError(
                f"Failed to build strategy '{strategy_name}': {e}"
            ) from e

    def list_strategies(self, tags: list[str] | None = None) -> list[str]:
        """List available strategies.

        Args:
            tags: Filter by tags if provided

        Returns:
            List of strategy names
        """
        if tags is None:
            return list(self._strategies.keys())

        return [
            name
            for name, metadata in self._strategies.items()
            if any(tag in metadata.tags for tag in tags)
        ]

    def get_metadata(self, name: str) -> StrategyMetadata | None:
        """Get strategy metadata.

        Args:
            name: Strategy name

        Returns:
            Strategy metadata or None if not found
        """
        return self._strategies.get(name)

    def set_default(self, name: str) -> None:
        """Set default strategy.

        Args:
            name: Strategy name

        Raises:
            FactoryError: If strategy not found
        """
        if name not in self._strategies:
            raise FactoryError(f"Strategy '{name}' not found in {self.registry_name}")

        self._default_strategy = name
        logger.info(f"Set default strategy to '{name}' in {self.registry_name}")


class StrategyRegistryManager:
    """Manager for multiple strategy registries."""

    def __init__(self) -> None:
        """Initialize registry manager."""
        self._registries: dict[str, StrategyRegistry] = {}

    def get_registry(self, name: str) -> StrategyRegistry:
        """Get or create a strategy registry.

        Args:
            name: Registry name

        Returns:
            Strategy registry
        """
        if name not in self._registries:
            self._registries[name] = StrategyRegistry(name)
            logger.info(f"Created strategy registry '{name}'")

        return self._registries[name]

    def register_strategy(
        self,
        registry_name: str,
        strategy_name: str,
        builder: Callable[..., Any],
        **kwargs: Any,
    ) -> None:
        """Register a strategy in a specific registry.

        Args:
            registry_name: Registry name
            strategy_name: Strategy name
            builder: Strategy builder function
            **kwargs: Additional registration parameters
        """
        registry = self.get_registry(registry_name)
        registry.register(strategy_name, builder, **kwargs)


# Global strategy registry manager
_strategy_manager = StrategyRegistryManager()


def get_strategy_registry(name: str) -> StrategyRegistry:
    """Get a strategy registry.

    Args:
        name: Registry name

    Returns:
        Strategy registry
    """
    return _strategy_manager.get_registry(name)


def register_strategy(
    registry_name: str, strategy_name: str, builder: Callable[..., Any], **kwargs: Any
) -> None:
    """Register a strategy globally.

    Args:
        registry_name: Registry name
        strategy_name: Strategy name
        builder: Strategy builder function
        **kwargs: Additional registration parameters
    """
    _strategy_manager.register_strategy(registry_name, strategy_name, builder, **kwargs)
