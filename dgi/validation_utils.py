"""Input validation and sanitization utilities for DGI Toolkit.

This module provides comprehensive input validation and sanitization functions
following security best practices to prevent common vulnerabilities like
directory traversal, injection attacks, and data corruption.
"""

import math
import os
import re
import unicodedata
import uuid
from typing import Any
from urllib.parse import urlparse

import pandas as pd

from .exceptions import (
    DataFrameValidationError,
    DataValidationError,
    PathValidationError,
    SecurityValidationError,
    URLValidationError,
)

__all__ = [
    "sanitize_string",
    "validate_file_path",
    "validate_numeric_bounds",
    "validate_percentage",
    "validate_yield_rate",
    "validate_cagr",
    "validate_portfolio_size",
    "validate_weighting_method",
    "validate_financial_value",
    "validate_dividend_yield",
    "validate_payout_ratio",
    "validate_dividend_growth",
    "validate_fcf_yield",
    "validate_company_data_comprehensive",
    "sanitize_for_logging",
    "validate_url",
    "validate_uuid_format",
    "validate_user_id",
    "validate_csv_data",
    "PathValidationError",
    "SecurityValidationError",
    "URLValidationError",
    "DataFrameValidationError",
    "DataValidationError",
]


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string input to prevent injection attacks.

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        SecurityValidationError: If the string contains dangerous patterns
    """
    if not isinstance(value, str):
        raise SecurityValidationError(f"Expected string, got {type(value).__name__}")

    # Check length
    if len(value) > max_length:
        raise SecurityValidationError(f"String too long (max {max_length} characters)")

    # Normalize unicode to prevent homograph attacks
    normalized = unicodedata.normalize("NFKC", value)

    # Remove null bytes and control characters (except newlines and tabs)
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)

    # Check for potentially dangerous patterns
    dangerous_patterns = [
        r"<script\b",  # Script tags (simplified)
        r"javascript:",  # JavaScript protocol
        r"data:",  # Data URLs
        r"vbscript:",  # VBScript protocol
        r"on\w+\s*=",  # Event handlers
        r"<iframe\b",  # Iframe tags
        r"<object\b",  # Object tags
        r"<embed\b",  # Embed tags
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            raise SecurityValidationError(
                f"String contains potentially dangerous content: {pattern}"
            )

    return sanitized.strip()


def validate_file_path(
    path: str,
    base_dir: str | None = None,
    allowed_extensions: list[str] | None = None,
) -> str:
    """Validate and sanitize a file path to prevent directory traversal attacks.

    Args:
        path: The file path to validate
        base_dir: Base directory to restrict paths to (optional)
        allowed_extensions: List of allowed file extensions (optional)

    Returns:
        Normalized and validated file path

    Raises:
        PathValidationError: If the path is invalid or dangerous
    """
    if not isinstance(path, str):
        raise PathValidationError(f"Expected string path, got {type(path).__name__}")

    # Sanitize the path string
    sanitized_path = sanitize_string(path, max_length=500)

    # Normalize path separators
    normalized_path = os.path.normpath(sanitized_path)

    # Check for directory traversal attempts
    if ".." in normalized_path:
        raise PathValidationError("Path contains directory traversal attempt")

    # Check for absolute paths if base_dir is specified
    if base_dir and os.path.isabs(normalized_path):
        raise PathValidationError(
            "Absolute paths not allowed when base_dir is specified"
        )

    # Construct full path if base_dir is provided
    if base_dir:
        full_path = os.path.join(base_dir, normalized_path)
        # Ensure the final path is within the base directory
        try:
            full_path = os.path.abspath(full_path)
            base_dir_abs = os.path.abspath(base_dir)
            if not full_path.startswith(base_dir_abs):
                raise PathValidationError("Path outside of allowed base directory")
        except (OSError, ValueError) as e:
            raise PathValidationError(f"Invalid path: {e}") from e
    else:
        full_path = normalized_path

    # Check file extension if specified
    if allowed_extensions:
        file_ext = os.path.splitext(full_path)[1].lower()
        if file_ext not in allowed_extensions:
            raise PathValidationError(
                f"File extension {file_ext} not allowed. Allowed: {allowed_extensions}"
            )

    return full_path


def validate_numeric_bounds(
    value: int | float,
    min_val: int | float | None = None,
    max_val: int | float | None = None,
    field_name: str = "value",
) -> int | float:
    """Validate numeric values within specified bounds.

    Args:
        value: The numeric value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages

    Returns:
        The validated value

    Raises:
        ValidationError: If the value is outside the allowed range
    """
    if not isinstance(value, int | float):
        raise DataValidationError(
            f"{field_name} must be numeric", field=field_name, value=value
        )

    # Check for NaN or infinity
    if isinstance(value, float) and (pd.isna(value) or not math.isfinite(value)):
        raise DataValidationError(
            f"{field_name} cannot be NaN or infinite", field=field_name, value=value
        )

    if min_val is not None and value < min_val:
        raise DataValidationError(
            f"{field_name} must be at least {min_val}", field=field_name, value=value
        )

    if max_val is not None and value > max_val:
        raise DataValidationError(
            f"{field_name} must be at most {max_val}", field=field_name, value=value
        )

    return value


def validate_percentage(value: float, field_name: str = "percentage") -> float:
    """Validate percentage values (0-100).

    Args:
        value: The percentage value to validate
        field_name: Name of the field for error messages

    Returns:
        The validated percentage value

    Raises:
        ValidationError: If the value is not a valid percentage
    """
    return validate_numeric_bounds(value, 0.0, 100.0, field_name)


def validate_yield_rate(value: float, field_name: str = "yield_rate") -> float:
    """Validate dividend yield rates (0-100).

    Args:
        value: The yield rate to validate
        field_name: Name of the field for error messages

    Returns:
        The validated yield rate

    Raises:
        ValidationError: If the value is not a valid yield rate
    """
    return validate_numeric_bounds(value, 0.0, 100.0, field_name)


def validate_cagr(value: float, field_name: str = "cagr") -> float:
    """Validate CAGR values (reasonable range for dividend growth).

    Args:
        value: The CAGR value to validate
        field_name: Name of the field for error messages

    Returns:
        The validated CAGR value

    Raises:
        ValidationError: If the value is not a valid CAGR
    """
    return validate_numeric_bounds(value, -50.0, 100.0, field_name)


def validate_portfolio_size(value: int, field_name: str = "portfolio_size") -> int:
    """Validate portfolio size (reasonable range for number of stocks).

    Args:
        value: The portfolio size to validate
        field_name: Name of the field for error messages

    Returns:
        The validated portfolio size

    Raises:
        ValidationError: If the value is not a valid portfolio size
    """
    result = validate_numeric_bounds(value, 1, 100, field_name)
    return int(result)


def validate_weighting_method(value: str, field_name: str = "weighting_method") -> str:
    """Validate portfolio weighting method.

    Args:
        value: The weighting method to validate
        field_name: Name of the field for error messages

    Returns:
        The validated weighting method

    Raises:
        ValidationError: If the value is not a valid weighting method
    """
    if not isinstance(value, str):
        raise DataValidationError(
            f"{field_name} must be a string", field=field_name, value=value
        )

    sanitized = sanitize_string(value, max_length=50)
    allowed_methods = ["equal", "score", "market_cap", "dividend_weight"]

    if sanitized.lower() not in allowed_methods:
        raise DataValidationError(
            f"{field_name} must be one of: {allowed_methods}",
            field=field_name,
            value=value,
        )

    return sanitized.lower()


def validate_financial_value(
    value: float, field_name: str = "financial_value"
) -> float:
    """Validate financial values for common edge cases.

    This function handles infinity, NaN, and other problematic values
    that can occur in financial data processing.

    Args:
        value: The financial value to validate
        field_name: Name of the field for error messages

    Returns:
        The validated financial value

    Raises:
        DataValidationError: If the value contains problematic financial data
    """
    if not isinstance(value, int | float):
        raise DataValidationError(
            f"{field_name} must be a number", field=field_name, value=value
        )

    # Check for NaN
    if pd.isna(value):
        raise DataValidationError(
            f"{field_name} cannot be NaN", field=field_name, value=value
        )

    # Check for infinity
    if not math.isfinite(value):
        raise DataValidationError(
            f"{field_name} cannot be infinite", field=field_name, value=value
        )

    return float(value)


def validate_dividend_yield(value: float, field_name: str = "dividend_yield") -> float:
    """Validate dividend yield with financial data edge case handling.

    Dividend yield should be positive and reasonable (typically 0-50%).

    Args:
        value: The dividend yield to validate
        field_name: Name of the field for error messages

    Returns:
        The validated dividend yield

    Raises:
        DataValidationError: If the value is not a valid dividend yield
    """
    # First validate for financial edge cases
    validated_value = validate_financial_value(value, field_name)

    # Then apply dividend yield specific rules
    if validated_value < 0:
        raise DataValidationError(
            f"{field_name} cannot be negative", field=field_name, value=validated_value
        )

    if validated_value > 50:  # Unrealistic dividend yield > 50%
        raise DataValidationError(
            f"{field_name} cannot exceed 50% (unrealistic)",
            field=field_name,
            value=validated_value,
        )

    return validated_value


def validate_payout_ratio(value: float, field_name: str = "payout_ratio") -> float:
    """Validate payout ratio with financial data edge case handling.

    Payout ratio should be positive and reasonable (typically 0-200%).

    Args:
        value: The payout ratio to validate
        field_name: Name of the field for error messages

    Returns:
        The validated payout ratio

    Raises:
        DataValidationError: If the value is not a valid payout ratio
    """
    # First validate for financial edge cases
    validated_value = validate_financial_value(value, field_name)

    # Then apply payout ratio specific rules
    if validated_value < 0:
        raise DataValidationError(
            f"{field_name} cannot be negative", field=field_name, value=validated_value
        )

    if validated_value > 200:  # Unrealistic payout ratio > 200%
        raise DataValidationError(
            f"{field_name} cannot exceed 200% (unrealistic)",
            field=field_name,
            value=validated_value,
        )

    return validated_value


def validate_dividend_growth(
    value: float, field_name: str = "dividend_growth"
) -> float:
    """Validate dividend growth with financial data edge case handling.

    Dividend growth can be negative or positive but should be reasonable.

    Args:
        value: The dividend growth to validate
        field_name: Name of the field for error messages

    Returns:
        The validated dividend growth

    Raises:
        DataValidationError: If the value is not a valid dividend growth
    """
    # First validate for financial edge cases
    validated_value = validate_financial_value(value, field_name)

    # Then apply dividend growth specific rules
    if validated_value < -100:  # Cannot lose more than 100%
        raise DataValidationError(
            f"{field_name} cannot be less than -100%",
            field=field_name,
            value=validated_value,
        )

    if validated_value > 100:  # Unrealistic growth > 100%
        raise DataValidationError(
            f"{field_name} cannot exceed 100% (unrealistic)",
            field=field_name,
            value=validated_value,
        )

    return validated_value


def validate_fcf_yield(value: float, field_name: str = "fcf_yield") -> float:
    """Validate free cash flow yield with financial data edge case handling.

    FCF yield can be negative or positive but should be reasonable.

    Args:
        value: The FCF yield to validate
        field_name: Name of the field for error messages

    Returns:
        The validated FCF yield

    Raises:
        DataValidationError: If the value is not a valid FCF yield
    """
    # First validate for financial edge cases
    validated_value = validate_financial_value(value, field_name)

    # Then apply FCF yield specific rules
    if validated_value < -50:  # Unrealistic negative FCF yield
        raise DataValidationError(
            f"{field_name} cannot be less than -50% (unrealistic)",
            field=field_name,
            value=validated_value,
        )

    if validated_value > 50:  # Unrealistic positive FCF yield
        raise DataValidationError(
            f"{field_name} cannot exceed 50% (unrealistic)",
            field=field_name,
            value=validated_value,
        )

    return validated_value


def validate_company_data_comprehensive(data: dict[str, Any]) -> dict[str, Any]:
    """Validate company data comprehensively with all financial edge cases.

    This function validates all financial fields in company data with
    appropriate business rules and edge case handling.

    Args:
        data: Dictionary containing company data

    Returns:
        Validated company data dictionary

    Raises:
        DataValidationError: If any field fails validation
    """
    validated_data: dict[str, Any] = {}

    # Validate required financial fields
    if "dividend_yield" in data:
        validated_data["dividend_yield"] = validate_dividend_yield(
            data["dividend_yield"], "dividend_yield"
        )

    if "payout_ratio" in data:
        validated_data["payout_ratio"] = validate_payout_ratio(
            data["payout_ratio"], "payout_ratio"
        )

    if "dividend_growth_5y" in data:
        validated_data["dividend_growth_5y"] = validate_dividend_growth(
            data["dividend_growth_5y"], "dividend_growth_5y"
        )

    if "fcf_yield" in data:
        validated_data["fcf_yield"] = validate_fcf_yield(data["fcf_yield"], "fcf_yield")

    # Validate non-financial fields
    if "symbol" in data:
        validated_data["symbol"] = sanitize_string(str(data["symbol"]), max_length=10)

    if "name" in data:
        validated_data["name"] = sanitize_string(str(data["name"]), max_length=100)

    if "sector" in data:
        validated_data["sector"] = sanitize_string(str(data["sector"]), max_length=50)

    if "industry" in data:
        validated_data["industry"] = sanitize_string(
            str(data["industry"]), max_length=50
        )

    return validated_data


def sanitize_for_logging(value: Any, max_length: int = 200) -> str:
    """Sanitize a value for safe logging to prevent log injection.

    Args:
        value: The value to sanitize for logging
        max_length: Maximum length for the logged string

    Returns:
        Sanitized string safe for logging
    """
    if value is None:
        return "None"

    # Convert to string
    str_value = str(value)

    # Truncate if too long before sanitization
    if len(str_value) > max_length:
        str_value = str_value[: max_length - 3] + "..."

    # Sanitize the truncated string
    try:
        sanitized = sanitize_string(str_value, max_length)
        return sanitized
    except SecurityValidationError:
        # If sanitization fails, return a safe fallback
        return f"[SANITIZED: {type(value).__name__}]"


def validate_url(url: str, allowed_schemes: list[str] | None = None) -> str:
    """Validate and sanitize a URL.

    Args:
        url: The URL to validate
        allowed_schemes: List of allowed URL schemes (e.g., ['http', 'https'])

    Returns:
        The validated URL

    Raises:
        ValidationError: If the URL is invalid or uses disallowed schemes
    """
    if not isinstance(url, str):
        raise URLValidationError(f"Expected string URL, got {type(url).__name__}")

    sanitized_url = sanitize_string(url, max_length=500)

    try:
        parsed = urlparse(sanitized_url)
    except Exception as e:
        raise URLValidationError(f"Invalid URL format: {e}") from e

    if not parsed.scheme:
        raise URLValidationError("URL must include a scheme (e.g., http://, https://)")

    if allowed_schemes and parsed.scheme.lower() not in allowed_schemes:
        raise URLValidationError(
            f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}"
        )

    return sanitized_url


def validate_uuid_format(value: str, field_name: str = "uuid") -> str:
    """Validate UUID format.

    Args:
        value: The UUID string to validate
        field_name: Name of the field for error messages

    Returns:
        The validated UUID string

    Raises:
        ValidationError: If the value is not a valid UUID format
    """
    if not isinstance(value, str):
        raise DataValidationError(
            f"{field_name} must be a string", field=field_name, value=value
        )

    sanitized = sanitize_string(value, max_length=50)

    try:
        uuid.UUID(sanitized)
        return sanitized
    except ValueError as e:
        raise DataValidationError(
            f"{field_name} must be a valid UUID format", field=field_name, value=value
        ) from e


def validate_user_id(value: str, field_name: str = "user_id") -> str:
    """Validate user ID format.

    Args:
        value: The user ID string to validate
        field_name: Name of the field for error messages

    Returns:
        The validated user ID string

    Raises:
        ValidationError: If the value is not a valid user ID format
    """
    if not isinstance(value, str):
        raise DataValidationError(
            f"{field_name} must be a string", field=field_name, value=value
        )

    sanitized = sanitize_string(value, max_length=100)

    # Check for valid user ID pattern (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a-zA-Z0-9_-]+$", sanitized):
        raise DataValidationError(
            f"{field_name} must contain only alphanumeric characters, underscores, and hyphens",
            field=field_name,
            value=value,
        )

    return sanitized


def validate_csv_data(
    df: pd.DataFrame,
    required_columns: list[str] | None = None,
    max_rows: int = 10000,
) -> pd.DataFrame:
    """Validate CSV data structure and content.

    Args:
        df: The DataFrame to validate
        required_columns: List of required column names
        max_rows: Maximum number of rows allowed

    Returns:
        The validated DataFrame

    Raises:
        ValidationError: If the data is invalid
    """
    if not isinstance(df, pd.DataFrame):
        raise DataFrameValidationError(f"Expected DataFrame, got {type(df).__name__}")

    if df.empty:
        raise DataFrameValidationError("DataFrame is empty")

    if len(df) > max_rows:
        raise DataFrameValidationError(f"DataFrame has too many rows (max {max_rows})")

    if required_columns:
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise DataFrameValidationError(
                f"Missing required columns: {missing_columns}"
            )

    # Check for suspicious column names
    for col in df.columns:
        if not isinstance(col, str):
            raise DataFrameValidationError(
                f"Column names must be strings, got {type(col).__name__}"
            )

        try:
            sanitized_col = sanitize_string(col, max_length=100)
            if sanitized_col != col:
                raise DataFrameValidationError(
                    f"Column name contains invalid characters: {col}"
                )
        except SecurityValidationError as e:
            raise DataFrameValidationError(
                f"Column name contains invalid characters: {col}"
            ) from e

    return df
