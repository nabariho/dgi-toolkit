"""Tests for validation utilities module."""

import pandas as pd
import pytest

from dgi.exceptions import (
    DataFrameValidationError,
    DataValidationError,
    PathValidationError,
    SecurityValidationError,
    URLValidationError,
)
from dgi.validation_utils import (
    sanitize_for_logging,
    sanitize_string,
    validate_cagr,
    validate_csv_data,
    validate_file_path,
    validate_numeric_bounds,
    validate_percentage,
    validate_portfolio_size,
    validate_url,
    validate_user_id,
    validate_uuid_format,
    validate_weighting_method,
    validate_yield_rate,
)


class TestSanitizeString:
    """Test string sanitization functionality."""

    def test_valid_string(self):
        """Test that valid strings are returned unchanged."""
        result = sanitize_string("Hello, World!")
        assert result == "Hello, World!"

    def test_unicode_normalization(self):
        """Test unicode normalization."""
        # Test with combining characters
        result = sanitize_string("café")
        assert result == "café"

    def test_control_character_removal(self):
        """Test that control characters are removed."""
        result = sanitize_string("Hello\x00World\x1f")
        assert result == "HelloWorld"

    def test_script_tag_detection(self):
        """Test detection of script tags."""
        with pytest.raises(SecurityValidationError, match="dangerous content"):
            sanitize_string("<script>alert('xss')</script>")

    def test_javascript_protocol_detection(self):
        """Test detection of javascript protocol."""
        with pytest.raises(SecurityValidationError, match="dangerous content"):
            sanitize_string("javascript:alert('xss')")

    def test_event_handler_detection(self):
        """Test detection of event handlers."""
        with pytest.raises(SecurityValidationError, match="dangerous content"):
            sanitize_string("onclick=alert('xss')")

    def test_length_limit(self):
        """Test string length limit."""
        long_string = "a" * 1001
        with pytest.raises(SecurityValidationError, match="too long"):
            sanitize_string(long_string)

    def test_non_string_input(self):
        """Test handling of non-string input."""
        with pytest.raises(SecurityValidationError, match="Expected string"):
            sanitize_string(123)


class TestValidateFilePath:
    """Test file path validation functionality."""

    def test_valid_relative_path(self):
        """Test valid relative path."""
        result = validate_file_path("data/file.csv")
        assert result == "data/file.csv"

    def test_valid_path_with_extension_check(self):
        """Test path validation with extension check."""
        result = validate_file_path("data/file.csv", allowed_extensions=[".csv"])
        assert result == "data/file.csv"

    def test_invalid_extension(self):
        """Test rejection of invalid file extension."""
        with pytest.raises(PathValidationError, match="not allowed"):
            validate_file_path("data/file.txt", allowed_extensions=[".csv"])

    def test_directory_traversal_attempt(self):
        """Test detection of directory traversal attempts."""
        with pytest.raises(PathValidationError, match="directory traversal"):
            validate_file_path("../etc/passwd")

    def test_absolute_path_with_base_dir(self):
        """Test rejection of absolute paths when base_dir is specified."""
        with pytest.raises(PathValidationError, match="Absolute paths not allowed"):
            validate_file_path("/absolute/path", base_dir="/base")

    def test_path_outside_base_directory(self):
        """Test that paths outside base directory are rejected."""
        with pytest.raises(PathValidationError, match="directory traversal"):
            validate_file_path("../../../etc/passwd", base_dir="/safe/dir")

    def test_non_string_path(self):
        """Test handling of non-string path."""
        with pytest.raises(PathValidationError, match="Expected string path"):
            validate_file_path(123)


class TestValidateNumericBounds:
    """Test numeric bounds validation."""

    def test_valid_value_within_bounds(self):
        """Test valid value within bounds."""
        result = validate_numeric_bounds(5, 0, 10, "test_field")
        assert result == 5

    def test_value_at_minimum(self):
        """Test value at minimum bound."""
        result = validate_numeric_bounds(0, 0, 10, "test_field")
        assert result == 0

    def test_value_at_maximum(self):
        """Test value at maximum bound."""
        result = validate_numeric_bounds(10, 0, 10, "test_field")
        assert result == 10

    def test_value_below_minimum(self):
        """Test value below minimum bound."""
        with pytest.raises(DataValidationError, match="must be at least"):
            validate_numeric_bounds(-1, 0, 10, "test_field")

    def test_value_above_maximum(self):
        """Test value above maximum bound."""
        with pytest.raises(DataValidationError, match="must be at most"):
            validate_numeric_bounds(11, 0, 10, "test_field")

    def test_non_numeric_value(self):
        """Test handling of non-numeric value."""
        with pytest.raises(DataValidationError, match="must be numeric"):
            validate_numeric_bounds("not a number", 0, 10, "test_field")

    def test_nan_value(self):
        """Test handling of NaN values."""
        with pytest.raises(DataValidationError, match="cannot be NaN"):
            validate_numeric_bounds(float("nan"), 0, 10, "test_field")

    def test_infinite_value(self):
        """Test handling of infinite values."""
        with pytest.raises(DataValidationError, match="cannot be NaN or infinite"):
            validate_numeric_bounds(float("inf"), 0, 10, "test_field")


