"""Test validation functionality."""

import unittest
from typing import Any

from pydantic import ValidationError

from dgi.models import CompanyData
from dgi.validation import DataValidationError, DgiRowValidator, PydanticRowValidation


class TestDgiRowValidator(unittest.TestCase):
    """Test DgiRowValidator class."""

    def test_validate_empty_list(self) -> None:
        """Test validation with empty list."""
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        rows: list[dict[str, Any]] = []
        with self.assertRaises(DataValidationError):
            validator.validate_rows(rows)

    def test_validate_missing_required_fields(self) -> None:
        """Test validation with missing required fields."""
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        rows: list[dict[str, Any]] = [
            {"symbol": "AAPL"},  # Missing required fields
            {
                "symbol": "MSFT",
                "name": "Microsoft Corp",
                "sector": "Technology",
                "industry": "Software",
                "dividend_yield": 2.5,
                "payout": 30.0,
                "dividend_cagr": 8.0,
                "fcf_yield": 4.2,
            },  # Valid row
        ]
        result = validator.validate_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].symbol, "MSFT")

    def test_validate_invalid_data_types(self) -> None:
        """Test validation with invalid data types."""
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        # Create test rows with invalid types
        test_objects = [
            {"invalid": "object"},
            {"another": "invalid", "object": True},
        ]
        with self.assertRaises(DataValidationError):
            validator.validate_rows(test_objects)  # type: ignore[arg-type]

    def test_validate_valid_rows(self) -> None:
        """Test validation with all valid rows."""
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        rows: list[dict[str, Any]] = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "dividend_yield": 1.5,
                "payout": 25.0,
                "dividend_cagr": 5.0,
                "fcf_yield": 3.5,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corp",
                "sector": "Technology",
                "industry": "Software",
                "dividend_yield": 2.5,
                "payout": 30.0,
                "dividend_cagr": 8.0,
                "fcf_yield": 4.2,
            },
        ]
        results = validator.validate_rows(rows)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].symbol, "AAPL")
        self.assertEqual(results[1].symbol, "MSFT")

    def test_validate_raises_error_with_all_invalid(self) -> None:
        """Test that validation raises error when all rows are invalid."""
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        rows: list[dict[str, Any]] = [
            {"symbol": "INVALID1"},  # Missing required fields
            {"symbol": "INVALID2"},  # Missing required fields
        ]

        with self.assertRaises(DataValidationError):
            validator.validate_rows(rows)

    def test_validate_partial_errors_returns_valid_rows(self) -> None:
        """Test validation with some errors returns only valid rows."""
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        rows: list[dict[str, Any]] = [
            {"symbol": "INVALID"},  # Missing required fields
            {
                "symbol": "MSFT",
                "name": "Microsoft Corp",
                "sector": "Technology",
                "industry": "Software",
                "dividend_yield": 2.5,
                "payout": 30.0,
                "dividend_cagr": 8.0,
                "fcf_yield": 4.2,
            },  # Valid row
        ]
        # This should return the valid rows and log warnings about invalid ones
        result = validator.validate_rows(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].symbol, "MSFT")

    def test_validate_invalid_data_types_again(self) -> None:
        """Test validation with another set of invalid data types."""
        validator = DgiRowValidator(PydanticRowValidation(CompanyData))
        # Create test rows with completely invalid structure
        test_objects = [
            {"completely": "wrong", "structure": 123},
            {"not": "a", "valid": "company", "data": "object"},
        ]
        with self.assertRaises(DataValidationError):
            validator.validate_rows(test_objects)  # type: ignore[arg-type]


class TestPydanticRowValidation(unittest.TestCase):
    """Test PydanticRowValidation class."""

    def test_pydantic_validation_success(self) -> None:
        """Test successful pydantic validation."""
        validation = PydanticRowValidation(CompanyData)
        row = {
            "symbol": "AAPL",
            "name": "Apple Inc",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "dividend_yield": 1.5,
            "payout": 25.0,
            "dividend_cagr": 5.0,
            "fcf_yield": 3.5,
        }
        result = validation.validate(row)
        self.assertIsInstance(result, CompanyData)
        self.assertEqual(result.symbol, "AAPL")

    def test_pydantic_validation_failure(self) -> None:
        """Test pydantic validation failure."""
        validation = PydanticRowValidation(CompanyData)
        row = {"symbol": "AAPL"}  # Missing required fields

        with self.assertRaises(ValidationError):
            validation.validate(row)


if __name__ == "__main__":
    unittest.main()
