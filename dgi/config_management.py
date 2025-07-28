"""
Enhanced configuration management system with strategy patterns.

This module provides enterprise-grade configuration management features:
- Strategy pattern for different configuration sources
- Configuration validation and composition
- Environment-specific configuration loading
- Hot-reload capabilities for dynamic updates
- Configuration change monitoring and notifications
"""

import json
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from dgi.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseSettings)


class ConfigurationSource(Enum):
    """Configuration source types."""

    ENVIRONMENT = "environment"
    FILE = "file"
    DATABASE = "database"
    REMOTE = "remote"
    DEFAULT = "default"


class ConfigurationFormat(Enum):
    """Configuration file formats."""

    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"


class ConfigurationStrategy(ABC):
    """Abstract base class for configuration loading strategies."""

    @abstractmethod
    def load_config(self) -> dict[str, Any]:
        """Load configuration from the strategy's source."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the configuration source is available."""

    def get_priority(self) -> int:
        """Get the priority of this configuration source (lower = higher priority)."""
        return 100


class EnvironmentConfigStrategy(ConfigurationStrategy):
    """Load configuration from environment variables."""

    def __init__(self, prefix: str = "DGI_"):
        """Initialize with environment variable prefix."""
        self.prefix = prefix

    def load_config(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(self.prefix) :].lower()
                # Try to parse as JSON, fallback to string
                try:
                    config[config_key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    config[config_key] = value

        logger.debug(f"Loaded {len(config)} settings from environment variables")
        return config

    def is_available(self) -> bool:
        """Check if environment variables are available."""
        return any(key.startswith(self.prefix) for key in os.environ)

    def get_priority(self) -> int:
        """Environment variables have high priority."""
        return 10


class FileConfigStrategy(ConfigurationStrategy):
    """Load configuration from files (JSON, YAML, TOML)."""

    def __init__(
        self, file_path: str | Path, format_type: ConfigurationFormat | None = None
    ):
        """Initialize with file path and optional format."""
        self.file_path = Path(file_path)
        self.format_type = format_type or self._detect_format()

    def _detect_format(self) -> ConfigurationFormat:
        """Detect configuration format from file extension."""
        suffix = self.file_path.suffix.lower()
        if suffix in [".json"]:
            return ConfigurationFormat.JSON
        elif suffix in [".yml", ".yaml"]:
            return ConfigurationFormat.YAML
        elif suffix in [".toml"]:
            return ConfigurationFormat.TOML
        elif suffix in [".env"]:
            return ConfigurationFormat.ENV
        else:
            raise ConfigurationError(f"Unsupported configuration file format: {suffix}")

    def load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not self.file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.file_path}")

        try:
            with open(self.file_path, encoding="utf-8") as f:
                if self.format_type == ConfigurationFormat.JSON:
                    config = json.load(f)
                elif self.format_type == ConfigurationFormat.YAML:
                    config = yaml.safe_load(f)
                elif self.format_type == ConfigurationFormat.ENV:
                    config = self._parse_env_file(f)
                else:
                    raise ConfigurationError(f"Unsupported format: {self.format_type}")

            logger.info(f"Loaded configuration from {self.file_path}")
            return config

        except Exception as e:
            raise ConfigurationError(
                f"Failed to load config from {self.file_path}: {e}"
            ) from e

    def _parse_env_file(self, file_handle) -> dict[str, Any]:
        """Parse .env file format."""
        config = {}
        for line in file_handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip("\"'")
        return config

    def is_available(self) -> bool:
        """Check if configuration file exists."""
        return self.file_path.exists()

    def get_priority(self) -> int:
        """File configurations have medium priority."""
        return 50


class DefaultConfigStrategy(ConfigurationStrategy):
    """Provide default configuration values."""

    def __init__(self, defaults: dict[str, Any]):
        """Initialize with default values."""
        self.defaults = defaults

    def load_config(self) -> dict[str, Any]:
        """Return default configuration."""
        logger.debug(f"Using default configuration with {len(self.defaults)} settings")
        return self.defaults.copy()

    def is_available(self) -> bool:
        """Default configuration is always available."""
        return True

    def get_priority(self) -> int:
        """Default configuration has lowest priority."""
        return 999


