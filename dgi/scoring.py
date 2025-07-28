"""Scoring strategies for DGI Toolkit.

This module implements the Strategy pattern for different scoring approaches
used in stock screening. All scoring strategies inherit from ScoringStrategy
and can be composed together for complex scoring logic.
"""

from abc import ABC, abstractmethod

from dgi.models import CompanyData


class ScoringStrategy(ABC):
    """Abstract base class for all scoring strategies."""

    @abstractmethod
    def score(self, row: CompanyData) -> float:
        """Calculate score for a company."""


class DefaultScoring(ScoringStrategy):
    """Default DGI scoring strategy."""

    def score(self, row: CompanyData) -> float:
        """Calculate composite DGI score."""
        cagr_norm = min(max(row.dividend_cagr / 20.0, 0.0), 1.0)
        fcf_norm = min(max(row.fcf_yield / 20.0, 0.0), 1.0)
        payout_norm = min(max(row.payout / 100.0, 0.0), 1.0)
        composite = cagr_norm + fcf_norm - payout_norm
        composite = composite / 3.0
        result = max(0.0, min(composite, 1.0))
        return float(result)


class DividendYieldScoring(ScoringStrategy):
    """Scoring strategy based on dividend yield."""

    def score(self, row: CompanyData) -> float:
        """Score based on dividend yield."""
        return min(max(row.dividend_yield / 0.10, 0.0), 1.0)  # Normalize to 10% max


class DividendGrowthScoring(ScoringStrategy):
    """Scoring strategy based on dividend growth."""

    def score(self, row: CompanyData) -> float:
        """Score based on dividend growth."""
        return min(max(row.dividend_growth_5y / 20.0, 0.0), 1.0)  # Normalize to 20% max


class PayoutRatioScoring(ScoringStrategy):
    """Scoring strategy based on payout ratio."""

    def score(self, row: CompanyData) -> float:
        """Score based on payout ratio (lower is better)."""
        # Invert payout ratio so lower values get higher scores
        payout_score = 1.0 - min(max(row.payout_ratio / 100.0, 0.0), 1.0)
        return payout_score


class FCFYieldScoring(ScoringStrategy):
    """Scoring strategy based on free cash flow yield."""

    def score(self, row: CompanyData) -> float:
        """Score based on free cash flow yield."""
        return min(max(row.fcf_yield / 20.0, 0.0), 1.0)  # Normalize to 20% max


class SectorBonusScoring(ScoringStrategy):
    """Scoring strategy that adds bonus for preferred sectors."""

    def __init__(self, preferred_sectors: list[str], bonus: float = 0.1):
        self.preferred_sectors = preferred_sectors
        self.bonus = bonus

    def score(self, row: CompanyData) -> float:
        """Score based on sector with bonus for preferred sectors."""
        base_score = 0.5  # Base score for all companies
        if row.sector in self.preferred_sectors:
            return base_score + self.bonus
        return base_score


class IndustryBonusScoring(ScoringStrategy):
    """Scoring strategy that adds bonus for preferred industries."""

    def __init__(self, preferred_industries: list[str], bonus: float = 0.05):
        self.preferred_industries = preferred_industries
        self.bonus = bonus

    def score(self, row: CompanyData) -> float:
        """Score based on industry with bonus for preferred industries."""
        base_score = 0.5  # Base score for all companies
        if row.industry in self.preferred_industries:
            return base_score + self.bonus
        return base_score


class CompositeScoringStrategy(ScoringStrategy):
    """Composite scoring strategy that combines multiple scoring components."""

    def __init__(self) -> None:
        self.components: list[tuple[ScoringStrategy, float]] = []

    def add_scoring_component(self, scorer: ScoringStrategy, weight: float) -> None:
        """Add a scoring component with weight."""
        self.components.append((scorer, weight))

    def score(self, row: CompanyData) -> float:
        """Calculate weighted composite score."""
        if not self.components:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for scorer, weight in self.components:
            component_score = scorer.score(row)
            total_score += component_score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight


class WeightedScoringStrategy(ScoringStrategy):
    """Scoring strategy that applies configurable weights to different factors."""

    def __init__(
        self,
        yield_weight: float = 0.3,
        growth_weight: float = 0.3,
        payout_weight: float = 0.2,
        fcf_weight: float = 0.2,
    ):
        self.yield_weight = yield_weight
        self.growth_weight = growth_weight
        self.payout_weight = payout_weight
        self.fcf_weight = fcf_weight

    def score(self, row: CompanyData) -> float:
        """Calculate weighted score based on multiple factors."""
        # Calculate individual component scores
        yield_score = min(max(row.dividend_yield / 10.0, 0.0), 1.0)
        growth_score = min(max(row.dividend_growth_5y / 20.0, 0.0), 1.0)
        payout_score = 1.0 - min(max(row.payout_ratio / 100.0, 0.0), 1.0)  # Inverted
        fcf_score = min(max(row.fcf_yield / 20.0, 0.0), 1.0)

        # Calculate weighted composite score
        composite_score = (
            yield_score * self.yield_weight
            + growth_score * self.growth_weight
            + payout_score * self.payout_weight
            + fcf_score * self.fcf_weight
        )

        return max(0.0, min(composite_score, 1.0))
