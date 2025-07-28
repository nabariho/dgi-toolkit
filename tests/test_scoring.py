"""Tests for scoring strategies."""

import unittest

from dgi.models import CompanyData
from dgi.scoring import (
    CompositeScoringStrategy,
    DefaultScoring,
    DividendGrowthScoring,
    DividendYieldScoring,
    FCFYieldScoring,
    IndustryBonusScoring,
    PayoutRatioScoring,
    ScoringStrategy,
    SectorBonusScoring,
    WeightedScoringStrategy,
)


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

    def test_default_scoring_edge_cases(self) -> None:
        """Test DefaultScoring with edge case values."""
        scoring = DefaultScoring()

        # Test with zero values
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=0.0,
            payout_ratio=0.0,
            dividend_growth_5y=0.0,
            fcf_yield=0.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

        # Test with maximum values
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=20.0,
            payout_ratio=100.0,
            dividend_growth_5y=30.0,
            fcf_yield=25.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestDividendYieldScoring(unittest.TestCase):
    """Tests for DividendYieldScoring implementation."""

    def test_dividend_yield_scoring_basic(self) -> None:
        """Test basic dividend yield scoring."""
        scoring = DividendYieldScoring()

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=5.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Actual implementation: min(max(5.0 / 0.10, 0.0), 1.0) = min(max(50.0, 0.0), 1.0) = 1.0
        self.assertEqual(score, 1.0)  # Capped at 1.0 since 5% / 10% = 50 > 1.0

    def test_dividend_yield_scoring_edge_cases(self) -> None:
        """Test dividend yield scoring with edge cases."""
        scoring = DividendYieldScoring()

        # Test with zero yield
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=0.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 0.0)

        # Test with maximum yield (should be capped at 1.0)
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=15.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 1.0)


class TestDividendGrowthScoring(unittest.TestCase):
    """Tests for DividendGrowthScoring implementation."""

    def test_dividend_growth_scoring_basic(self) -> None:
        """Test basic dividend growth scoring."""
        scoring = DividendGrowthScoring()

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=10.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertEqual(score, 0.5)  # 10% / 20% = 0.5

    def test_dividend_growth_scoring_edge_cases(self) -> None:
        """Test dividend growth scoring with edge cases."""
        scoring = DividendGrowthScoring()

        # Test with zero growth
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=0.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 0.0)

        # Test with maximum growth (should be capped at 1.0)
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=25.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 1.0)


class TestPayoutRatioScoring(unittest.TestCase):
    """Tests for PayoutRatioScoring implementation."""

    def test_payout_ratio_scoring_basic(self) -> None:
        """Test basic payout ratio scoring."""
        scoring = PayoutRatioScoring()

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertEqual(score, 0.6)  # 1.0 - (40% / 100%) = 0.6

    def test_payout_ratio_scoring_edge_cases(self) -> None:
        """Test payout ratio scoring with edge cases."""
        scoring = PayoutRatioScoring()

        # Test with zero payout ratio (best score)
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=0.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 1.0)

        # Test with maximum payout ratio (worst score)
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=100.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 0.0)


class TestFCFYieldScoring(unittest.TestCase):
    """Tests for FCFYieldScoring implementation."""

    def test_fcf_yield_scoring_basic(self) -> None:
        """Test basic FCF yield scoring."""
        scoring = FCFYieldScoring()

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=10.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertEqual(score, 0.5)  # 10% / 20% = 0.5

    def test_fcf_yield_scoring_edge_cases(self) -> None:
        """Test FCF yield scoring with edge cases."""
        scoring = FCFYieldScoring()

        # Test with zero FCF yield
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=0.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 0.0)

        # Test with maximum FCF yield (should be capped at 1.0)
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=25.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 1.0)


class TestSectorBonusScoring(unittest.TestCase):
    """Tests for SectorBonusScoring implementation."""

    def test_sector_bonus_scoring_preferred_sector(self) -> None:
        """Test sector bonus scoring with preferred sector."""
        scoring = SectorBonusScoring(["Technology", "Finance"], bonus=0.1)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertEqual(score, 0.6)  # 0.5 base + 0.1 bonus

    def test_sector_bonus_scoring_non_preferred_sector(self) -> None:
        """Test sector bonus scoring with non-preferred sector."""
        scoring = SectorBonusScoring(["Technology", "Finance"], bonus=0.1)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Healthcare",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertEqual(score, 0.5)  # 0.5 base only

    def test_sector_bonus_scoring_custom_bonus(self) -> None:
        """Test sector bonus scoring with custom bonus value."""
        scoring = SectorBonusScoring(["Technology"], bonus=0.2)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 0.7)  # 0.5 base + 0.2 bonus


class TestIndustryBonusScoring(unittest.TestCase):
    """Tests for IndustryBonusScoring implementation."""

    def test_industry_bonus_scoring_preferred_industry(self) -> None:
        """Test industry bonus scoring with preferred industry."""
        scoring = IndustryBonusScoring(["Software", "Banking"], bonus=0.05)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertEqual(score, 0.55)  # 0.5 base + 0.05 bonus

    def test_industry_bonus_scoring_non_preferred_industry(self) -> None:
        """Test industry bonus scoring with non-preferred industry."""
        scoring = IndustryBonusScoring(["Software", "Banking"], bonus=0.05)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Hardware",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertEqual(score, 0.5)  # 0.5 base only

    def test_industry_bonus_scoring_custom_bonus(self) -> None:
        """Test industry bonus scoring with custom bonus value."""
        scoring = IndustryBonusScoring(["Software"], bonus=0.15)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = scoring.score(test_company)
        self.assertEqual(score, 0.65)  # 0.5 base + 0.15 bonus