class ConfigurationComposer:
    """Compose configuration from multiple sources with priority ordering."""

    def __init__(self):
        """Initialize configuration composer."""
        self.strategies: list[ConfigurationStrategy] = []
        self._cache: dict[str, Any] | None = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 300  # 5 minutes

    def add_strategy(self, strategy: ConfigurationStrategy) -> "ConfigurationComposer":
        """Add a configuration strategy."""
        self.strategies.append(strategy)
        self._invalidate_cache()
        return self

    def compose_config(self, force_reload: bool = False) -> dict[str, Any]:
        """Compose configuration from all available strategies."""
        # Check cache first
        if not force_reload and self._is_cache_valid():
            return self._cache.copy()

        # Sort strategies by priority
        available_strategies = [s for s in self.strategies if s.is_available()]
        available_strategies.sort(key=lambda s: s.get_priority())

        # Compose configuration
        composed_config = {}

        for strategy in available_strategies:
            try:
                strategy_config = strategy.load_config()
                # Merge with lower priority taking precedence for existing keys
                for key, value in strategy_config.items():
                    if key not in composed_config:
                        composed_config[key] = value

                logger.debug(f"Applied configuration from {type(strategy).__name__}")

            except Exception as e:
                logger.warning(
                    f"Failed to load config from {type(strategy).__name__}: {e}"
                )
                continue

        # Cache the result
        self._cache = composed_config
        self._cache_timestamp = time.time()

        logger.info(f"Composed configuration from {len(available_strategies)} sources")
        return composed_config.copy()

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        return (
            self._cache is not None
            and time.time() - self._cache_timestamp < self._cache_ttl
        )

    def _invalidate_cache(self):
        """Invalidate configuration cache."""
        self._cache = None
        self._cache_timestamp = 0


class ConfigurationValidator:
    """Validate configuration against Pydantic models."""

    def __init__(self, settings_class: type[BaseSettings]):
        """Initialize with settings class for validation."""
        self.settings_class = settings_class

    def validate_config(self, config: dict[str, Any]) -> BaseSettings:
        """Validate configuration and return settings instance."""
        try:
            # Convert config dict to settings instance
            return self.settings_class(**config)
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e}") from e

    def validate_partial_config(self, config: dict[str, Any]) -> list[str]:
        """Validate partial configuration and return list of errors."""
        errors = []
        try:
            self.settings_class(**config)
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"{field}: {error['msg']}")
        return errors


class ConfigurationChangeHandler(FileSystemEventHandler):
    """Handle configuration file changes for hot-reload."""

    def __init__(self, callback: Callable[[], None]):
        """Initialize with callback function."""
        self.callback = callback
        super().__init__()

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            logger.info(f"Configuration file changed: {event.src_path}")
            self.callback()


