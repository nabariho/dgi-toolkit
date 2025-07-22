import pandas as pd
from typing import Any
import pytest  # type: ignore
from dgi.screener import load_universe, apply_filters, score
from dgi.models import DgiRow
from dgi.validation import DgiRowValidator


def test_load_universe(tmp_path: Any) -> None:
    # Create a temporary CSV with all required columns
    csv = tmp_path / "fundamentals.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,0.6,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,0.8,35,10,7\n"
    )
    df = load_universe(str(csv))
    assert list(df.columns) == [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    assert df.shape[0] == 2
    assert df["dividend_yield"].dtype == float


def test_load_universe_missing_columns(tmp_path: Any) -> None:
    # Create a CSV missing required columns
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "symbol,name,sector\n"  # missing most required columns
        "AAPL,Apple,Tech\n"
    )
    with pytest.raises(ValueError) as excinfo:
        load_universe(str(csv))
    assert "Missing required columns" in str(excinfo.value)
    assert "dividend_yield" in str(excinfo.value)
    assert "payout" in str(excinfo.value)


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
    filtered = apply_filters(df, min_yield=1.5, max_payout=50.0, min_cagr=5.0)
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
    s = score(row)
    assert abs(s - 0.16666666666666666) < 1e-6  # (0.5 + 0.5 - 0.5) / 3


def test_load_universe_invalid_types(tmp_path: Any) -> None:
    # Create a CSV with invalid types in numeric columns
    csv = tmp_path / "bad_types.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"  # invalid dividend_yield
        "MSFT,Microsoft,Tech,Software,0.8,thirtyfive,10,7\n"  # invalid payout
        "GOOG,Google,Tech,Software,1.2,30,12,8\n"  # valid row
    )
    with pytest.raises(ValueError) as excinfo:
        load_universe(str(csv))
    msg = str(excinfo.value)
    assert "Row 2" in msg and "is not a valid number" in msg
    assert "Row 3" in msg and "is not a valid number" in msg
    assert "dividend_yield" in msg or "payout" in msg
    assert "GOOG" not in msg  # valid row should not be in error message


def test_load_universe_only_valid_rows(tmp_path: Any) -> None:
    # Create a CSV with one valid and one invalid row
    csv = tmp_path / "mixed.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"  # invalid
        "GOOG,Google,Tech,Software,1.2,30,12,8\n"  # valid
    )
    # Should raise error for invalid row
    with pytest.raises(ValueError):
        load_universe(str(csv))
    # If we remove the invalid row, it should load
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "GOOG,Google,Tech,Software,1.2,30,12,8\n"
    )
    df = load_universe(str(csv))
    assert df.shape[0] == 1
    assert df.iloc[0]["symbol"] == "GOOG"


def test_dgirow_valid() -> None:
    row = DgiRow(
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
    assert isinstance(row.dividend_yield, float)


def test_dgirow_invalid_type() -> None:
    # Should raise error for invalid type
    import pytest

    with pytest.raises(Exception):
        DgiRow(
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
    validator = DgiRowValidator(DgiRow)
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
    assert valid[0]["symbol"] == "AAPL"


def test_dgirowvalidator_invalid() -> None:
    validator = DgiRowValidator(DgiRow)
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
    import pytest

    with pytest.raises(ValueError):
        validator.validate_rows(rows)
