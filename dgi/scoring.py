from abc import ABC, abstractmethod

from dgi.models import CompanyData


class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, row: CompanyData) -> float:
        pass


class DefaultScoring(ScoringStrategy):
    def score(self, row: CompanyData) -> float:
        cagr_norm = min(max(row.dividend_cagr / 20.0, 0.0), 1.0)
        fcf_norm = min(max(row.fcf_yield / 20.0, 0.0), 1.0)
        payout_norm = min(max(row.payout / 100.0, 0.0), 1.0)
        composite = cagr_norm + fcf_norm - payout_norm
        composite = composite / 3.0
        result = max(0.0, min(composite, 1.0))
        return float(result)
