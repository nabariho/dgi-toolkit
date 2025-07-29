"""API response schemas for DGI Toolkit.

This module defines comprehensive response schemas with detailed documentation,
examples, and field constraints for all API endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StockResponse(BaseModel):
    """Response model for individual stock data.

    Contains comprehensive information about a dividend growth stock including
    financial metrics, scoring, and classification data.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "JNJ",
                "name": "Johnson & Johnson",
                "sector": "Healthcare",
                "industry": "Drug Manufacturers",
                "dividend_yield": 0.025,
                "payout": 45.2,
                "dividend_cagr": 0.065,
                "fcf_yield": 4.8,
                "score": 0.82,
            }
        }
    )

    symbol: str = Field(
        description="Stock ticker symbol (1-5 alphanumeric characters)",
        min_length=1,
        max_length=5,
        pattern=r"^[A-Z0-9]+$",
        examples=["JNJ"],
    )
    name: str = Field(
        description="Company name",
        min_length=1,
        max_length=100,
        examples=["Johnson & Johnson"],
    )
    sector: str = Field(
        description="Business sector classification",
        min_length=1,
        max_length=50,
        examples=["Healthcare"],
    )
    industry: str = Field(
        description="Industry classification",
        min_length=1,
        max_length=50,
        examples=["Drug Manufacturers"],
    )
    dividend_yield: float = Field(
        description="Current dividend yield as decimal (e.g., 0.025 = 2.5%)",
        ge=0.0,
        le=1.0,
        examples=[0.025],
    )
    payout: float = Field(
        description="Dividend payout ratio as percentage (e.g., 45.2 = 45.2%)",
        ge=0.0,
        le=200.0,
        examples=[45.2],
    )
    dividend_cagr: float = Field(
        description="5-year dividend compound annual growth rate as decimal (e.g., 0.065 = 6.5%)",
        ge=-1.0,
        le=1.0,
        examples=[0.065],
    )
    fcf_yield: float = Field(
        description="Free cash flow yield as percentage (e.g., 4.8 = 4.8%)",
        ge=-100.0,
        le=100.0,
        examples=[4.8],
    )
    score: float = Field(
        description="Composite DGI score (0.0 to 1.0, higher is better)",
        ge=0.0,
        le=1.0,
        examples=[0.82],
    )


class FiltersApplied(BaseModel):
    """Model for screening filters applied to the request.

    Documents the exact filter parameters used in the screening process.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "min_yield": 0.02,
                "max_payout": 80.0,
                "min_cagr": 0.05,
                "top_n": 10,
            }
        }
    )

    min_yield: float = Field(
        description="Minimum dividend yield filter applied (as percentage, e.g., 50.0 for 50%)",
        ge=0.0,
        le=100.0,
        examples=[2.0],
    )
    max_payout: float = Field(
        description="Maximum payout ratio filter applied (as percentage, e.g., 80.0 for 80%)",
        ge=0.0,
        le=200.0,
        examples=[80.0],
    )
    min_cagr: float = Field(
        description="Minimum dividend CAGR filter applied (as percentage, e.g., 5.0 for 5%)",
        ge=-100.0,
        le=100.0,
        examples=[5.0],
    )
    top_n: int = Field(
        description="Maximum number of stocks returned", ge=1, le=1000, examples=[10]
    )


class ScreenResponse(BaseModel):
    """Response model for stock screening results.

    Contains the screened stocks, metadata about the screening process,
    and performance metrics.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stocks": [
                    {
                        "symbol": "JNJ",
                        "name": "Johnson & Johnson",
                        "sector": "Healthcare",
                        "industry": "Drug Manufacturers",
                        "dividend_yield": 0.025,
                        "payout": 45.2,
                        "dividend_cagr": 0.065,
                        "fcf_yield": 4.8,
                        "score": 0.82,
                    }
                ],
                "total_count": 1,
                "filters_applied": {
                    "min_yield": 2.0,
                    "max_payout": 80.0,
                    "min_cagr": 5.0,
                    "top_n": 10,
                },
                "processing_time_ms": 15.23,
            }
        }
    )

    stocks: list[StockResponse] = Field(
        description="List of stocks meeting the screening criteria, sorted by score (highest first)",
        min_length=0,
        max_length=1000,
    )
    total_count: int = Field(
        description="Total number of stocks returned", ge=0, examples=[1]
    )
    filters_applied: FiltersApplied = Field(
        description="Exact filter parameters used in the screening process"
    )
    processing_time_ms: float = Field(
        description="Time taken to process the screening request in milliseconds",
        ge=0.0,
        examples=[15.23],
    )


