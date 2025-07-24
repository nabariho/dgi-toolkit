"""Tests for CLI helper functions."""

import contextlib
import unittest

import pandas as pd

from dgi.cli_helpers import render_screen_table


class TestCliHelpers(unittest.TestCase):
    """Tests for CLI helper functions."""

    def test_render_screen_table_basic(self) -> None:
        """Test basic screen table rendering."""
        test_df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "company_name": ["Apple Inc"],
                "dividend_yield": [1.5],
                "payout": [25.0],
                "dividend_cagr": [5.0],
                "score": [8.5],
            }
        )

        # This should not raise an exception
        with contextlib.suppress(ImportError):
            render_screen_table(test_df)


if __name__ == "__main__":
    unittest.main()
