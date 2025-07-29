"""Configuration management for DGI Toolkit core functionality."""

import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    """Core DGI Toolkit configuration settings using Pydantic BaseSettings."""

    # Data settings
    data_path: str = Field(
        default="data/fundamentals_small.csv",
        description="Path to the data file",
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Default screening parameters
    default_min_yield: float = Field(
        default=2.0,
        ge=0.0,
        le=100.0,
        description="Default minimum dividend yield",
    )
    default_max_payout: float = Field(
        default=80.0,
        ge=0.0,
        le=200.0,
        description="Default maximum payout ratio",
    )
    default_min_cagr: float = Field(
        default=5.0,
        ge=-100.0,
        le=100.0,
        description="Default minimum dividend CAGR",
    )
    default_top_n: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Default number of top stocks to return",
    )

    # Screen parameter defaults
    default_screen_min_yield: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Default screen minimum yield",
    )
    default_screen_max_payout: float = Field(
        default=100.0,
        ge=0.0,
        le=200.0,
        description="Default screen maximum payout",
    )
    default_screen_min_cagr: float = Field(
        default=0.0,
        ge=-100.0,
        le=100.0,
        description="Default screen minimum CAGR",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("data_path")
    @classmethod
    def validate_data_path(cls, v: str) -> str:
        """Validate data path is not empty."""
        if not v or not v.strip():
            raise ValueError("data_path cannot be empty")
        return v.strip()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DGI_",
        case_sensitive=False,
    )


# Backward compatibility class
class Config:
    """Legacy configuration class for backward compatibility."""

    def __init__(self) -> None:
        settings = get_core_settings()
        self.DATA_PATH = settings.data_path
        self.LOG_LEVEL = settings.log_level
        self.DEFAULT_MIN_YIELD = settings.default_min_yield
        self.DEFAULT_MAX_PAYOUT = settings.default_max_payout
        self.DEFAULT_MIN_CAGR = settings.default_min_cagr
        self.DEFAULT_TOP_N = settings.default_top_n
        self.DEFAULT_SCREEN_MIN_YIELD = settings.default_screen_min_yield
        self.DEFAULT_SCREEN_MAX_PAYOUT = settings.default_screen_max_payout
        self.DEFAULT_SCREEN_MIN_CAGR = settings.default_screen_min_cagr


# Global settings instance - lazy loading to support test isolation
_core_settings = None


def get_core_settings() -> CoreSettings:
    """Get the global core settings instance with lazy loading.

    This ensures that environment variables are read at the time of access,
    not at module import time, which is crucial for test isolation.

    Returns:
        CoreSettings instance
    """
    global _core_settings
    if _core_settings is None:
        _core_settings = CoreSettings()
    return _core_settings


def reset_core_settings() -> None:
    """Reset the global core settings instance (useful for testing).

    This allows tests to set environment variables and get fresh settings.
    """
    global _core_settings
    _core_settings = None


def validate_core_configuration() -> None:
    """Validate the core configuration on startup.

    Raises:
        ValueError: If configuration is invalid
    """
    settings = get_core_settings()

    # Check if data file exists
    if not os.path.exists(settings.data_path):
        raise ValueError(f"Data file not found: {settings.data_path}")

    print(f"📊 Data path: {settings.data_path}")
    print(f"📝 Log level: {settings.log_level}")
    print(f"🎯 Default min yield: {settings.default_min_yield}%")
    print(f"🎯 Default max payout: {settings.default_max_payout}%")
    print(f"🎯 Default min CAGR: {settings.default_min_cagr}%")


def get_config() -> Config:
    """Get legacy configuration for backward compatibility."""
    return Config()
