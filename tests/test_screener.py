import pytest
import pandas as pd
from typing import Any
from dgi.models import CompanyData
from dgi.validation import DgiRowValidator, PydanticRowValidation
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.screener import Screener


def make_screener(csv_path: str) -> Screener:
    repo = CsvCompanyDataRepository(csv_path, DgiRowValidator())
    return Screener(repo)


def test_load_universe_valid(tmp_path: Any) -> None:
    csv = tmp_path / "fundamentals.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,0.6,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,0.8,35,10,7\n"
    )
    screener = make_screener(str(csv))
    df = screener.load_universe()
    expected_columns = [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    assert list(df.columns) == expected_columns
    assert df.shape[0] == 2
    for col in ["dividend_yield", "payout", "dividend_cagr", "fcf_yield"]:
        assert df[col].dtype == float


def test_load_universe_invalid_all_rows(tmp_path: Any) -> None:
    csv = tmp_path / "invalid.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,not_a_number,35,10,7\n"
    )
    screener = make_screener(str(csv))
    with pytest.raises(
        ValueError,
        match="(Validation errors:|Missing expected columns|No valid rows found)",
    ):
        screener.load_universe()


def test_load_universe_mixed_valid_invalid(tmp_path: Any) -> None:
    csv = tmp_path / "mixed.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"  # invalid
        "GOOG,Google,Tech,Software,1.2,30,12,8\n"  # valid
    )
    screener = make_screener(str(csv))
    df = screener.load_universe()
    assert df.shape[0] == 1
    assert df.iloc[0]["symbol"] == "GOOG"


def test_apply_filters() -> None:
    df = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "dividend_yield": [2.0, 1.0],
            "payout": [40.0, 60.0],
            "dividend_cagr": [7.0, 3.0],
            "name": ["n1", "n2"],
            "sector": ["s1", "s2"],
            "industry": ["i1", "i2"],
            "fcf_yield": [4.0, 2.0],
        }
    )
    screener = Screener(None)  # No repo needed for filtering
    filtered = screener.apply_filters(df, min_yield=1.5, max_payout=50.0, min_cagr=5.0)
    assert filtered.shape[0] == 1
    assert filtered.iloc[0]["symbol"] == "A"


def test_score() -> None:
    row = pd.Series(
        {
            "dividend_cagr": 10.0,  # 0.5 normalized
            "fcf_yield": 10.0,  # 0.5 normalized
            "payout": 50.0,  # 0.5 normalized
        }
    )
    screener = Screener(None)
    s = screener.default_score(row)
    assert abs(s - 0.16666666666666666) < 1e-6  # (0.5 + 0.5 - 0.5) / 3


def test_load_universe_invalid_types(tmp_path: Any) -> None:
    csv = tmp_path / "bad_types.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"  # invalid dividend_yield
        "MSFT,Microsoft,Tech,Software,0.8,thirtyfive,10,7\n"  # invalid payout
        "GOOG,Google,Tech,Software,1.2,30,12,8\n"  # valid row
    )
    screener = make_screener(str(csv))
    df = screener.load_universe()
    assert df.shape[0] == 1
    assert df.iloc[0]["symbol"] == "GOOG"


def test_csv_repository_and_screener(tmp_path: Any) -> None:
    csv = tmp_path / "repo_test.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,0.6,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,0.8,35,10,7\n"
    )
    repo = CsvCompanyDataRepository(str(csv), DgiRowValidator())
    screener = Screener(repo)
    df = screener.load_universe()
    assert df.shape[0] == 2
    assert set(df["symbol"]) == {"AAPL", "MSFT"}


def test_companydata_valid() -> None:
    row = CompanyData(
        symbol="AAPL",
        name="Apple",
        sector="Tech",
        industry="Hardware",
        dividend_yield=0.6,
        payout=20.0,
        dividend_cagr=8.0,
        fcf_yield=5.0,
    )
    assert row.symbol == "AAPL"
    assert row.dividend_yield == 0.6


def test_companydata_invalid() -> None:
    # This test intentionally passes the wrong type to check runtime validation.
    with pytest.raises(Exception):
        CompanyData(
            symbol="AAPL",
            name="Apple",
            sector="Tech",
            industry="Hardware",
            dividend_yield="not_a_number",
            payout=20.0,
            dividend_cagr=8.0,
            fcf_yield=5.0,
        )


def test_dgirowvalidator_valid() -> None:
    validator = DgiRowValidator(validation_strategy=PydanticRowValidation(CompanyData))
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "Hardware",
            "dividend_yield": 0.6,
            "payout": 20.0,
            "dividend_cagr": 8.0,
            "fcf_yield": 5.0,
        }
    ]
    valid = validator.validate_rows(rows)
    assert valid[0].symbol == "AAPL"


def test_dgirowvalidator_invalid() -> None:
    validator = DgiRowValidator(CompanyData)
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "Hardware",
            "dividend_yield": "not_a_number",
            "payout": 20.0,
            "dividend_cagr": 8.0,
            "fcf_yield": 5.0,
        }
    ]
    with pytest.raises(ValueError):
        validator.validate_rows(rows)


def test_screener_empty_repository():
    class EmptyRepo:
        def get_rows(self):
            return []

    screener = Screener(EmptyRepo())
    with pytest.raises(ValueError):
        screener.load_universe()


def test_screener_missing_columns(tmp_path: Any):
    csv = tmp_path / "missing_cols.csv"
    csv.write_text("symbol,name,sector\nAAPL,Apple,Tech\n")
    repo = CsvCompanyDataRepository(str(csv), DgiRowValidator())
    screener = Screener(repo)
    with pytest.raises(ValueError):
        screener.load_universe()


def test_screener_score_edge_cases():
    screener = Screener(None)
    # All zeros
    row = pd.Series({"dividend_cagr": 0.0, "fcf_yield": 0.0, "payout": 0.0})
    assert screener.default_score(row) == 0.0
    # All max
    row = pd.Series({"dividend_cagr": 20.0, "fcf_yield": 20.0, "payout": 0.0})
    assert abs(screener.default_score(row) - 0.6666666666666666) < 1e-8
    # Negative values (should clamp to 0)
    row = pd.Series({"dividend_cagr": -10.0, "fcf_yield": -10.0, "payout": -10.0})
    assert screener.default_score(row) == 0.0
    # Over max (should clamp to 1)
    row = pd.Series({"dividend_cagr": 100.0, "fcf_yield": 100.0, "payout": 0.0})
    assert screener.default_score(row) == 0.6666666666666666
