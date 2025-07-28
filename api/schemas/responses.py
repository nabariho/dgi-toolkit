"""Response schemas for DGI Toolkit API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(default="up", description="Service status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    version: str = Field(description="API version")
    environment: str = Field(description="Environment (development, production, etc.)")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class StockResponse(BaseModel):
    """Response model for stock data."""

    symbol: str = Field(description="Stock symbol/ticker")
    name: str = Field(description="Company name")
    sector: str = Field(description="Business sector")
    industry: str = Field(description="Industry classification")
    dividend_yield: float = Field(
        description="Dividend yield as decimal (e.g., 0.025 for 2.5%)"
    )
    payout: float = Field(description="Payout ratio as percentage (e.g., 30.0 for 30%)")
    dividend_cagr: float = Field(
        description="5-year dividend CAGR as decimal (e.g., 0.08 for 8%)"
    )
    fcf_yield: float = Field(description="Free cash flow yield as percentage")
    score: float = Field(description="Composite DGI score (0.0 to 1.0)")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
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


class ErrorResponse(BaseModel):
    """Response model for error responses."""

    error: dict[str, Any] = Field(description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    correlation_id: str | None = Field(None, description="Request correlation ID")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        json_schema_extra = {
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


class ScreenResponse(BaseModel):
    """Response model for stock screening endpoint."""

    stocks: list[StockResponse] = Field(description="List of screened stocks")
    total_count: int = Field(description="Total number of stocks returned")
    filters_applied: dict[str, Any] = Field(description="Filters that were applied")
    processing_time_ms: float | None = Field(
        None, description="Request processing time in milliseconds"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
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


class APIInfoResponse(BaseModel):
    """Response model for API information endpoint."""

    message: str = Field(description="API welcome message")
    version: str = Field(description="API version")
    docs_url: str = Field(description="API documentation URL")
    health_url: str = Field(description="Health check endpoint URL")
    endpoints: list[str] = Field(description="Available API endpoints")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "message": "DGI Toolkit API",
                "version": "1.0.0",
                "docs_url": "/docs",
                "health_url": "/healthz",
                "endpoints": ["/api/v1/screen", "/healthz", "/docs"],
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
