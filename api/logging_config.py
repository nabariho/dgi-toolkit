"""Logging configuration for DGI Toolkit API."""

import json
import logging
import sys
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class JSONFormatter(logging.Formatter):
    """Structured JSON logging formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to capture request context for logging."""

    async def dispatch(self, request: Request, call_next):
        """Add request context to logging."""
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", f"req-{id(request)}")

        # Add to request state
        request.state.correlation_id = correlation_id

        # Add correlation ID to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    include_correlation_id: bool = True,
) -> None:
    """Set up logging configuration for the API.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ("json" or "text")
        include_correlation_id: Whether to include correlation IDs in logs
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Set formatter based on type
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    correlation_id: str | None = None,
    **kwargs: Any,
) -> None:
    """Log message with additional context.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        correlation_id: Request correlation ID
        **kwargs: Additional context fields
    """
    extra_fields = kwargs.copy()
    if correlation_id:
        extra_fields["correlation_id"] = correlation_id

    # Create a new record with extra fields
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None,
    )
    record.extra_fields = extra_fields

    logger.handle(record)
