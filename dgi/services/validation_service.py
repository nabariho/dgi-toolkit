"""Validation service for business logic separation."""

import logging
import os

logger = logging.getLogger(__name__)


class ValidationService:
    """Service class for validation business logic."""

    @staticmethod
    def validate_yield_rate(yield_rate: float, field_name: str = "yield_rate") -> float:
        """Validate dividend yield rate using business rules (0-100%)."""
        if not isinstance(yield_rate, (int, float)):
            raise ValueError(f"{field_name} must be a number")

        if yield_rate < 0:
            raise ValueError(f"{field_name} must be non-negative")

        if yield_rate > 100:  # More than 100%
            raise ValueError(f"{field_name} cannot exceed 100%")

        return float(yield_rate)

    @staticmethod
    def validate_percentage(percentage: float, field_name: str = "percentage") -> float:
        """Validate percentage values using business rules."""
        if not isinstance(percentage, (int, float)):
            raise ValueError(f"{field_name} must be a number")

        if percentage < 0:
            raise ValueError(f"{field_name} must be non-negative")

        if percentage > 100:
            raise ValueError(f"{field_name} cannot exceed 100%")

        return float(percentage)

    @staticmethod
    def validate_cagr(cagr: float, field_name: str = "cagr") -> float:
        """Validate CAGR values using business rules (-100% to 100%)."""
        if not isinstance(cagr, (int, float)):
            raise ValueError(f"{field_name} must be a number")

        if cagr < -100:  # Cannot lose more than 100%
            raise ValueError(f"{field_name} cannot be less than -100%")

        if cagr > 100:  # Unrealistic growth > 100%
            raise ValueError(f"{field_name} cannot exceed 100%")

        return float(cagr)

    @staticmethod
    def validate_portfolio_size(size: int, field_name: str = "portfolio_size") -> int:
        """Validate portfolio size using business rules."""
        if not isinstance(size, int):
            raise ValueError(f"{field_name} must be an integer")

        if size < 1:
            raise ValueError(f"{field_name} must be at least 1")

        if size > 100:  # Reasonable limit for portfolio size
            raise ValueError(f"{field_name} cannot exceed 100 stocks")

        return size

    @staticmethod
    def validate_weighting_method(weighting: str, field_name: str = "weighting") -> str:
        """Validate weighting method using business rules."""
        if not isinstance(weighting, str):
            raise ValueError(f"{field_name} must be a string")

        valid_methods = ["equal", "score"]
        if weighting.lower() not in valid_methods:
            raise ValueError(f"{field_name} must be one of: {', '.join(valid_methods)}")

        return weighting.lower()

    @staticmethod
    def validate_file_path(
        file_path: str,
        allowed_extensions: list[str] | None = None,
        field_name: str = "file_path",
    ) -> str:
        """Validate file path using business rules."""
        if not isinstance(file_path, str):
            raise ValueError(f"{field_name} must be a string")

        if not file_path.strip():
            raise ValueError(f"{field_name} cannot be empty")

        # Check file extension if specified
        if allowed_extensions:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                raise ValueError(
                    f"{field_name} must have one of these extensions: {', '.join(allowed_extensions)}"
                )

        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        # Check if it's actually a file
        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        return file_path

    @staticmethod
    def validate_uuid_format(uuid_str: str, field_name: str = "uuid") -> str:
        """Validate UUID format using business rules."""
        import uuid

        if not isinstance(uuid_str, str):
            raise ValueError(f"{field_name} must be a string")

        try:
            uuid.UUID(uuid_str)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {uuid_str}")

        return uuid_str

    @staticmethod
    def sanitize_for_logging(value: str) -> str:
        """Sanitize values for logging to prevent sensitive data exposure."""
        if not isinstance(value, str):
            return str(value)

        # Remove potential sensitive patterns
        sensitive_patterns = ["password", "secret", "key", "token", "auth"]

        sanitized = value
        for pattern in sensitive_patterns:
            if pattern.lower() in sanitized.lower():
                sanitized = sanitized.replace(pattern, "[REDACTED]")

        return sanitized
