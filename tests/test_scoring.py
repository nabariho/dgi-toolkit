"""Tests for scoring strategies."""

import unittest

from dgi.models import CompanyData
from dgi.scoring import DefaultScoring


class TestDefaultScoring(unittest.TestCase):
    """Tests for DefaultScoring implementation."""

    def test_default_scoring_basic(self) -> None:
        """Test basic scoring functionality."""
        scoring = DefaultScoring()

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",  # Use 'name' not 'company_name'
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,  # Use 'payout_ratio' not 'payout'
            dividend_growth_5y=8.0,  # Use 'dividend_growth_5y' not 'dividend_cagr'
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
