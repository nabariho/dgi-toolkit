"""Validation service for business logic separation.

This module provides service-layer validation that leverages the unified
validation utilities in dgi.validation_utils for consistent error handling.
"""

import logging
import re

from dgi.exceptions import DataValidationError
from dgi.models import CompanyData
from dgi.validation_utils import (
    validate_cagr,
    validate_file_path,
    validate_numeric_bounds,
    validate_percentage,
    validate_portfolio_size,
    validate_uuid_format,
    validate_weighting_method,
    validate_yield_rate,
)

logger = logging.getLogger(__name__)


class ValidationService:
    """Service class for validation business logic.

    This service leverages the unified validation utilities to ensure
    consistent error handling and validation logic across the application.
    """

    @staticmethod
    def validate_company_data(company: CompanyData) -> None:
        """Validate company data using business rules."""
        # Validate required fields
        if not company.symbol or not company.symbol.strip():
            raise DataValidationError("Company symbol is required")

        if not company.name or not company.name.strip():
            raise DataValidationError("Company name is required")

        # Validate financial metrics
        validate_yield_rate(company.dividend_yield, "dividend_yield")
        validate_percentage(company.payout_ratio, "payout_ratio")
        validate_cagr(company.dividend_growth_5y, "dividend_growth_5y")
        validate_yield_rate(company.fcf_yield, "fcf_yield")

    @staticmethod
    def sanitize_company_name(name: str) -> str:
        """Sanitize company name by removing extra whitespace."""
        if not name:
            return ""

        # Remove leading/trailing whitespace
        sanitized = name.strip()

        # Normalize multiple spaces to single space
        sanitized = re.sub(r"\s+", " ", sanitized)

        return sanitized

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate stock symbol format."""
        if not symbol:
            return False

        # Check length (most symbols are 1-5 characters, max 9 characters)
        if len(symbol) > 9:
            return False

        # Check if it contains only alphanumeric characters
        if not re.match(r"^[A-Za-z0-9]+$", symbol):
            return False

        return True

    @staticmethod
    def validate_yield_rate(yield_rate: float, field_name: str = "yield_rate") -> float:
        """Validate dividend yield rate using business rules (0-100%)."""
        return validate_yield_rate(yield_rate, field_name)

    @staticmethod
    def validate_percentage(percentage: float, field_name: str = "percentage") -> float:
        """Validate percentage values using business rules."""
        return validate_percentage(percentage, field_name)

    @staticmethod
    def validate_cagr(cagr: float, field_name: str = "cagr") -> float:
        """Validate CAGR values using business rules (-100% to 100%)."""
        return validate_cagr(cagr, field_name)

    @staticmethod
    def validate_portfolio_size(size: int, field_name: str = "portfolio_size") -> int:
        """Validate portfolio size using business rules."""
        return validate_portfolio_size(size, field_name)

    @staticmethod
    def validate_weighting_method(weighting: str, field_name: str = "weighting") -> str:
        """Validate weighting method using business rules."""
        return validate_weighting_method(weighting, field_name)

    @staticmethod
    def validate_file_path(
        file_path: str,
        allowed_extensions: list[str] | None = None,
        field_name: str = "file_path",
    ) -> str:
        """Validate file path using business rules."""
        return validate_file_path(file_path, allowed_extensions=allowed_extensions)

    @staticmethod
    def validate_uuid_format(uuid_str: str, field_name: str = "uuid") -> str:
        """Validate UUID format using business rules."""
        return validate_uuid_format(uuid_str, field_name)

    @staticmethod
    def validate_financial_data_edge_cases(
        value: float, field_name: str = "value"
    ) -> float:
        """Validate financial data for edge cases like infinity and NaN."""
        return validate_numeric_bounds(
            value, min_val=float("-inf"), max_val=float("inf"), field_name=field_name
        )

    @staticmethod
    def sanitize_for_logging(value: str) -> str:
        """Sanitize value for safe logging."""
        from dgi.validation_utils import sanitize_for_logging as _sanitize

        return _sanitize(value)

    @staticmethod
    def validate_screening_parameters(
        min_yield: float, max_payout: float, min_cagr: float, top_n: int
    ) -> None:
        """Validate screening parameters comprehensively."""
        # Validate each parameter using unified validation
        validate_yield_rate(min_yield, "min_yield")
        validate_percentage(max_payout, "max_payout")
        validate_cagr(min_cagr, "min_cagr")
        validate_portfolio_size(top_n, "top_n")

        # Additional business rule validations
        if min_yield > max_payout:
            raise DataValidationError(
                "Minimum yield cannot be greater than maximum payout",
                field="screening_parameters",
            )

        if top_n > 1000:
            raise DataValidationError(
                "Top N cannot exceed 1000 for performance reasons",
                field="top_n",
                value=top_n,
            )
