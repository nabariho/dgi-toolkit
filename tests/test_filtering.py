"""Tests for filtering strategies."""

import unittest
import pandas as pd
from dgi.filtering import FilterStrategy, DefaultFilter


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


class TestFilterStrategyInterface(unittest.TestCase):
    """Tests for FilterStrategy interface."""

    def test_filter_strategy_is_abstract(self) -> None:
        """Test that FilterStrategy cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            FilterStrategy()  # type: ignore

    def test_custom_filter_implementation(self) -> None:
        """Test custom filter strategy implementation."""

        class SectorFilter(FilterStrategy):
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

        class CompositeFilter(FilterStrategy):
            def __init__(self, *filters: FilterStrategy) -> None:
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

        class MinimumRowsFilter(FilterStrategy):
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
