from dgi.scoring import DefaultScoring
from dgi.models.company import CompanyData


def test_defaultscoring_zero_values():
    company = CompanyData(
        symbol="ZERO",
        name="Zero",
        sector="Tech",
        industry="SW",
        dividend_yield=0.0,
        payout_ratio=0.0,
        dividend_growth_5y=0.0,
        fcf_yield=0.0,
    )
    score = DefaultScoring().score(company)
    assert score == 0.0  # Should clamp to 0
