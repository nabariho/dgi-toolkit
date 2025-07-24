"""Tests for dgi/validation.py edge cases and errors."""

import pytest
from dgi.models.company import CompanyData
from dgi.validation import DgiRowValidator, PydanticRowValidation, DataValidationError


def test_dgirowvalidator_missing_required_columns():
    """Test DgiRowValidator with missing required columns."""
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    validator.required_columns = ["symbol", "name"]
    rows = [{"symbol": "AAPL"}]  # Missing 'name'
    with pytest.raises(DataValidationError) as exc:
        validator.validate_rows(rows)
    assert "Missing" in str(exc.value)


def test_dgirowvalidator_some_invalid(caplog):
    """Test DgiRowValidator with some invalid rows (should skip and warn)."""
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    validator.required_columns = [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    # One valid, one invalid
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "HW",
            "dividend_yield": 1.0,
            "payout": 20.0,
            "dividend_cagr": 5.0,
            "fcf_yield": 3.0,
        },
        {"symbol": "MSFT"},  # Invalid
    ]
    result = validator.validate_rows(rows)
    assert len(result) == 1
    assert any(
        "invalid" in r.lower() or "skipped" in r.lower()
        for r in caplog.text.splitlines()
    )


def test_dgirowvalidator_all_invalid():
    """Test DgiRowValidator with all invalid rows (should raise)."""
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    validator.required_columns = ["symbol", "name"]
    rows = [{"foo": "bar"}, {"baz": "qux"}]
    with pytest.raises(DataValidationError):
        validator.validate_rows(rows)


def test_pydanticrowvalidation_model_validate():
    """Test PydanticRowValidation uses model_validate."""
    validator = PydanticRowValidation(CompanyData)
    row = {
        "symbol": "AAPL",
        "name": "Apple",
        "sector": "Tech",
        "industry": "HW",
        "dividend_yield": 1.0,
        "payout": 20.0,
        "dividend_cagr": 5.0,
        "fcf_yield": 3.0,
    }
    result = validator.validate(row)
    assert isinstance(result, CompanyData)
    assert result.symbol == "AAPL"


def test_dgirowvalidator_some_invalid_rows_warns(caplog):
    """Test DgiRowValidator warns when some rows are invalid but returns valid ones."""
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    validator.required_columns = [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "HW",
            "dividend_yield": 1.0,
            "payout": 20.0,
            "dividend_cagr": 5.0,
            "fcf_yield": 3.0,
        },
        {"symbol": "MSFT"},  # Invalid
        {
            "symbol": "GOOG",
            "name": "Google",
            "sector": "Tech",
            "industry": "SW",
            "dividend_yield": 1.2,
            "payout": 22.0,
            "dividend_cagr": 6.0,
            "fcf_yield": 2.5,
        },
    ]
    result = validator.validate_rows(rows)
    assert len(result) == 2
    assert "Some rows were invalid and skipped" in caplog.text
