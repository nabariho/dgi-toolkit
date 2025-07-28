"""Tests for filtering strategies."""

import unittest

import pandas as pd

from dgi.filtering import (
    BaseFilter,
    CompositeFilter,
    DefaultFilter,
    GrowthOnlyFilter,
    PayoutOnlyFilter,
    RankingFilter,
    SectorFilter,
    TopNFilter,
    YieldOnlyFilter,
)


class TestDefaultFilter(unittest.TestCase):
    """Tests for DefaultFilter implementation."""

    def test_default_filter_all_pass(self) -> None:
        """Test DefaultFilter when all rows pass filters."""
        filter_strategy = DefaultFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 3)
        pd.testing.assert_frame_equal(result, test_df)

    def test_default_filter_all_fail(self) -> None:
        """Test DefaultFilter when no rows pass filters."""
        filter_strategy = DefaultFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [1.0, 1.5, 1.8],
                "payout": [70.0, 80.0, 90.0],
                "dividend_cagr": [2.0, 3.0, 4.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)
        self.assertEqual(
            list(result.columns), ["dividend_yield", "payout", "dividend_cagr"]
        )

    def test_default_filter_partial_pass(self) -> None:
        """Test DefaultFilter when some rows pass filters."""
        filter_strategy = DefaultFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [1.0, 2.5, 3.0, 0.5],
                "payout": [30.0, 70.0, 40.0, 90.0],
                "dividend_cagr": [8.0, 3.0, 6.0, 2.0],
                "symbol": ["A", "B", "C", "D"],  # Extra column to verify it's preserved
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Only row 2 should pass all filters
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["dividend_yield"], 3.0)
        self.assertEqual(result.iloc[0]["payout"], 40.0)
        self.assertEqual(result.iloc[0]["dividend_cagr"], 6.0)
        self.assertEqual(result.iloc[0]["symbol"], "C")

    def test_default_filter_edge_values(self) -> None:
        """Test DefaultFilter with edge case values."""
        filter_strategy = DefaultFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.0, 2.0],  # Exactly at minimum
                "payout": [60.0, 60.0],  # Exactly at maximum
                "dividend_cagr": [5.0, 5.0],  # Exactly at minimum
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Both rows should pass (inclusive bounds)
        self.assertEqual(len(result), 2)

    def test_default_filter_empty_dataframe(self) -> None:
        """Test DefaultFilter with empty input DataFrame."""
        filter_strategy = DefaultFilter()

        test_df = pd.DataFrame(
            {"dividend_yield": [], "payout": [], "dividend_cagr": []}
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)
        self.assertEqual(
            list(result.columns), ["dividend_yield", "payout", "dividend_cagr"]
        )

    def test_default_filter_zero_thresholds(self) -> None:
        """Test DefaultFilter with zero thresholds."""
        filter_strategy = DefaultFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [0.0, 1.0, 2.0],
                "payout": [0.0, 50.0, 100.0],
                "dividend_cagr": [0.0, 5.0, 10.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=0.0, max_payout=100.0, min_cagr=0.0
        )

        # All rows should pass
        self.assertEqual(len(result), 3)

    def test_default_filter_missing_columns(self) -> None:
        """Test DefaultFilter with missing required columns."""
        filter_strategy = DefaultFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                # Missing dividend_cagr column
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return empty DataFrame with same structure
        self.assertEqual(len(result), 0)
        self.assertEqual(list(result.columns), ["dividend_yield", "payout"])


