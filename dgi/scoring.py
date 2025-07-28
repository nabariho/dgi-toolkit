from abc import ABC, abstractmethod
from typing import Protocol

from dgi.models import CompanyData


class ScoringStrategy(ABC):
    """Base interface for all scoring strategies."""

    @abstractmethod
    def score(self, row: CompanyData) -> float:
        """Calculate score for a company."""


class DividendScoring(Protocol):
    """Protocol for dividend-based scoring."""

    def score_dividend_yield(self, row: CompanyData) -> float:
        """Score based on dividend yield."""
        ...

    def score_dividend_growth(self, row: CompanyData) -> float:
        """Score based on dividend growth."""
        ...


class FinancialHealthScoring(Protocol):
    """Protocol for financial health scoring."""

    def score_payout_ratio(self, row: CompanyData) -> float:
        """Score based on payout ratio."""
        ...

    def score_fcf_yield(self, row: CompanyData) -> float:
        """Score based on free cash flow yield."""
        ...


class SectorScoring(Protocol):
    """Protocol for sector-based scoring."""

    def score_sector(self, row: CompanyData) -> float:
        """Score based on sector."""
        ...

    def score_industry(self, row: CompanyData) -> float:
        """Score based on industry."""
        ...


class CompositeScoring(Protocol):
    """Protocol for composite scoring."""

    def add_scoring_component(self, scorer: ScoringStrategy, weight: float) -> None:
        """Add a scoring component with weight."""
        ...


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


# Specific scoring implementations that implement only the interfaces they need


class DividendYieldScoring:
    """Implementation of dividend yield scoring only."""

    def score_dividend_yield(self, row: CompanyData) -> float:
        """Score based on dividend yield."""
        return min(max(row.dividend_yield / 0.10, 0.0), 1.0)  # Normalize to 10% max


class DividendGrowthScoring:
    """Implementation of dividend growth scoring only."""

    def score_dividend_growth(self, row: CompanyData) -> float:
        """Score based on dividend growth."""
        return min(max(row.dividend_growth_5y / 20.0, 0.0), 1.0)  # Normalize to 20% max


class PayoutRatioScoring:
    """Implementation of payout ratio scoring only."""

    def score_payout_ratio(self, row: CompanyData) -> float:
        """Score based on payout ratio (lower is better)."""
        # Invert payout ratio so lower values get higher scores
        payout_score = 1.0 - min(max(row.payout_ratio / 100.0, 0.0), 1.0)
        return payout_score


class FCFYieldScoring:
    """Implementation of FCF yield scoring only."""

    def score_fcf_yield(self, row: CompanyData) -> float:
        """Score based on free cash flow yield."""
        return min(max(row.fcf_yield / 20.0, 0.0), 1.0)  # Normalize to 20% max


class SectorBonusScoring:
    """Implementation of sector bonus scoring only."""

    def __init__(self, preferred_sectors: list[str], bonus: float = 0.1):
        self.preferred_sectors = preferred_sectors
        self.bonus = bonus

    def score_sector(self, row: CompanyData) -> float:
        """Score based on sector."""
        return self.bonus if row.sector in self.preferred_sectors else 0.0


class IndustryBonusScoring:
    """Implementation of industry bonus scoring only."""

    def __init__(self, preferred_industries: list[str], bonus: float = 0.05):
        self.preferred_industries = preferred_industries
        self.bonus = bonus

    def score_industry(self, row: CompanyData) -> float:
        """Score based on industry."""
        return self.bonus if row.industry in self.preferred_industries else 0.0


class CompositeScoringStrategy(ScoringStrategy):
    """Composite scoring strategy that combines multiple scoring components."""

    def __init__(self):
        self.components: list[tuple[ScoringStrategy, float]] = []

    def add_scoring_component(self, scorer: ScoringStrategy, weight: float) -> None:
        """Add a scoring component with weight."""
        self.components.append((scorer, weight))

    def score(self, row: CompanyData) -> float:
        """Calculate composite score from all components."""
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
