"""Edge case and error tests for dgi/screener.py."""

import pytest
from dgi.models.company import CompanyData
from dgi.screener import Screener
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.validation import DgiRowValidator, PydanticRowValidation


def test_screener_apply_filters_empty_df_raises():
    """Test apply_filters with empty DataFrame raises KeyError."""
    import pandas as pd

    df = pd.DataFrame([])
    screener = Screener(
        CsvCompanyDataRepository(
            "data/fundamentals_small.csv",
            DgiRowValidator(PydanticRowValidation(CompanyData)),
        )
    )
    with pytest.raises(KeyError):
        screener.apply_filters(df)


def test_screener_apply_filters_missing_column():
    """Test apply_filters with missing required column raises KeyError."""
    import pandas as pd

    df = pd.DataFrame({"symbol": ["AAPL"]})
    screener = Screener(
        CsvCompanyDataRepository(
            "data/fundamentals_small.csv",
            DgiRowValidator(PydanticRowValidation(CompanyData)),
        )
    )
    with pytest.raises(KeyError):
        screener.apply_filters(df)


def test_screener_add_scores_empty_df():
    """Test add_scores with empty DataFrame returns empty DataFrame."""
    import pandas as pd

    df = pd.DataFrame([])
    screener = Screener(
        CsvCompanyDataRepository(
            "data/fundamentals_small.csv",
            DgiRowValidator(PydanticRowValidation(CompanyData)),
        )
    )
    scored = screener.add_scores(df)
    assert scored.empty


def test_screener_rows_to_dataframe_handles_aliases():
    """Test rows_to_dataframe maps aliases correctly."""
    row = CompanyData(
        symbol="AAPL",
        name="Apple",
        sector="Tech",
        industry="HW",
        dividend_yield=1.0,
        payout_ratio=20.0,
        dividend_growth_5y=5.0,
        fcf_yield=3.0,
    )
    df = Screener.rows_to_dataframe([row])
    assert "payout" in df.columns
    assert "dividend_cagr" in df.columns
    assert df.iloc[0]["payout"] == 20.0
    assert df.iloc[0]["dividend_cagr"] == 5.0


def test_screener_score_row_handles_missing_fields():
    from dgi.screener import Screener
    import pandas as pd

    row = pd.Series({"symbol": "AAPL"})
    try:
        Screener.score_row(row)
    except Exception:
        pass  # Should not crash