class TestValidatePercentage:
    """Test percentage validation."""

    def test_valid_percentage(self):
        """Test valid percentage value."""
        result = validate_percentage(50.0, "test_field")
        assert result == 50.0

    def test_percentage_at_bounds(self):
        """Test percentage at boundary values."""
        assert validate_percentage(0.0, "test_field") == 0.0
        assert validate_percentage(100.0, "test_field") == 100.0

    def test_negative_percentage(self):
        """Test rejection of negative percentage."""
        with pytest.raises(DataValidationError, match="must be at least"):
            validate_percentage(-1.0, "test_field")

    def test_percentage_above_100(self):
        """Test rejection of percentage above 100."""
        with pytest.raises(DataValidationError, match="must be at most"):
            validate_percentage(101.0, "test_field")


class TestValidateYieldRate:
    """Test yield rate validation."""

    def test_valid_yield_rate(self):
        """Test valid yield rate."""
        result = validate_yield_rate(5.0, "test_field")
        assert result == 5.0

    def test_yield_rate_at_bounds(self):
        """Test yield rate at boundary values."""
        assert validate_yield_rate(0.0, "test_field") == 0.0
        assert validate_yield_rate(100.0, "test_field") == 100.0

    def test_negative_yield_rate(self):
        """Test rejection of negative yield rate."""
        with pytest.raises(DataValidationError, match="must be at least"):
            validate_yield_rate(-1.0, "test_field")


class TestValidateCagr:
    """Test CAGR validation."""

    def test_valid_cagr(self):
        """Test valid CAGR value."""
        result = validate_cagr(10.0, "test_field")
        assert result == 10.0

    def test_cagr_at_bounds(self):
        """Test CAGR at boundary values."""
        assert validate_cagr(-50.0, "test_field") == -50.0
        assert validate_cagr(100.0, "test_field") == 100.0

    def test_cagr_below_minimum(self):
        """Test rejection of CAGR below minimum."""
        with pytest.raises(DataValidationError, match="must be at least"):
            validate_cagr(-51.0, "test_field")

    def test_cagr_above_maximum(self):
        """Test rejection of CAGR above maximum."""
        with pytest.raises(DataValidationError, match="must be at most"):
            validate_cagr(101.0, "test_field")


class TestValidatePortfolioSize:
    """Test portfolio size validation."""

    def test_valid_portfolio_size(self):
        """Test valid portfolio size."""
        result = validate_portfolio_size(10, "test_field")
        assert result == 10

    def test_portfolio_size_at_bounds(self):
        """Test portfolio size at boundary values."""
        assert validate_portfolio_size(1, "test_field") == 1
        assert validate_portfolio_size(100, "test_field") == 100

    def test_portfolio_size_below_minimum(self):
        """Test rejection of portfolio size below minimum."""
        with pytest.raises(DataValidationError, match="must be at least"):
            validate_portfolio_size(0, "test_field")

    def test_portfolio_size_above_maximum(self):
        """Test rejection of portfolio size above maximum."""
        with pytest.raises(DataValidationError, match="must be at most"):
            validate_portfolio_size(101, "test_field")


class TestValidateWeightingMethod:
    """Test weighting method validation."""

    def test_valid_weighting_methods(self):
        """Test all valid weighting methods."""
        valid_methods = ["equal", "score", "market_cap", "dividend_weight"]
        for method in valid_methods:
            result = validate_weighting_method(method, "test_field")
            assert result == method

    def test_case_insensitive_validation(self):
        """Test that validation is case insensitive."""
        result = validate_weighting_method("EQUAL", "test_field")
        assert result == "equal"

    def test_invalid_weighting_method(self):
        """Test rejection of invalid weighting method."""
        with pytest.raises(DataValidationError, match="must be one of"):
            validate_weighting_method("invalid", "test_field")

    def test_non_string_weighting_method(self):
        """Test handling of non-string weighting method."""
        with pytest.raises(DataValidationError, match="must be a string"):
            validate_weighting_method(123, "test_field")


class TestSanitizeForLogging:
    """Test logging sanitization functionality."""

    def test_string_sanitization(self):
        """Test string sanitization for logging."""
        result = sanitize_for_logging("Hello, World!")
        assert result == "Hello, World!"

    def test_none_value(self):
        """Test handling of None value."""
        result = sanitize_for_logging(None)
        assert result == "None"

    def test_numeric_value(self):
        """Test handling of numeric value."""
        result = sanitize_for_logging(123)
        assert result == "123"

    def test_long_string_truncation(self):
        """Test truncation of long strings."""
        long_string = "a" * 300
        result = sanitize_for_logging(long_string, max_length=200)
        assert len(result) == 200
        assert result.endswith("...")

    def test_dangerous_content_removal(self):
        """Test removal of dangerous content for logging."""
        dangerous_string = "Hello<script>alert('xss')</script>World"
        result = sanitize_for_logging(dangerous_string)
        # Should be sanitized and safe for logging
        assert "<script>" not in result


