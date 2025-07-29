"""Request schemas for DGI Toolkit API.

This module contains Pydantic models for API request validation with comprehensive
documentation, field constraints, and examples for all endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field


class ScreenRequest(BaseModel):
    """Request model for stock screening operations.

    This model validates and documents all parameters for the stock screening endpoint.
    All parameters have comprehensive validation rules and clear documentation.
    """

    min_yield: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Minimum dividend yield as a decimal (e.g., 0.02 for 2%)",
        json_schema_extra={"example": 0.025},
        title="Minimum Dividend Yield",
    )

    max_payout: float = Field(
        default=80.0,
        ge=0.0,
        le=200.0,
        description="Maximum payout ratio as a percentage (e.g., 80.0 for 80%)",
        json_schema_extra={"example": 75.0},
        title="Maximum Payout Ratio",
    )

    min_cagr: float = Field(
        default=0.05,
        ge=-100.0,
        le=100.0,
        description="Minimum 5-year dividend compound annual growth rate as a decimal (e.g., 0.05 for 5%)",
        json_schema_extra={"example": 0.08},
        title="Minimum Dividend CAGR",
    )

    top_n: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of top stocks to return in the results",
        json_schema_extra={"example": 15},
        title="Top N Results",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "min_yield": 0.025,
                "max_payout": 75.0,
                "min_cagr": 0.08,
                "top_n": 15,
            },
            "description": """
            Stock screening request with DGI (Dividend Growth Investing) criteria.

            This request filters stocks based on:
            - **Dividend Yield**: Minimum yield for income generation
            - **Payout Ratio**: Maximum ratio to ensure dividend sustainability
            - **Dividend Growth**: Minimum 5-year CAGR for growth potential
            - **Top N**: Number of best stocks to return

            All parameters have validation rules to ensure reasonable values.
            """,
        }
    )


class AsyncScreenRequest(ScreenRequest):
    """Request model for asynchronous stock screening operations.

    Extends the base screening request with additional parameters for background processing.
    """

    priority: str = Field(
        default="normal",
        description="Job priority level for background processing",
        json_schema_extra={"example": "high"},
        title="Job Priority",
        pattern=r"^(low|normal|high|urgent)$",
    )

    user_id: str | None = Field(
        default=None,
        description="User ID for job tracking and monitoring",
        json_schema_extra={"example": "user123"},
        title="User ID",
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "min_yield": 0.025,
                "max_payout": 75.0,
                "min_cagr": 0.08,
                "top_n": 15,
                "priority": "high",
                "user_id": "user123",
            },
            "description": """
            Asynchronous stock screening request with background processing.

            This request submits a screening job for background processing with:
            - All standard DGI screening criteria
            - Job priority for queue management
            - User ID for job tracking

            The job will be processed asynchronously and results can be retrieved later.
            """,
        }
    )


class JobStatusRequest(BaseModel):
    """Request model for job status queries.

    This model validates job ID parameters for status checking endpoints.
    """

    job_id: str = Field(
        description="Unique job identifier (UUID format)",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
        title="Job ID",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
            },
            "description": """
            Job status request for checking background processing status.

            This request queries the status of a previously submitted async job.
            The job ID must be a valid UUID format.
            """,
        }
    )


class JobListRequest(BaseModel):
    """Request model for job listing queries.

    This model validates parameters for listing background jobs.
    """

    status: str | None = Field(
        default=None,
        description="Filter jobs by status",
        json_schema_extra={"example": "completed"},
        title="Job Status Filter",
        pattern=r"^(pending|running|completed|failed|cancelled)$",
    )

    user_id: str | None = Field(
        default=None,
        description="Filter jobs by user ID",
        json_schema_extra={"example": "user123"},
        title="User ID Filter",
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of jobs to return",
        json_schema_extra={"example": 25},
        title="Result Limit",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "completed",
                "user_id": "user123",
                "limit": 25,
            },
            "description": """
            Job listing request for retrieving background job information.

            This request lists jobs with optional filtering by:
            - Job status (pending, running, completed, failed, cancelled)
            - User ID for user-specific jobs
            - Limit for result pagination

            Jobs are sorted by creation time (newest first).
            """,
        }
    )


class CacheStatsRequest(BaseModel):
    """Request model for cache statistics queries.

    This model validates parameters for cache monitoring endpoints.
    """

    include_details: bool = Field(
        default=False,
        description="Include detailed cache statistics",
        json_schema_extra={"example": True},
        title="Include Details",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "include_details": True,
            },
            "description": """
            Cache statistics request for monitoring cache performance.

            This request retrieves cache performance metrics including:
            - Hit/miss rates
            - Cache size and memory usage
            - Performance statistics

            Optional detailed statistics can be included for debugging.
            """,
        }
    )