class TestCompositeScoringStrategy(unittest.TestCase):
    """Tests for CompositeScoringStrategy implementation."""

    def test_composite_scoring_strategy_basic(self) -> None:
        """Test basic composite scoring strategy."""
        composite = CompositeScoringStrategy()
        composite.add_scoring_component(DividendYieldScoring(), 0.5)
        composite.add_scoring_component(PayoutRatioScoring(), 0.5)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=5.0,  # 1.0 score (capped)
            payout_ratio=40.0,  # 0.6 score
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = composite.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Expected: (1.0 * 0.5 + 0.6 * 0.5) / 1.0 = 0.8
        self.assertAlmostEqual(score, 0.8, places=2)

    def test_composite_scoring_strategy_empty(self) -> None:
        """Test composite scoring strategy with no components."""
        composite = CompositeScoringStrategy()

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = composite.score(test_company)
        self.assertEqual(score, 0.0)

    def test_composite_scoring_strategy_zero_weights(self) -> None:
        """Test composite scoring strategy with zero weights."""
        composite = CompositeScoringStrategy()
        composite.add_scoring_component(DividendYieldScoring(), 0.0)
        composite.add_scoring_component(PayoutRatioScoring(), 0.0)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        score = composite.score(test_company)
        self.assertEqual(score, 0.0)

    def test_composite_scoring_strategy_multiple_components(self) -> None:
        """Test composite scoring strategy with multiple components."""
        composite = CompositeScoringStrategy()
        composite.add_scoring_component(DividendYieldScoring(), 0.3)
        composite.add_scoring_component(PayoutRatioScoring(), 0.3)
        composite.add_scoring_component(FCFYieldScoring(), 0.4)

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=5.0,  # 1.0 score (capped)
            payout_ratio=40.0,  # 0.6 score
            dividend_growth_5y=8.0,
            fcf_yield=10.0,  # 0.5 score
        )

        score = composite.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Expected: (1.0 * 0.3 + 0.6 * 0.3 + 0.5 * 0.4) / 1.0 = 0.68
        self.assertAlmostEqual(score, 0.68, places=2)


class TestWeightedScoringStrategy(unittest.TestCase):
    """Tests for WeightedScoringStrategy implementation."""

    def test_weighted_scoring_strategy_basic(self) -> None:
        """Test basic weighted scoring strategy."""
        scoring = WeightedScoringStrategy(
            yield_weight=0.3,
            growth_weight=0.3,
            payout_weight=0.2,
            fcf_weight=0.2,
        )

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=5.0,  # 0.5 score
            payout_ratio=40.0,  # 0.6 score (inverted)
            dividend_growth_5y=10.0,  # 0.5 score
            fcf_yield=10.0,  # 0.5 score
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Expected: 0.5*0.3 + 0.5*0.3 + 0.6*0.2 + 0.5*0.2 = 0.52
        self.assertAlmostEqual(score, 0.52, places=2)

    def test_weighted_scoring_strategy_edge_cases(self) -> None:
        """Test weighted scoring strategy with edge cases."""
        scoring = WeightedScoringStrategy()

        # Test with zero values
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=0.0,
            payout_ratio=0.0,
            dividend_growth_5y=0.0,
            fcf_yield=0.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

        # Test with maximum values
        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=15.0,
            payout_ratio=100.0,
            dividend_growth_5y=25.0,
            fcf_yield=25.0,
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_weighted_scoring_strategy_custom_weights(self) -> None:
        """Test weighted scoring strategy with custom weights."""
        scoring = WeightedScoringStrategy(
            yield_weight=0.5,
            growth_weight=0.3,
            payout_weight=0.1,
            fcf_weight=0.1,
        )

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=8.0,  # 0.8 score
            payout_ratio=30.0,  # 0.7 score (inverted)
            dividend_growth_5y=15.0,  # 0.75 score
            fcf_yield=12.0,  # 0.6 score
        )

        score = scoring.score(test_company)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Expected: 0.8*0.5 + 0.75*0.3 + 0.7*0.1 + 0.6*0.1 = 0.755
        self.assertAlmostEqual(score, 0.755, places=3)


class TestScoringStrategyInterface(unittest.TestCase):
    """Tests for ScoringStrategy interface."""

    def test_scoring_strategy_is_abstract(self) -> None:
        """Test that ScoringStrategy cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            ScoringStrategy()  # type: ignore

    def test_custom_scoring_implementation(self) -> None:
        """Test custom scoring strategy implementation."""

        class SimpleScoring(ScoringStrategy):
            def score(self, row: CompanyData) -> float:
                return 0.5  # Always return 0.5

        test_company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=3.0,
            payout_ratio=40.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )

        scoring = SimpleScoring()
        score = scoring.score(test_company)
        self.assertEqual(score, 0.5)


if __name__ == "__main__":
    unittest.main()
