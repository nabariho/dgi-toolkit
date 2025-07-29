"""Scoring configuration for DGI Toolkit.

This module contains all configurable parameters for the scoring algorithms,
extracting magic numbers and hardcoded values into a centralized configuration
system that can be easily modified and validated.
"""

import os

from pydantic import BaseModel, ConfigDict, Field


class ScoringWeights(BaseModel):
    """Configuration for scoring algorithm weights."""

    model_config = ConfigDict(frozen=True)

    # Yield scoring weights
    yield_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Weight multiplier for dividend yield score",
    )

    # Growth scoring weights
    growth_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=10.0,
        description="Weight multiplier for dividend growth score",
    )

    # Payout penalty weights
    payout_penalty_weight: float = Field(
        default=-0.1,
        le=0.0,
        ge=-10.0,
        description="Weight multiplier for payout ratio penalty (negative)",
    )

    # Payout threshold for penalty calculation
    payout_penalty_threshold: float = Field(
        default=60.0,
        ge=0.0,
        le=200.0,
        description="Payout ratio threshold above which penalty is applied",
    )

    # FCF yield weight (for future use)
    fcf_yield_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=10.0,
        description="Weight multiplier for free cash flow yield score",
    )

    # Sector bonus weights
    sector_bonus: float = Field(
        default=0.1, ge=0.0, le=5.0, description="Bonus score for preferred sectors"
    )

    # Industry bonus weights
    industry_bonus: float = Field(
        default=0.05, ge=0.0, le=5.0, description="Bonus score for preferred industries"
    )


class ScoringThresholds(BaseModel):
    """Configuration for scoring thresholds and limits."""

    model_config = ConfigDict(frozen=True)

    # Minimum acceptable scores
    min_total_score: float = Field(
        default=0.0, ge=-100.0, le=100.0, description="Minimum acceptable total score"
    )

    # Maximum acceptable scores
    max_total_score: float = Field(
        default=100.0, ge=0.0, le=1000.0, description="Maximum acceptable total score"
    )

    # Score normalization
    score_normalization_factor: float = Field(
        default=1.0, ge=0.1, le=10.0, description="Factor for normalizing final scores"
    )


class ScoringConfig(BaseModel):
    """Complete scoring configuration."""

    model_config = ConfigDict(frozen=True)

    # Scoring weights
    weights: ScoringWeights = Field(
        default_factory=ScoringWeights, description="Scoring algorithm weights"
    )

    # Scoring thresholds
    thresholds: ScoringThresholds = Field(
        default_factory=ScoringThresholds, description="Scoring thresholds and limits"
    )

    # Preferred sectors (for bonus scoring)
    preferred_sectors: list[str] = Field(
        default=[
            "Consumer Defensive",
            "Healthcare",
            "Utilities",
            "Real Estate",
            "Consumer Cyclical",
        ],
        description="Sectors that receive bonus points",
    )

    # Preferred industries (for bonus scoring)
    preferred_industries: list[str] = Field(
        default=[
            "Drug Manufacturers",
            "Utilities - Regulated Electric",
            "REIT - Retail",
            "REIT - Office",
            "Beverages - Non-Alcoholic",
        ],
        description="Industries that receive bonus points",
    )

    # Penalty sectors (for negative scoring)
    penalty_sectors: list[str] = Field(
        default=["Energy", "Basic Materials"],
        description="Sectors that receive penalty points",
    )

    # Penalty industries (for negative scoring)
    penalty_industries: list[str] = Field(
        default=["Oil & Gas E&P", "Oil & Gas Integrated", "Oil & Gas Midstream"],
        description="Industries that receive penalty points",
    )


def load_scoring_config_from_env() -> ScoringConfig:
    """Load scoring configuration from environment variables."""

    # Load weights from environment
    weights = ScoringWeights(
        yield_weight=float(os.getenv("DGI_YIELD_WEIGHT", "1.0")),
        growth_weight=float(os.getenv("DGI_GROWTH_WEIGHT", "0.5")),
        payout_penalty_weight=float(os.getenv("DGI_PAYOUT_PENALTY_WEIGHT", "-0.1")),
        payout_penalty_threshold=float(
            os.getenv("DGI_PAYOUT_PENALTY_THRESHOLD", "60.0")
        ),
        fcf_yield_weight=float(os.getenv("DGI_FCF_YIELD_WEIGHT", "0.3")),
        sector_bonus=float(os.getenv("DGI_SECTOR_BONUS", "0.1")),
        industry_bonus=float(os.getenv("DGI_INDUSTRY_BONUS", "0.05")),
    )

    # Load thresholds from environment
    thresholds = ScoringThresholds(
        min_total_score=float(os.getenv("DGI_MIN_TOTAL_SCORE", "0.0")),
        max_total_score=float(os.getenv("DGI_MAX_TOTAL_SCORE", "100.0")),
        score_normalization_factor=float(
            os.getenv("DGI_SCORE_NORMALIZATION_FACTOR", "1.0")
        ),
    )

    # Load preferred sectors and industries from environment
    preferred_sectors_str = os.getenv("DGI_PREFERRED_SECTORS", "")
    preferred_sectors = (
        [s.strip() for s in preferred_sectors_str.split(",") if s.strip()]
        if preferred_sectors_str
        else [
            "Consumer Defensive",
            "Healthcare",
            "Utilities",
            "Real Estate",
            "Consumer Cyclical",
        ]
    )

    preferred_industries_str = os.getenv("DGI_PREFERRED_INDUSTRIES", "")
    preferred_industries = (
        [i.strip() for i in preferred_industries_str.split(",") if i.strip()]
        if preferred_industries_str
        else [
            "Drug Manufacturers",
            "Utilities - Regulated Electric",
            "REIT - Retail",
            "REIT - Office",
            "Beverages - Non-Alcoholic",
        ]
    )

    penalty_sectors_str = os.getenv("DGI_PENALTY_SECTORS", "")
    penalty_sectors = (
        [s.strip() for s in penalty_sectors_str.split(",") if s.strip()]
        if penalty_sectors_str
        else ["Energy", "Basic Materials"]
    )

    penalty_industries_str = os.getenv("DGI_PENALTY_INDUSTRIES", "")
    penalty_industries = (
        [i.strip() for i in penalty_industries_str.split(",") if i.strip()]
        if penalty_industries_str
        else ["Oil & Gas E&P", "Oil & Gas Integrated", "Oil & Gas Midstream"]
    )

    return ScoringConfig(
        weights=weights,
        thresholds=thresholds,
        preferred_sectors=preferred_sectors,
        preferred_industries=preferred_industries,
        penalty_sectors=penalty_sectors,
        penalty_industries=penalty_industries,
    )


# Global scoring configuration instance
_scoring_config: ScoringConfig | None = None


def get_scoring_config() -> ScoringConfig:
    """Get the global scoring configuration instance."""
    global _scoring_config
    if _scoring_config is None:
        _scoring_config = load_scoring_config_from_env()
    return _scoring_config


def reset_scoring_config() -> None:
    """Reset the global scoring configuration instance (useful for testing)."""
    global _scoring_config
    _scoring_config = None
