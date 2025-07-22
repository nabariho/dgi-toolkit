import pandas as pd
import pytest
from dgi.portfolio import build, summary_stats


def sample_df():
    return pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "score": [10, 20, 30],
            "dividend_yield": [2.0, 3.0, 4.0],
            "dividend_cagr": [5.0, 6.0, 7.0],
            "payout": [40.0, 50.0, 60.0],
        }
    )


def test_build_equal_weight():
    df = sample_df()
    result = build(df, top_n=2, weighting="equal")
    assert result.shape[0] == 2
    assert all(abs(w - 0.5) < 1e-8 for w in result["weight"])
    assert set(result["ticker"]) == {"B", "C"}  # top 2 by score


def test_build_score_weight():
    df = sample_df()
    result = build(df, top_n=2, weighting="score")
    assert result.shape[0] == 2
    total_score = 20 + 30
    expected_weights = [20 / total_score, 30 / total_score]
    assert all(
        abs(w - ew) < 1e-8
        for w, ew in zip(sorted(result["weight"]), sorted(expected_weights))
    )
    assert set(result["ticker"]) == {"B", "C"}


def test_build_invalid_weighting():
    df = sample_df()
    with pytest.raises(ValueError):
        build(df, top_n=2, weighting="invalid")


def test_build_topn_too_large():
    df = sample_df()
    with pytest.raises(ValueError):
        build(df, top_n=10, weighting="equal")


def test_summary_stats():
    df = sample_df()
    stats = summary_stats(df)
    assert abs(stats["yield"] - 3.0) < 1e-8
    assert abs(stats["median_cagr"] - 6.0) < 1e-8
    assert abs(stats["mean_payout"] - 50.0) < 1e-8
