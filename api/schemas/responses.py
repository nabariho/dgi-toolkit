"""Response schemas for DGI Toolkit API."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class HealthResponse(BaseModel):
    """Response model for health check endpoint.

    Provides comprehensive system health information including service status,
    system metrics, and data file accessibility for monitoring and alerting purposes.
    """

    status: str = Field(
        default="up",
        description="Service status - 'up' for healthy, 'down' for unhealthy",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="ISO 8601 formatted response timestamp",
    )
    version: str = Field(description="Current API version (e.g., '1.0.0')")
    environment: str = Field(
        description="Deployment environment (e.g., 'development', 'production', 'staging')"
    )
    uptime_seconds: float | None = Field(
        None, description="Service uptime in seconds since last restart"
    )
    memory_usage_mb: float | None = Field(
        None, description="Current memory usage in megabytes (MB)"
    )
    cpu_usage_percent: float | None = Field(
        None, description="Current CPU usage as a percentage (0-100)"
    )
    data_file_status: str | None = Field(
        None, description="Data file status: 'accessible', 'not_found', or 'error'"
    )
    data_file_size_mb: float | None = Field(
        None, description="Data file size in megabytes (MB)"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()


class StockResponse(BaseModel):
    """Response model for stock data.

    Represents a single stock with comprehensive dividend growth investing metrics
    including yield, payout ratio, growth rate, and composite scoring.
    """

    symbol: str = Field(description="Stock symbol/ticker (e.g., 'AAPL', 'JNJ', 'PG')")
    name: str = Field(
        description="Full company name (e.g., 'Apple Inc.', 'Johnson & Johnson')"
    )
    sector: str = Field(
        description="Business sector classification (e.g., 'Technology', 'Healthcare')"
    )
    industry: str = Field(
        description="Specific industry classification (e.g., 'Consumer Electronics', 'Drug Manufacturers')"
    )
    dividend_yield: float = Field(
        description="Annual dividend yield as decimal (e.g., 0.025 for 2.5%)"
    )
    payout: float = Field(
        description="Dividend payout ratio as percentage (e.g., 30.0 for 30%)"
    )
    dividend_cagr: float = Field(
        description="5-year compound annual growth rate as decimal (e.g., 0.08 for 8%)"
    )
    fcf_yield: float = Field(
        description="Free cash flow yield as percentage (e.g., 5.2 for 5.2%)"
    )
    score: float = Field(
        description="Composite DGI score from 0.0 to 1.0 (higher is better)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "dividend_yield": 0.025,
                "payout": 30.0,
                "dividend_cagr": 0.08,
                "fcf_yield": 5.2,
                "score": 0.75,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Response model for error responses."""

    error: dict[str, Any] = Field(description="Error details")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Error timestamp"
    )
    correlation_id: str | None = Field(None, description="Request correlation ID")

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "status_code": 422,
                    "details": {
                        "validation_errors": [
                            {
                                "field": "min_yield",
                                "message": "ensure this value is greater than 0",
                                "type": "value_error.number.not_gt",
                            }
                        ]
                    },
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "correlation_id": "req-12345",
            }
        }
    )


class ScreenResponse(BaseModel):
    """Response model for stock screening endpoint.

    Contains the results of a stock screening operation including the filtered stocks,
    applied filters, and performance metrics for monitoring and analysis.
    """

    stocks: list[StockResponse] = Field(
        description="List of screened stocks ranked by composite score"
    )
    total_count: int = Field(
        description="Total number of stocks returned in the response"
    )
    filters_applied: dict[str, Any] = Field(
        description="Dictionary of filters that were applied to the screening"
    )
    processing_time_ms: float | None = Field(
        None,
        description="Request processing time in milliseconds for performance monitoring",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stocks": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "sector": "Technology",
                        "industry": "Consumer Electronics",
                        "dividend_yield": 0.025,
                        "payout": 30.0,
                        "dividend_cagr": 0.08,
                        "fcf_yield": 5.2,
                        "score": 0.75,
                    }
                ],
                "total_count": 1,
                "filters_applied": {
                    "min_yield": 0.02,
                    "max_payout": 80.0,
                    "min_cagr": 0.05,
                    "top_n": 10,
                },
                "processing_time_ms": 45.2,
            }
        }
    )


class APIInfoResponse(BaseModel):
    """Response model for API information endpoint."""

    message: str = Field(description="API welcome message")
    version: str = Field(description="API version")
    docs_url: str = Field(description="API documentation URL")
    health_url: str = Field(description="Health check endpoint URL")
    endpoints: list[str] = Field(description="Available API endpoints")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Response timestamp"
    )

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "DGI Toolkit API",
                "version": "1.0.0",
                "docs_url": "/docs",
                "health_url": "/healthz",
                "endpoints": ["/api/v1/screen", "/healthz", "/docs"],
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
    )
