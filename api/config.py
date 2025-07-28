"""Configuration management for DGI Toolkit API."""

import os

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API configuration settings using Pydantic BaseSettings."""

    # API settings
    api_title: str = "DGI Toolkit API"
    api_description: str = (
        "API for Dividend Growth Investing (DGI) stock screening and analysis"
    )
    api_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(
        default_factory=lambda: os.environ.get("DGI_ENVIRONMENT", "development"),
        description="Environment (development, test, production)",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Enable auto-reload")

    # Data settings
    data_path: str = Field(
        default_factory=lambda: os.environ.get(
            "DGI_DATA_PATH", "data/fundamentals_small.csv"
        ),
        description="Path to the data file",
    )

    # Rate limiting
    rate_limit_requests: int = Field(
        default=100, description="Number of requests allowed per period"
    )
    rate_limit_period: int = Field(
        default=60, description="Rate limit period in seconds"
    )

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS"
    )
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"], description="Allowed HTTP headers"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Security settings
    enable_security_headers: bool = Field(
        default=True, description="Enable security headers"
    )
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")

    # Validation settings
    max_top_n: int = Field(
        default=100, description="Maximum number of stocks to return"
    )
    min_yield_range: tuple[float, float] = Field(
        default=(0.0, 100.0), description="Valid range for dividend yield"
    )
    max_payout_range: tuple[float, float] = Field(
        default=(0.0, 200.0), description="Valid range for payout ratio"
    )
    cagr_range: tuple[float, float] = Field(
        default=(-100.0, 100.0), description="Valid range for dividend CAGR"
    )

    @field_validator("data_path")
    @classmethod
    def validate_data_path(cls, v: str) -> str:
        """Validate data path is not empty."""
        if not v or not v.strip():
            raise ValueError("data_path cannot be empty")
        return v.strip()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is valid."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v.lower()

    @field_validator("rate_limit_requests")
    @classmethod
    def validate_rate_limit_requests(cls, v: int) -> int:
        """Validate rate limit requests is positive."""
        if v <= 0:
            raise ValueError("rate_limit_requests must be positive")
        return v

    @field_validator("rate_limit_period")
    @classmethod
    def validate_rate_limit_period(cls, v: int) -> int:
        """Validate rate limit period is positive."""
        if v <= 0:
            raise ValueError("rate_limit_period must be positive")
        return v

    @field_validator("max_top_n")
    @classmethod
    def validate_max_top_n(cls, v: int) -> int:
        """Validate max top N is positive."""
        if v <= 0:
            raise ValueError("max_top_n must be positive")
        return v

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DGI_API_",
        case_sensitive=False,
    )


# Global settings instance - lazy loading to support test isolation
_settings = None


def get_settings() -> APISettings:
    """Get the global settings instance with lazy loading.

    This ensures that environment variables are read at the time of access,
    not at module import time, which is crucial for test isolation.

    Returns:
        APISettings instance
    """
    global _settings
    if _settings is None:
        _settings = APISettings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing).

    This allows tests to set environment variables and get fresh settings.
    """
    global _settings
    _settings = None


def validate_configuration() -> None:
    """Validate the configuration on startup.

    Raises:
        ValueError: If configuration is invalid
    """
    settings = get_settings()

    # Check if data file exists
    if not os.path.exists(settings.data_path):
        raise ValueError(f"Data file not found: {settings.data_path}")

    # Validate environment
    if settings.debug:
        print("⚠️  Running in DEBUG mode")

    print(f"📊 Data path: {settings.data_path}")
    print(
        f"🔒 Security headers: {'enabled' if settings.enable_security_headers else 'disabled'}"
    )
    print(
        f"⏱️  Rate limiting: {'enabled' if settings.enable_rate_limiting else 'disabled'}"
    )
    print(f"📝 Log level: {settings.log_level}")
    print(f"🌐 CORS origins: {settings.cors_origins}")
