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


class ValidationError(Exception):
    """Base exception for validation errors."""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class SecurityValidationError(ValidationError):
    """Exception for security-related validation failures."""


class PathValidationError(ValidationError):
    """Exception for path validation failures."""


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
            raise PathValidationError(f"Invalid path: {e}")
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
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{field_name} must be numeric", field=field_name, value=value
        )

    # Check for NaN or infinity
    if isinstance(value, float) and (pd.isna(value) or not math.isfinite(value)):
        raise ValidationError(
            f"{field_name} cannot be NaN or infinite", field=field_name, value=value
        )

    if min_val is not None and value < min_val:
        raise ValidationError(
            f"{field_name} must be at least {min_val}", field=field_name, value=value
        )

    if max_val is not None and value > max_val:
        raise ValidationError(
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
    return validate_numeric_bounds(value, 1, 100, field_name)


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
        raise ValidationError(
            f"{field_name} must be a string", field=field_name, value=value
        )

    sanitized = sanitize_string(value, max_length=50)
    allowed_methods = ["equal", "score", "market_cap", "dividend_weight"]

    if sanitized.lower() not in allowed_methods:
        raise ValidationError(
            f"{field_name} must be one of: {allowed_methods}",
            field=field_name,
            value=value,
        )

    return sanitized.lower()


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
        raise ValidationError(f"Expected string URL, got {type(url).__name__}")

    sanitized_url = sanitize_string(url, max_length=500)

    try:
        parsed = urlparse(sanitized_url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}")

    if not parsed.scheme:
        raise ValidationError("URL must include a scheme (e.g., http://, https://)")

    if allowed_schemes and parsed.scheme.lower() not in allowed_schemes:
        raise ValidationError(
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
        raise ValidationError(
            f"{field_name} must be a string", field=field_name, value=value
        )

    sanitized = sanitize_string(value, max_length=50)

    try:
        uuid.UUID(sanitized)
        return sanitized
    except ValueError:
        raise ValidationError(
            f"{field_name} must be a valid UUID format", field=field_name, value=value
        )


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
        raise ValidationError(
            f"{field_name} must be a string", field=field_name, value=value
        )

    sanitized = sanitize_string(value, max_length=100)

    # Check for valid user ID pattern (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a-zA-Z0-9_-]+$", sanitized):
        raise ValidationError(
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
        raise ValidationError(f"Expected DataFrame, got {type(df).__name__}")

    if df.empty:
        raise ValidationError("DataFrame is empty")

    if len(df) > max_rows:
        raise ValidationError(f"DataFrame has too many rows (max {max_rows})")

    if required_columns:
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValidationError(f"Missing required columns: {missing_columns}")

    # Check for suspicious column names
    for col in df.columns:
        if not isinstance(col, str):
            raise ValidationError(
                f"Column names must be strings, got {type(col).__name__}"
            )

        try:
            sanitized_col = sanitize_string(col, max_length=100)
            if sanitized_col != col:
                raise ValidationError(f"Column name contains invalid characters: {col}")
        except SecurityValidationError:
            raise ValidationError(f"Column name contains invalid characters: {col}")

    return df