class ErrorDetail(BaseModel):
    """Detailed error information for API error responses.

    Provides comprehensive error details including error codes,
    messages, and additional context for debugging.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "min_yield",
                "message": "ensure this value is greater than 0",
                "type": "value_error.number.not_gt",
            }
        }
    )

    field: str | None = Field(
        description="Field name that caused the error (if applicable)",
        examples=["min_yield"],
    )
    message: str = Field(
        description="Human-readable error message",
        examples=["ensure this value is greater than 0"],
    )
    type: str = Field(
        description="Error type/code for programmatic handling",
        examples=["value_error.number.not_gt"],
    )


class ErrorResponse(BaseModel):
    """Standard error response model for all API endpoints.

    Provides consistent error response format across all endpoints
    with detailed error information and correlation tracking.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "status_code": 400,
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

    error: dict[str, Any] = Field(
        description="Error details including code, message, and additional context"
    )
    timestamp: datetime = Field(
        description="ISO 8601 timestamp when the error occurred",
        examples=["2024-01-15T10:30:00Z"],
    )
    correlation_id: str | None = Field(
        description="Unique correlation ID for tracking the request",
        examples=["req-12345"],
    )


class HealthResponse(BaseModel):
    """Health check response model.

    Provides comprehensive health status information including
    service status, dependencies, and performance metrics.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                "uptime_seconds": 3600,
                "dependencies": {
                    "database": "healthy",
                    "cache": "healthy",
                    "external_api": "healthy",
                },
                "metrics": {
                    "total_requests": 1500,
                    "average_response_time_ms": 25.5,
                    "error_rate": 0.001,
                },
            }
        }
    )

    status: str = Field(
        description="Overall health status (healthy, degraded, unhealthy)",
        examples=["healthy"],
    )
    timestamp: datetime = Field(
        description="ISO 8601 timestamp of the health check",
        examples=["2024-01-15T10:30:00Z"],
    )
    version: str = Field(description="API version", examples=["1.0.0"])
    uptime_seconds: float = Field(
        description="Service uptime in seconds", ge=0.0, examples=[3600.0]
    )
    dependencies: dict[str, str] = Field(
        description="Health status of external dependencies",
        examples=[
            {
                "database": "healthy",
                "cache": "healthy",
                "external_api": "healthy",
            }
        ],
    )
    metrics: dict[str, Any] = Field(
        description="Performance and operational metrics",
        examples=[
            {
                "total_requests": 1500,
                "average_response_time_ms": 25.5,
                "error_rate": 0.001,
            }
        ],
    )


class APIInfoResponse(BaseModel):
    """API information response model.

    Provides comprehensive information about the API including
    version, features, endpoints, and usage guidelines.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "DGI Toolkit API",
                "version": "1.0.0",
                "description": "Dividend Growth Investing stock screening and analysis API",
                "documentation_url": "https://api.dgi-toolkit.com/docs",
                "features": [
                    "Stock screening with DGI criteria",
                    "Real-time financial data",
                    "Portfolio analysis",
                    "Async processing",
                ],
                "rate_limits": {
                    "requests_per_minute": 100,
                    "burst_limit": 10,
                },
                "endpoints": {
                    "screening": "/api/v1/screen",
                    "async_screening": "/api/v1/screen/async",
                    "health": "/api/v1/health",
                    "metrics": "/api/v1/metrics",
                },
            }
        }
    )

    name: str = Field(description="API name", examples=["DGI Toolkit API"])
    version: str = Field(description="API version", examples=["1.0.0"])
    description: str = Field(
        description="Brief description of the API",
        examples=["Dividend Growth Investing stock screening and analysis API"],
    )
    documentation_url: str = Field(
        description="URL to API documentation",
        examples=["https://api.dgi-toolkit.com/docs"],
    )
    features: list[str] = Field(
        description="List of available features",
        examples=[
            "Stock screening with DGI criteria",
            "Real-time financial data",
            "Portfolio analysis",
            "Async processing",
        ],
    )
    rate_limits: dict[str, Any] = Field(
        description="Rate limiting information",
        examples=[
            {
                "requests_per_minute": 100,
                "burst_limit": 10,
            }
        ],
    )
    endpoints: dict[str, str] = Field(
        description="Available API endpoints",
        examples=[
            {
                "screening": "/api/v1/screen",
                "async_screening": "/api/v1/screen/async",
                "health": "/api/v1/health",
                "metrics": "/api/v1/metrics",
            }
        ],
    )


class JobStatusResponse(BaseModel):
    """Job status response model for async operations.

    Provides detailed information about background job status,
    progress, and results.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "progress": 0.5,
                "current_step": 3,
                "total_steps": 5,
                "step_description": "Calculating scores",
                "estimated_completion": "2024-01-15T10:35:00Z",
            }
        }
    )

    job_id: str = Field(
        description="Unique job identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: str = Field(
        description="Job status (pending, running, completed, failed, cancelled)",
        examples=["running"],
    )
    progress: float = Field(
        description="Job progress as percentage (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.5],
    )
    current_step: int = Field(description="Current processing step", ge=0, examples=[3])
    total_steps: int = Field(
        description="Total number of processing steps", ge=1, examples=[5]
    )
    step_description: str = Field(
        description="Description of current step", examples=["Calculating scores"]
    )
    estimated_completion: datetime | None = Field(
        description="Estimated completion time", examples=["2024-01-15T10:35:00Z"]
    )
    result: ScreenResponse | None = Field(
        description="Screening results (available when completed)", default=None
    )
    error_message: str | None = Field(
        description="Error message (if job failed)", default=None
    )
