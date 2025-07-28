"""Custom exception classes for DGI Toolkit API."""

from typing import Any


class APIException(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize API exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self._get_default_error_code(status_code)
        self.details = details or {}

    def _get_default_error_code(self, status_code: int) -> str:
        """Get default error code based on status code."""
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
        }
        return error_codes.get(status_code, "UNKNOWN_ERROR")

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details,
            }
        }


class ValidationError(APIException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error."""
        super().__init__(
            message, status_code=422, error_code="VALIDATION_ERROR", details=details
        )


class DataNotFoundError(APIException):
    """Raised when requested data is not found."""

    def __init__(
        self,
        message: str = "Data not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        """Initialize data not found error."""
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message, status_code=404, error_code="DATA_NOT_FOUND", details=details
        )


class RateLimitExceededError(APIException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        """Initialize rate limit error."""
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", details=details
        )


class DataProcessingError(APIException):
    """Raised when data processing fails."""

    def __init__(
        self,
        message: str = "Data processing error",
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize data processing error."""
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message,
            status_code=500,
            error_code="DATA_PROCESSING_ERROR",
            details=error_details,
        )


class ConfigurationError(APIException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str = "Configuration error",
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize configuration error."""
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key

        super().__init__(
            message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=error_details,
        )


class ServiceUnavailableError(APIException):
    """Raised when service is temporarily unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int | None = None,
    ) -> None:
        """Initialize service unavailable error."""
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message, status_code=503, error_code="SERVICE_UNAVAILABLE", details=details
        )


class BadRequestError(APIException):
    """Raised when request is malformed."""

    def __init__(
        self,
        message: str = "Bad request",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize bad request error."""
        super().__init__(
            message, status_code=400, error_code="BAD_REQUEST", details=details
        )


class UnauthorizedError(APIException):
    """Raised when authentication is required but not provided."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize unauthorized error."""
        super().__init__(
            message, status_code=401, error_code="UNAUTHORIZED", details=details
        )


class ForbiddenError(APIException):
    """Raised when access is forbidden."""

    def __init__(
        self,
        message: str = "Access forbidden",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize forbidden error."""
        super().__init__(
            message, status_code=403, error_code="FORBIDDEN", details=details
        )