class TestYieldOnlyFilter(unittest.TestCase):
    """Tests for YieldOnlyFilter implementation."""

    def test_yield_only_filter_basic(self) -> None:
        """Test YieldOnlyFilter basic functionality."""
        filter_strategy = YieldOnlyFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [1.5, 2.0, 2.5, 3.0],
                "payout": [30.0, 40.0, 50.0, 60.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should only filter by yield, ignore other parameters
        self.assertEqual(len(result), 3)  # 2.0, 2.5, 3.0 pass
        self.assertTrue(all(result["dividend_yield"] >= 2.0))

    def test_yield_only_filter_empty_dataframe(self) -> None:
        """Test YieldOnlyFilter with empty DataFrame."""
        filter_strategy = YieldOnlyFilter()

        test_df = pd.DataFrame({"dividend_yield": []})

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)

    def test_yield_only_filter_missing_column(self) -> None:
        """Test YieldOnlyFilter with missing dividend_yield column."""
        filter_strategy = YieldOnlyFilter()

        test_df = pd.DataFrame(
            {
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [5.0, 6.0, 7.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return empty DataFrame
        self.assertEqual(len(result), 0)


class TestPayoutOnlyFilter(unittest.TestCase):
    """Tests for PayoutOnlyFilter implementation."""

    def test_payout_only_filter_basic(self) -> None:
        """Test PayoutOnlyFilter basic functionality."""
        filter_strategy = PayoutOnlyFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 50.0, 70.0],
                "dividend_cagr": [5.0, 6.0, 7.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should only filter by payout, ignore other parameters
        self.assertEqual(len(result), 2)  # 30.0, 50.0 pass
        self.assertTrue(all(result["payout"] <= 60.0))

    def test_payout_only_filter_empty_dataframe(self) -> None:
        """Test PayoutOnlyFilter with empty DataFrame."""
        filter_strategy = PayoutOnlyFilter()

        test_df = pd.DataFrame({"payout": []})

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)

    def test_payout_only_filter_missing_column(self) -> None:
        """Test PayoutOnlyFilter with missing payout column."""
        filter_strategy = PayoutOnlyFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "dividend_cagr": [5.0, 6.0, 7.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return empty DataFrame
        self.assertEqual(len(result), 0)


class TestGrowthOnlyFilter(unittest.TestCase):
    """Tests for GrowthOnlyFilter implementation."""

    def test_growth_only_filter_basic(self) -> None:
        """Test GrowthOnlyFilter basic functionality."""
        filter_strategy = GrowthOnlyFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [3.0, 5.0, 7.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should only filter by growth, ignore other parameters
        self.assertEqual(len(result), 2)  # 5.0, 7.0 pass
        self.assertTrue(all(result["dividend_cagr"] >= 5.0))

    def test_growth_only_filter_empty_dataframe(self) -> None:
        """Test GrowthOnlyFilter with empty DataFrame."""
        filter_strategy = GrowthOnlyFilter()

        test_df = pd.DataFrame({"dividend_cagr": []})

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)

    def test_growth_only_filter_missing_column(self) -> None:
        """Test GrowthOnlyFilter with missing dividend_cagr column."""
        filter_strategy = GrowthOnlyFilter()

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return empty DataFrame
        self.assertEqual(len(result), 0)


class TestSectorFilter(unittest.TestCase):
    """Tests for SectorFilter implementation."""

    def test_sector_filter_basic(self) -> None:
        """Test SectorFilter basic functionality."""
        filter_strategy = SectorFilter(["Technology", "Finance"])

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0, 2.8],
                "payout": [30.0, 40.0, 50.0, 35.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 5.5],
                "sector": ["Technology", "Finance", "Healthcare", "Technology"],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should only filter by sector, ignore other parameters
        self.assertEqual(len(result), 3)  # Technology, Finance, Technology
        self.assertTrue(all(result["sector"].isin(["Technology", "Finance"])))

    def test_sector_filter_empty_dataframe(self) -> None:
        """Test SectorFilter with empty DataFrame."""
        filter_strategy = SectorFilter(["Technology"])

        test_df = pd.DataFrame({"sector": []})

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)

    def test_sector_filter_missing_column(self) -> None:
        """Test SectorFilter with missing sector column."""
        filter_strategy = SectorFilter(["Technology"])

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [5.0, 6.0, 7.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return empty DataFrame
        self.assertEqual(len(result), 0)

    def test_sector_filter_no_matches(self) -> None:
        """Test SectorFilter when no sectors match."""
        filter_strategy = SectorFilter(["Technology"])

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [5.0, 6.0, 7.0],
                "sector": ["Finance", "Healthcare", "Consumer"],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return empty DataFrame
        self.assertEqual(len(result), 0)


class TestCompositeFilter(unittest.TestCase):
    """Tests for CompositeFilter implementation."""

    def test_composite_filter_basic(self) -> None:
        """Test CompositeFilter basic functionality."""
        filter_strategy = CompositeFilter(YieldOnlyFilter(), PayoutOnlyFilter())

        test_df = pd.DataFrame(
            {
                "dividend_yield": [1.5, 2.5, 3.0, 4.0],
                "payout": [30.0, 70.0, 50.0, 80.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should apply both filters: yield >= 2.0 AND payout <= 60.0
        # Only row 2 (index 2) passes both: yield=3.0 >= 2.0 and payout=50.0 <= 60.0
        self.assertEqual(len(result), 1)  # Only one row passes both filters
        self.assertTrue(all(result["dividend_yield"] >= 2.0))
        self.assertTrue(all(result["payout"] <= 60.0))

    def test_composite_filter_empty_dataframe(self) -> None:
        """Test CompositeFilter with empty DataFrame."""
        filter_strategy = CompositeFilter(DefaultFilter())

        test_df = pd.DataFrame(
            {"dividend_yield": [], "payout": [], "dividend_cagr": []}
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)

    def test_composite_filter_add_filter(self) -> None:
        """Test CompositeFilter add_filter method."""
        filter_strategy = CompositeFilter(DefaultFilter())
        filter_strategy.add_filter(TopNFilter(2))

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0, 5.0],
                "payout": [30.0, 40.0, 50.0, 60.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should apply DefaultFilter (all pass) then TopNFilter (limit to 2)
        self.assertEqual(len(result), 2)


class TestTopNFilter(unittest.TestCase):
    """Tests for TopNFilter implementation."""

    def test_top_n_filter_basic(self) -> None:
        """Test TopNFilter basic functionality."""
        filter_strategy = TopNFilter(2)

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0, 5.0],
                "payout": [30.0, 40.0, 50.0, 60.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return top 2 rows
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["dividend_yield"], 2.5)
        self.assertEqual(result.iloc[1]["dividend_yield"], 3.0)

    def test_top_n_filter_with_base_filter(self) -> None:
        """Test TopNFilter with base filter."""
        filter_strategy = TopNFilter(2, DefaultFilter())

        test_df = pd.DataFrame(
            {
                "dividend_yield": [1.5, 2.5, 3.0, 4.0],
                "payout": [30.0, 70.0, 50.0, 80.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should apply DefaultFilter first, then limit to top 2
        # Only rows 0 and 2 pass DefaultFilter (yield>=2.0, payout<=60.0, cagr>=5.0)
        # Row 0: yield=1.5 < 2.0 (fails)
        # Row 1: yield=2.5 >= 2.0, payout=70.0 > 60.0 (fails)
        # Row 2: yield=3.0 >= 2.0, payout=50.0 <= 60.0, cagr=7.0 >= 5.0 (passes)
        # Row 3: yield=4.0 >= 2.0, payout=80.0 > 60.0 (fails)
        # So only row 2 passes, and TopNFilter(2) returns it
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["dividend_yield"], 3.0)

    def test_top_n_filter_empty_dataframe(self) -> None:
        """Test TopNFilter with empty DataFrame."""
        filter_strategy = TopNFilter(2)

        test_df = pd.DataFrame(
            {"dividend_yield": [], "payout": [], "dividend_cagr": []}
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)

    def test_top_n_filter_n_larger_than_dataframe(self) -> None:
        """Test TopNFilter when n is larger than DataFrame size."""
        filter_strategy = TopNFilter(10)

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [5.0, 6.0, 7.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return all rows
        self.assertEqual(len(result), 3)


class TestRankingFilter(unittest.TestCase):
    """Tests for RankingFilter implementation."""

    def test_ranking_filter_basic(self) -> None:
        """Test RankingFilter basic functionality."""
        filter_strategy = RankingFilter(2, "dividend_yield", ascending=False)

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0, 5.0],
                "payout": [30.0, 40.0, 50.0, 60.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return top 2 rows sorted by dividend_yield descending
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["dividend_yield"], 5.0)
        self.assertEqual(result.iloc[1]["dividend_yield"], 4.0)

    def test_ranking_filter_ascending(self) -> None:
        """Test RankingFilter with ascending sort."""
        filter_strategy = RankingFilter(2, "dividend_yield", ascending=True)

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0, 5.0],
                "payout": [30.0, 40.0, 50.0, 60.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return top 2 rows sorted by dividend_yield ascending
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["dividend_yield"], 2.5)
        self.assertEqual(result.iloc[1]["dividend_yield"], 3.0)

    def test_ranking_filter_missing_column(self) -> None:
        """Test RankingFilter with missing sort column."""
        filter_strategy = RankingFilter(2, "missing_column", ascending=False)

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0, 5.0],
                "payout": [30.0, 40.0, 50.0, 60.0],
                "dividend_cagr": [5.0, 6.0, 7.0, 8.0],
            }
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should return top 2 rows without sorting
        self.assertEqual(len(result), 2)

    def test_ranking_filter_empty_dataframe(self) -> None:
        """Test RankingFilter with empty DataFrame."""
        filter_strategy = RankingFilter(2, "dividend_yield", ascending=False)

        test_df = pd.DataFrame(
            {"dividend_yield": [], "payout": [], "dividend_cagr": []}
        )

        result = filter_strategy.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        self.assertEqual(len(result), 0)


class TestFilterStrategyInterface(unittest.TestCase):
    """Tests for FilterStrategy interface."""

    def test_filter_strategy_is_abstract(self) -> None:
        """Test that BaseFilter cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseFilter()  # type: ignore

    def test_custom_filter_implementation(self) -> None:
        """Test custom filter strategy implementation."""

        class SectorFilter(BaseFilter):
            def __init__(self, allowed_sectors: list[str]) -> None:
                self.allowed_sectors = allowed_sectors

            def filter(
                self,
                df: pd.DataFrame,
                min_yield: float,
                max_payout: float,
                min_cagr: float,
            ) -> pd.DataFrame:
                # First apply base filters
                base_filtered = df[
                    (df["dividend_yield"] >= min_yield)
                    & (df["payout"] <= max_payout)
                    & (df["dividend_cagr"] >= min_cagr)
                ]
                # Then apply sector filter
                if "sector" in base_filtered.columns:
                    return base_filtered[
                        base_filtered["sector"].isin(self.allowed_sectors)
                    ]
                return base_filtered

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [6.0, 7.0, 8.0],
                "sector": ["Tech", "Finance", "Tech"],
            }
        )

        sector_filter = SectorFilter(["Tech"])
        result = sector_filter.filter(
            test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
        )

        # Should only return Tech sector stocks
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["sector"] == "Tech"))

    def test_composite_filter_implementation(self) -> None:
        """Test composite filter that combines multiple strategies."""

        class CompositeFilter(BaseFilter):
            def __init__(self, *filters: BaseFilter) -> None:
                self.filters = filters

            def filter(
                self,
                df: pd.DataFrame,
                min_yield: float,
                max_payout: float,
                min_cagr: float,
            ) -> pd.DataFrame:
                result = df
                for filter_strategy in self.filters:
                    result = filter_strategy.filter(
                        result, min_yield, max_payout, min_cagr
                    )
                return result

        class MinimumRowsFilter(BaseFilter):
            def filter(
                self,
                df: pd.DataFrame,
                min_yield: float,
                max_payout: float,
                min_cagr: float,
            ) -> pd.DataFrame:
                # Return at most 2 rows
                return df.head(2)

        test_df = pd.DataFrame(
            {
                "dividend_yield": [2.5, 3.0, 4.0],
                "payout": [30.0, 40.0, 50.0],
                "dividend_cagr": [6.0, 7.0, 8.0],
            }
        )

        composite = CompositeFilter(DefaultFilter(), MinimumRowsFilter())
        result = composite.filter(test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0)

        # Should apply both filters: all pass DefaultFilter, but limited to 2 rows
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
