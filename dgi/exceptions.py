"""Unified exception hierarchy for DGI Toolkit domain errors.

This module provides a comprehensive set of domain-specific exceptions
that should be used throughout the DGI toolkit instead of generic Python exceptions.
"""

from typing import Any


class DGIException(Exception):
    """Base exception for all DGI Toolkit domain errors.

    All domain-specific exceptions should inherit from this class
    to ensure consistent error handling and identification.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize DGI exception.

        Args:
            message: Human-readable error message
            details: Additional error context and details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Data and Validation Exceptions
class DataValidationError(DGIException):
    """Raised when data validation fails in the DGI toolkit."""

    def __init__(
        self, message: str, field: str | None = None, value: Any = None
    ) -> None:
        """Initialize data validation error.

        Args:
            message: Validation error message
            field: Name of the field that failed validation
            value: Value that failed validation
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)


class SecurityValidationError(DataValidationError):
    """Raised when security validation fails (input sanitization, etc.)."""



class PathValidationError(DataValidationError):
    """Raised when file path validation fails."""



class URLValidationError(DataValidationError):
    """Raised when URL validation fails."""



class DataFrameValidationError(DataValidationError):
    """Raised when DataFrame validation fails."""



# Screening and Business Logic Exceptions
class ScreeningError(DGIException):
    """Raised when stock screening process fails."""

    def __init__(self, message: str, operation: str | None = None) -> None:
        """Initialize screening error.

        Args:
            message: Error message
            operation: Name of the screening operation that failed
        """
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class FilterError(ScreeningError):
    """Raised when filtering operations fail."""



class ScoringError(ScreeningError):
    """Raised when scoring calculations fail."""



class PortfolioError(DGIException):
    """Raised when portfolio operations fail."""

    def __init__(self, message: str, portfolio_id: str | None = None) -> None:
        """Initialize portfolio error.

        Args:
            message: Error message
            portfolio_id: ID of the portfolio that caused the error
        """
        details = {}
        if portfolio_id:
            details["portfolio_id"] = portfolio_id
        super().__init__(message, details)


# Data Repository Exceptions
class RepositoryError(DGIException):
    """Raised when data repository operations fail."""

    def __init__(
        self, message: str, repository: str | None = None, operation: str | None = None
    ) -> None:
        """Initialize repository error.

        Args:
            message: Error message
            repository: Name of the repository that failed
            operation: Operation that failed (read, write, etc.)
        """
        details = {}
        if repository:
            details["repository"] = repository
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class DataNotFoundError(RepositoryError):
    """Raised when requested data is not found in repository."""



class DataCorruptionError(RepositoryError):
    """Raised when data is corrupted or in unexpected format."""



class DataAccessError(RepositoryError):
    """Raised when data access is denied or fails."""



# Configuration and System Exceptions
class ConfigurationError(DGIException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        """Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details)


class FactoryError(DGIException):
    """Raised when factory operations fail."""

    def __init__(self, message: str, factory_name: str | None = None) -> None:
        """Initialize factory error.

        Args:
            message: Error message
            factory_name: Name of the factory that failed
        """
        details = {}
        if factory_name:
            details["factory_name"] = factory_name
        super().__init__(message, details)


class ServiceError(DGIException):
    """Raised when service layer operations fail."""

    def __init__(
        self, message: str, service: str | None = None, operation: str | None = None
    ) -> None:
        """Initialize service error.

        Args:
            message: Error message
            service: Name of the service that failed
            operation: Operation that failed
        """
        details = {}
        if service:
            details["service"] = service
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


# CLI and User Interface Exceptions
class CLIError(DGIException):
    """Raised when CLI operations fail."""

    def __init__(self, message: str, command: str | None = None) -> None:
        """Initialize CLI error.

        Args:
            message: Error message
            command: Command that failed
        """
        details = {}
        if command:
            details["command"] = command
        super().__init__(message, details)


class UserInputError(CLIError):
    """Raised when user input is invalid."""



# Performance and Resource Exceptions
class PerformanceError(DGIException):
    """Raised when performance thresholds are exceeded."""

    def __init__(
        self, message: str, metric: str | None = None, threshold: Any = None
    ) -> None:
        """Initialize performance error.

        Args:
            message: Error message
            metric: Performance metric that exceeded threshold
            threshold: Threshold value that was exceeded
        """
        details = {}
        if metric:
            details["metric"] = metric
        if threshold is not None:
            details["threshold"] = threshold
        super().__init__(message, details)


class ResourceError(DGIException):
    """Raised when resource limits are exceeded."""

    def __init__(
        self, message: str, resource_type: str | None = None, limit: Any = None
    ) -> None:
        """Initialize resource error.

        Args:
            message: Error message
            resource_type: Type of resource that exceeded limit
            limit: Limit value that was exceeded
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if limit is not None:
            details["limit"] = limit
        super().__init__(message, details)


# Legacy compatibility - keep existing exception for backward compatibility
# This should be deprecated in favor of the new hierarchy
class ValidationError(DataValidationError):
    """Legacy validation error - use DataValidationError instead."""

