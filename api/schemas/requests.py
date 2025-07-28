"""Request schemas for DGI Toolkit API."""

from pydantic import BaseModel, Field, validator


class ScreenRequest(BaseModel):
    """Request model for stock screening endpoint."""

    min_yield: float = Field(
        default=0.02,
        ge=0.0,
        le=100.0,
        description="Minimum dividend yield (as decimal, e.g., 0.02 for 2%)",
    )
    max_payout: float = Field(
        default=80.0,
        ge=0.0,
        le=200.0,
        description="Maximum payout ratio (as percentage, e.g., 80.0 for 80%)",
    )
    min_cagr: float = Field(
        default=0.05,
        ge=-100.0,
        le=100.0,
        description="Minimum 5-year dividend CAGR (as decimal, e.g., 0.05 for 5%)",
    )
    top_n: int = Field(
        default=10, ge=1, le=100, description="Number of top stocks to return"
    )

    @validator("min_yield")
    def validate_min_yield(cls, v: float) -> float:
        """Validate minimum dividend yield."""
        if v < 0:
            raise ValueError("min_yield must be non-negative")
        if v > 100:
            raise ValueError("min_yield cannot exceed 100%")
        return v

    @validator("max_payout")
    def validate_max_payout(cls, v: float) -> float:
        """Validate maximum payout ratio."""
        if v < 0:
            raise ValueError("max_payout must be non-negative")
        if v > 200:
            raise ValueError("max_payout cannot exceed 200%")
        return v

    @validator("min_cagr")
    def validate_min_cagr(cls, v: float) -> float:
        """Validate minimum CAGR."""
        if v < -100:
            raise ValueError("min_cagr cannot be less than -100%")
        if v > 100:
            raise ValueError("min_cagr cannot exceed 100%")
        return v

    @validator("top_n")
    def validate_top_n(cls, v: int) -> int:
        """Validate top_n parameter."""
        if v < 1:
            raise ValueError("top_n must be at least 1")
        if v > 100:
            raise ValueError("top_n cannot exceed 100")
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "min_yield": 0.02,
                "max_payout": 80.0,
                "min_cagr": 0.05,
                "top_n": 10,
            }
        }


class HealthCheckRequest(BaseModel):
    """Request model for health check endpoint (for future extensibility)."""

    include_details: bool = Field(
        default=False, description="Include detailed health information"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {"example": {"include_details": False}}