class ConfigurationManager:
    """Enterprise configuration manager with hot-reload and validation."""

    def __init__(self, settings_class: type[T]):
        """Initialize configuration manager."""
        self.settings_class = settings_class
        self.composer = ConfigurationComposer()
        self.validator = ConfigurationValidator(settings_class)
        self._current_settings: T | None = None
        self._observers: list[Observer] = []
        self._change_callbacks: list[Callable[[T], None]] = []
        self._lock = threading.RLock()

    def add_environment_config(self, prefix: str = "DGI_") -> "ConfigurationManager":
        """Add environment variable configuration source."""
        self.composer.add_strategy(EnvironmentConfigStrategy(prefix))
        return self

    def add_file_config(
        self, file_path: str | Path, watch: bool = True
    ) -> "ConfigurationManager":
        """Add file configuration source with optional file watching."""
        strategy = FileConfigStrategy(file_path)
        self.composer.add_strategy(strategy)

        if watch and strategy.is_available():
            self._watch_file(Path(file_path))

        return self

    def add_default_config(self, defaults: dict[str, Any]) -> "ConfigurationManager":
        """Add default configuration values."""
        self.composer.add_strategy(DefaultConfigStrategy(defaults))
        return self

    def load_settings(self, force_reload: bool = False) -> T:
        """Load and validate settings from all sources."""
        with self._lock:
            if not force_reload and self._current_settings is not None:
                return self._current_settings

            # Compose configuration
            raw_config = self.composer.compose_config(force_reload)

            # Validate and create settings instance
            settings = self.validator.validate_config(raw_config)

            # Store current settings
            old_settings = self._current_settings
            self._current_settings = settings

            # Notify change callbacks if settings changed
            if old_settings != settings:
                self._notify_change_callbacks(settings)

            logger.info("Configuration loaded and validated successfully")
            return settings

    def get_current_settings(self) -> T | None:
        """Get current settings without reloading."""
        return self._current_settings

    def reload_settings(self) -> T:
        """Force reload settings from all sources."""
        logger.info("Reloading configuration from all sources")
        return self.load_settings(force_reload=True)

    def add_change_callback(self, callback: Callable[[T], None]):
        """Add callback to be notified when configuration changes."""
        self._change_callbacks.append(callback)

    def _watch_file(self, file_path: Path):
        """Set up file watching for hot-reload."""
        observer = Observer()
        handler = ConfigurationChangeHandler(self._on_config_change)
        observer.schedule(handler, str(file_path.parent), recursive=False)
        observer.start()
        self._observers.append(observer)
        logger.info(f"Watching configuration file: {file_path}")

    def _on_config_change(self):
        """Handle configuration file changes."""
        try:
            self.reload_settings()
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")

    def _notify_change_callbacks(self, new_settings: T):
        """Notify all change callbacks."""
        for callback in self._change_callbacks:
            try:
                callback(new_settings)
            except Exception as e:
                logger.error(f"Configuration change callback failed: {e}")

    def stop_watching(self):
        """Stop all file watchers."""
        for observer in self._observers:
            observer.stop()
            observer.join()
        self._observers.clear()
        logger.info("Stopped configuration file watching")

    @contextmanager
    def temporary_config(self, overrides: dict[str, Any]):
        """Temporarily override configuration values."""
        original_settings = self._current_settings
        try:
            # Apply overrides
            if original_settings:
                current_dict = original_settings.model_dump()
                current_dict.update(overrides)
                temp_settings = self.validator.validate_config(current_dict)
                self._current_settings = temp_settings
                yield temp_settings
            else:
                yield None
        finally:
            # Restore original settings
            self._current_settings = original_settings


# Convenience functions for common configuration patterns
def create_api_config_manager() -> ConfigurationManager:
    """Create configuration manager for API settings."""
    from api.config import APISettings

    manager = ConfigurationManager(APISettings)

    # Add configuration sources in priority order
    manager.add_environment_config("DGI_API_")
    manager.add_file_config("config/api.yaml", watch=True)
    manager.add_file_config("config/api.json", watch=True)
    manager.add_default_config(
        {
            "debug": False,
            "environment": "production",
            "host": "0.0.0.0",  # nosec B104 - Default host for API config
            "port": 8000,
        }
    )

    return manager


def create_core_config_manager() -> ConfigurationManager:
    """Create configuration manager for core DGI settings."""
    from dgi.config import CoreSettings

    manager = ConfigurationManager(CoreSettings)

    # Add configuration sources in priority order
    manager.add_environment_config("DGI_CORE_")
    manager.add_file_config("config/core.yaml", watch=True)
    manager.add_file_config("config/core.json", watch=True)
    manager.add_default_config(
        {
            "log_level": "INFO",
            "default_min_yield": 2.0,
            "default_max_payout": 80.0,
            "default_min_cagr": 5.0,
        }
    )

    return manager
