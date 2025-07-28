"""Observability and monitoring module for DGI Toolkit API.

This module provides comprehensive observability features including:
- OpenTelemetry integration for distributed tracing
- Prometheus metrics collection with consistent naming
- Structured logging for all business events
- Performance monitoring and alerting
- Distributed tracing correlation IDs
- Observability standards and patterns
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

# Try to import OpenTelemetry dependencies, but handle gracefully if not available
try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Note: logger not available yet, will be set up later

# Type checking imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opentelemetry.metrics import Meter

# Try to import Prometheus dependencies
try:
    from prometheus_client import Counter as PrometheusCounter
    from prometheus_client import Histogram as PrometheusHistogram
    from prometheus_client import Info, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Note: logger not available yet, will be set up later

from api.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Global variables for metrics and tracing
_metrics_initialized = False
_tracing_initialized = False


class ObservabilityManager:
    """Manages observability features including metrics, tracing, and logging.

    Provides comprehensive observability capabilities with structured logging,
    consistent metric naming, and distributed tracing correlation.
    """

    def __init__(self):
        """Initialize the observability manager."""
        self.settings = get_settings()
        self.meter: Meter | None = None
        self.tracer: trace.Tracer | None = None
        self._correlation_id: str | None = None
        self._initialize_metrics()
        self._initialize_tracing()

    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metrics collection with consistent naming."""
        global _metrics_initialized
        if _metrics_initialized:
            return

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available - metrics disabled")
            return

        try:
            # Create meter provider (simplified without Prometheus exporter for now)
            meter_provider = MeterProvider()
            self.meter = meter_provider.get_meter("dgi_toolkit")

            # Define metrics with consistent naming convention
            self.request_counter = self.meter.create_counter(
                name="dgi_api_requests_total",
                description="Total number of API requests by endpoint and status",
                unit="1",
            )

            self.request_duration = self.meter.create_histogram(
                name="dgi_api_request_duration_seconds",
                description="Request duration in seconds by endpoint",
                unit="s",
            )

            self.screening_operations = self.meter.create_counter(
                name="dgi_screening_operations_total",
                description="Total number of stock screening operations",
                unit="1",
            )

            self.cache_operations = self.meter.create_counter(
                name="dgi_cache_operations_total",
                description="Total number of cache operations by type",
                unit="1",
            )

            self.error_counter = self.meter.create_counter(
                name="dgi_errors_total",
                description="Total number of errors by type and endpoint",
                unit="1",
            )

            self.job_operations = self.meter.create_counter(
                name="dgi_job_operations_total",
                description="Total number of background job operations",
                unit="1",
            )

            _metrics_initialized = True
            logger.info("Metrics initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")

    def _initialize_tracing(self) -> None:
        """Initialize OpenTelemetry tracing with distributed correlation."""
        global _tracing_initialized
        if _tracing_initialized:
            return

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available - tracing disabled")
            return

        try:
            # Create tracer provider
            tracer_provider = TracerProvider()
            tracer_provider.add_span_processor(
                SimpleSpanProcessor(ConsoleSpanExporter())
            )
            self.tracer = tracer_provider.get_tracer("dgi_toolkit")

            _tracing_initialized = True
            logger.info("Tracing initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for distributed tracing."""
        self._correlation_id = correlation_id

    def get_correlation_id(self) -> str | None:
        """Get current correlation ID."""
        return self._correlation_id

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        correlation_id = f"req-{uuid.uuid4().hex[:8]}"
        self._correlation_id = correlation_id
        return correlation_id

    def record_request(
        self, method: str, path: str, status_code: int, duration: float
    ) -> None:
        """Record API request metrics with structured logging."""
        try:
            # Record metrics
            if self.meter:
                self.request_counter.add(
                    1,
                    {
                        "method": method,
                        "path": path,
                        "status_code": str(status_code),
                        "correlation_id": self._correlation_id or "unknown",
                    },
                )

                self.request_duration.record(
                    duration,
                    {
                        "method": method,
                        "path": path,
                        "status_code": str(status_code),
                        "correlation_id": self._correlation_id or "unknown",
                    },
                )

            # Structured logging
            logger.info(
                "API request completed",
                extra={
                    "event_type": "api_request",
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration * 1000,
                    "correlation_id": self._correlation_id,
                },
            )

        except Exception as e:
            logger.error(f"Error recording request metrics: {e}")

    def record_screening_operation(
        self, stocks_returned: int, duration: float, filters_applied: dict[str, Any]
    ) -> None:
        """Record stock screening operation with structured logging."""
        try:
            # Record metrics
            if self.meter:
                self.screening_operations.add(
                    1,
                    {
                        "stocks_returned": str(stocks_returned),
                        "filters_applied": str(len(filters_applied)),
                        "correlation_id": self._correlation_id or "unknown",
                    },
                )

            # Structured logging
            logger.info(
                "Stock screening operation completed",
                extra={
                    "event_type": "screening_operation",
                    "stocks_returned": stocks_returned,
                    "duration_ms": duration * 1000,
                    "filters_applied": filters_applied,
                    "correlation_id": self._correlation_id,
                },
            )

        except Exception as e:
            logger.error(f"Error recording screening metrics: {e}")

    def record_cache_operation(
        self, hit: bool, cache_key: str, cache_type: str = "default"
    ) -> None:
        """Record cache operation with structured logging."""
        try:
            # Record metrics
            if self.meter:
                self.cache_operations.add(
                    1,
                    {
                        "cache_type": cache_type,
                        "hit": str(hit).lower(),
                        "correlation_id": self._correlation_id or "unknown",
                    },
                )

            # Structured logging
            logger.info(
                "Cache operation",
                extra={
                    "event_type": "cache_operation",
                    "cache_type": cache_type,
                    "hit": hit,
                    "cache_key": cache_key,
                    "correlation_id": self._correlation_id,
                },
            )

        except Exception as e:
            logger.error(f"Error recording cache metrics: {e}")

    def record_error(self, error_type: str, error_message: str, endpoint: str) -> None:
        """Record error with structured logging."""
        try:
            # Record metrics
            if self.meter:
                self.error_counter.add(
                    1,
                    {
                        "error_type": error_type,
                        "endpoint": endpoint,
                        "correlation_id": self._correlation_id or "unknown",
                    },
                )

            # Structured logging
            logger.error(
                "API error occurred",
                extra={
                    "event_type": "api_error",
                    "error_type": error_type,
                    "error_message": error_message,
                    "endpoint": endpoint,
                    "correlation_id": self._correlation_id,
                },
            )

        except Exception as e:
            logger.error(f"Error recording error metrics: {e}")

    def record_job_operation(self, job_status: str, duration: float = 0.0) -> None:
        """Record background job operation with structured logging."""
        try:
            # Record metrics
            if self.meter:
                self.job_operations.add(
                    1,
                    {
                        "job_status": job_status,
                        "correlation_id": self._correlation_id or "unknown",
                    },
                )

            # Structured logging
            logger.info(
                "Background job operation",
                extra={
                    "event_type": "job_operation",
                    "job_status": job_status,
                    "duration_ms": duration * 1000,
                    "correlation_id": self._correlation_id,
                },
            )

        except Exception as e:
            logger.error(f"Error recording job metrics: {e}")

    @asynccontextmanager
    async def trace_operation(
        self, operation_name: str, attributes: dict[str, Any] | None = None
    ):
        """Async context manager for tracing operations."""
        if not self.tracer:
            # Provide dummy span if tracing is not available
            class DummySpan:
                def set_attribute(self, key, value):
                    pass

                def set_attributes(self, attributes):
                    pass

                def add_event(self, name, attributes=None):
                    pass

                def record_exception(self, exception):
                    pass

                def set_status(self, status):
                    pass

            yield DummySpan()
            return

        try:
            with self.tracer.start_as_current_span(operation_name) as span:
                # Add correlation ID to span
                if self._correlation_id:
                    span.set_attribute("correlation_id", self._correlation_id)

                # Add custom attributes
                if attributes:
                    span.set_attributes(attributes)

                # Structured logging for operation start
                logger.info(
                    f"Operation started: {operation_name}",
                    extra={
                        "event_type": "operation_start",
                        "operation_name": operation_name,
                        "attributes": attributes,
                        "correlation_id": self._correlation_id,
                    },
                )

                yield span

                # Structured logging for operation completion
                logger.info(
                    f"Operation completed: {operation_name}",
                    extra={
                        "event_type": "operation_complete",
                        "operation_name": operation_name,
                        "correlation_id": self._correlation_id,
                    },
                )

        except Exception as e:
            # Record exception in span
            if self.tracer:
                with self.tracer.start_as_current_span(
                    f"{operation_name}_error"
                ) as error_span:
                    error_span.record_exception(e)
                    error_span.set_status(trace.Status(trace.StatusCode.ERROR))

            # Structured logging for operation error
            logger.error(
                f"Operation failed: {operation_name}",
                extra={
                    "event_type": "operation_error",
                    "operation_name": operation_name,
                    "error": str(e),
                    "correlation_id": self._correlation_id,
                },
            )
            raise

    async def log_business_event(
        self, event_type: str, event_data: dict[str, Any], user_id: str | None = None
    ) -> None:
        """Log business event with structured logging and correlation."""
        try:
            log_data = {
                "event_type": event_type,
                "event_data": event_data,
                "correlation_id": self._correlation_id,
                "timestamp": time.time(),
            }

            if user_id:
                log_data["user_id"] = user_id

            logger.info(
                f"Business event: {event_type}",
                extra=log_data,
            )

        except Exception as e:
            logger.error(f"Error logging business event: {e}")

    def log_performance_event(
        self, operation: str, duration: float, metadata: dict[str, Any] | None = None
    ) -> None:
        """Log performance event with structured logging."""
        try:
            log_data = {
                "event_type": "performance_event",
                "operation": operation,
                "duration_ms": duration * 1000,
                "correlation_id": self._correlation_id,
            }

            if metadata:
                log_data["metadata"] = metadata

            logger.info(
                f"Performance event: {operation}",
                extra=log_data,
            )

        except Exception as e:
            logger.error(f"Error logging performance event: {e}")

    def log_security_event(
        self, event_type: str, details: dict[str, Any], severity: str = "info"
    ) -> None:
        """Log security event with structured logging."""
        try:
            log_data = {
                "event_type": "security_event",
                "security_event_type": event_type,
                "severity": severity,
                "details": details,
                "correlation_id": self._correlation_id,
            }

            if severity == "error":
                logger.error(f"Security event: {event_type}", extra=log_data)
            elif severity == "warning":
                logger.warning(f"Security event: {event_type}", extra=log_data)
            else:
                logger.info(f"Security event: {event_type}", extra=log_data)

        except Exception as e:
            logger.error(f"Error logging security event: {e}")


# Global observability manager instance
_observability_manager: ObservabilityManager | None = None


def get_observability_manager() -> ObservabilityManager:
    """Get the global observability manager instance."""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = ObservabilityManager()
    return _observability_manager


def instrument_fastapi(app) -> None:
    """Instrument FastAPI application with observability."""
    try:
        if OPENTELEMETRY_AVAILABLE:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation enabled")
        else:
            logger.warning(
                "OpenTelemetry not available - FastAPI instrumentation disabled"
            )

    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def get_metrics() -> str:
    """Get Prometheus metrics in text format."""
    try:
        if PROMETHEUS_AVAILABLE:
            return generate_latest().decode("utf-8")
        else:
            return "# Prometheus client not available\n"
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return f"# Error generating metrics: {e}\n"