class TestValidateUrl:
    """Test URL validation functionality."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        result = validate_url("http://example.com")
        assert result == "http://example.com"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        result = validate_url("https://example.com", allowed_schemes=["https"])
        assert result == "https://example.com"

    def test_url_without_scheme(self):
        """Test rejection of URL without scheme."""
        with pytest.raises(URLValidationError, match="must include a scheme"):
            validate_url("example.com")

    def test_disallowed_scheme(self):
        """Test rejection of disallowed URL scheme."""
        with pytest.raises(URLValidationError, match="not allowed"):
            validate_url("ftp://example.com", allowed_schemes=["http", "https"])

    def test_non_string_url(self):
        """Test handling of non-string URL."""
        with pytest.raises(URLValidationError, match="Expected string URL"):
            validate_url(123)

    def test_invalid_url_format(self):
        """Test handling of invalid URL format."""
        with pytest.raises(URLValidationError, match="must include a scheme"):
            validate_url("not a url")


class TestValidateCsvData:
    """Test CSV data validation functionality."""

    def test_valid_dataframe(self):
        """Test valid DataFrame."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        result = validate_csv_data(df)
        assert result.equals(df)

    def test_empty_dataframe(self):
        """Test rejection of empty DataFrame."""
        df = pd.DataFrame()
        with pytest.raises(DataFrameValidationError, match="DataFrame is empty"):
            validate_csv_data(df)

    def test_too_many_rows(self):
        """Test rejection of DataFrame with too many rows."""
        df = pd.DataFrame({"col1": range(10001)})
        with pytest.raises(DataFrameValidationError, match="too many rows"):
            validate_csv_data(df, max_rows=10000)

    def test_missing_required_columns(self):
        """Test rejection of DataFrame missing required columns."""
        df = pd.DataFrame({"col1": [1, 2]})
        with pytest.raises(DataFrameValidationError, match="Missing required columns"):
            validate_csv_data(df, required_columns=["col1", "col2"])

    def test_non_dataframe_input(self):
        """Test handling of non-DataFrame input."""
        with pytest.raises(DataFrameValidationError, match="Expected DataFrame"):
            validate_csv_data("not a dataframe")

    def test_suspicious_column_names(self):
        """Test rejection of suspicious column names."""
        df = pd.DataFrame({"<script>": [1, 2]})
        with pytest.raises(DataFrameValidationError, match="invalid characters"):
            validate_csv_data(df)


class TestValidateUuidFormat:
    """Test UUID format validation."""

    def test_valid_uuid(self):
        """Test valid UUID format."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid_format(valid_uuid)
        assert result == valid_uuid

    def test_invalid_uuid_format(self):
        """Test invalid UUID format."""
        invalid_uuid = "not-a-uuid"
        with pytest.raises(DataValidationError) as exc_info:
            validate_uuid_format(invalid_uuid)
        assert "must be a valid UUID format" in str(exc_info.value)

    def test_non_string_uuid(self):
        """Test non-string UUID input."""
        with pytest.raises(DataValidationError) as exc_info:
            validate_uuid_format(123)
        assert "must be a string" in str(exc_info.value)

    def test_uuid_too_long(self):
        """Test UUID that's too long after sanitization."""
        long_uuid = "a" * 100
        with pytest.raises(SecurityValidationError):
            validate_uuid_format(long_uuid)


class TestValidateUserId:
    """Test user ID validation."""

    def test_valid_user_id(self):
        """Test valid user ID format."""
        valid_ids = ["user123", "user_123", "user-123", "USER123"]
        for user_id in valid_ids:
            result = validate_user_id(user_id)
            assert result == user_id  # Function preserves case

    def test_invalid_user_id_characters(self):
        """Test user ID with invalid characters."""
        invalid_ids = ["user@123", "user#123", "user 123", "user.123"]
        for user_id in invalid_ids:
            with pytest.raises(DataValidationError) as exc_info:
                validate_user_id(user_id)
            assert "must contain only alphanumeric characters" in str(exc_info.value)

    def test_non_string_user_id(self):
        """Test non-string user ID input."""
        with pytest.raises(DataValidationError) as exc_info:
            validate_user_id(123)
        assert "must be a string" in str(exc_info.value)

    def test_user_id_too_long(self):
        """Test user ID that's too long."""
        long_user_id = "a" * 200
        with pytest.raises(SecurityValidationError):
            validate_user_id(long_user_id)
