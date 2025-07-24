"""Edge case tests for the screener module."""

import unittest
from unittest.mock import Mock

import pandas as pd

from dgi.screener import Screener


class TestScreenerEdgeCases(unittest.TestCase):
    """Test edge cases for Screener class."""

    def test_screener_empty_dataframe(self) -> None:
        """Test screener with empty DataFrame."""
        mock_repo = Mock()
        mock_repo.get_data.return_value = pd.DataFrame()

        screener = Screener(mock_repo)
        result = screener.screen()

        self.assertTrue(result.empty)

    def test_screener_no_filters_applied(self) -> None:
        """Test screener with no filters."""
        test_data = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT"],
                "dividend_yield": [1.5, 2.0],
                "payout": [25.0, 30.0],
                "dividend_cagr": [5.0, 7.0],
            }
        )

        mock_repo = Mock()
        mock_repo.get_data.return_value = test_data

        screener = Screener(mock_repo)
        result = screener.screen()

        self.assertEqual(len(result), 2)

    def test_screener_all_filtered_out(self) -> None:
        """Test screener when all stocks are filtered out."""
        test_data = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT"],
                "dividend_yield": [0.5, 0.8],  # Below threshold
                "payout": [90.0, 95.0],  # Above threshold
                "dividend_cagr": [1.0, 2.0],  # Below threshold
            }
        )

        mock_repo = Mock()
        mock_repo.get_data.return_value = test_data

        screener = Screener(mock_repo)
        result = screener.screen(min_yield=2.0, max_payout=60.0, min_cagr=5.0)

        self.assertTrue(result.empty)

    def test_screener_partial_filtering(self) -> None:
        """Test screener with partial filtering."""
        test_data = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT", "GOOGL"],
                "dividend_yield": [1.5, 2.5, 0.0],
                "payout": [25.0, 30.0, 0.0],
                "dividend_cagr": [5.0, 7.0, 0.0],
            }
        )

        mock_repo = Mock()
        mock_repo.get_data.return_value = test_data

        screener = Screener(mock_repo)
        result = screener.screen(min_yield=2.0, max_payout=60.0, min_cagr=5.0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["symbol"], "MSFT")

    def test_screener_with_missing_columns(self) -> None:
        """Test screener with missing required columns."""
        test_data = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT"],
                "dividend_yield": [1.5, 2.0],
                # Missing payout and dividend_cagr columns
            }
        )

        mock_repo = Mock()
        mock_repo.get_data.return_value = test_data

        screener = Screener(mock_repo)

        # This should handle missing columns gracefully
        with self.assertRaises((KeyError, AttributeError)):
            screener.screen()


if __name__ == "__main__":
    unittest.main()
