"""Tests for scoring strategies."""

import unittest
import pandas as pd
from dgi.scoring import DefaultScoring


class TestDefaultScoring(unittest.TestCase):
    """Tests for DefaultScoring implementation."""

    def test_default_scoring_basic(self) -> None:
        """Test basic scoring functionality."""
        scoring = DefaultScoring()

        test_row = pd.Series(
            {"dividend_yield": 3.0, "payout": 40.0, "dividend_cagr": 8.0}
        )

        score = scoring.score(test_row)
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)


if __name__ == "__main__":
    unittest.main()
