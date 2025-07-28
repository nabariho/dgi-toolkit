"""Observability and monitoring module for DGI Toolkit API.

This module provides comprehensive observability features including:
- OpenTelemetry integration for distributed tracing
- Prometheus metrics collection
- Structured logging for business events
- Performance monitoring and alerting
"""

import logging
import time
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
    """Manages observability features including metrics, tracing, and logging."""

    def __init__(self):
        """Initialize the observability manager."""
        self.settings = get_settings()
        self.meter: Meter | None = None
        self.tracer: trace.Tracer | None = None
        self._initialize_metrics()
        self._initialize_tracing()

    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metrics collection."""
        global _metrics_initialized
        if _metrics_initialized:
            return

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available - metrics disabled")
            return

        try:
            # Create meter provider (simplified without Prometheus exporter for now)
            meter_provider = MeterProvider()
            self.meter = meter_provider.get_meter("dgi-toolkit")

            # Define metrics
            self.request_counter = self.meter.create_counter(
                name="dgi_requests_total",
                description="Total number of API requests",
                unit="1",
            )

            self.request_duration = self.meter.create_histogram(
                name="dgi_request_duration_seconds",
                description="Request duration in seconds",
                unit="s",
            )

            self.screening_counter = self.meter.create_counter(
                name="dgi_screening_operations_total",
                description="Total number of stock screening operations",
                unit="1",
            )

            self.screening_duration = self.meter.create_histogram(
                name="dgi_screening_duration_seconds",
                description="Stock screening duration in seconds",
                unit="s",
            )

            self.cache_hits = self.meter.create_counter(
                name="dgi_cache_hits_total",
                description="Total number of cache hits",
                unit="1",
            )

            self.cache_misses = self.meter.create_counter(
                name="dgi_cache_misses_total",
                description="Total number of cache misses",
                unit="1",
            )

            self.error_counter = self.meter.create_counter(
                name="dgi_errors_total",
                description="Total number of errors",
                unit="1",
            )

            logger.info("Metrics initialized successfully")
            _metrics_initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")

    def _initialize_tracing(self) -> None:
        """Initialize OpenTelemetry tracing."""
        global _tracing_initialized
        if _tracing_initialized:
            return

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available - tracing disabled")
            return

        try:
            # Create tracer provider
            tracer_provider = TracerProvider()

            # Add console exporter for development
            if self.settings.debug:
                console_exporter = ConsoleSpanExporter()
                tracer_provider.add_span_processor(
                    SimpleSpanProcessor(console_exporter)
                )

            # Set the tracer provider
            trace.set_tracer_provider(tracer_provider)
            self.tracer = trace.get_tracer("dgi-toolkit")

            logger.info("Tracing initialized successfully")
            _tracing_initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")

    def record_request(
        self, method: str, path: str, status_code: int, duration: float
    ) -> None:
        """Record request metrics."""
        if not self.meter:
            return

        try:
            # Record request counter
            self.request_counter.add(
                1,
                {
                    "method": method,
                    "path": path,
                    "status_code": str(status_code),
                },
            )

            # Record request duration
            self.request_duration.record(
                duration,
                {
                    "method": method,
                    "path": path,
                    "status_code": str(status_code),
                },
            )

        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")

    def record_screening_operation(
        self, stocks_returned: int, duration: float, filters_applied: dict[str, Any]
    ) -> None:
        """Record stock screening operation metrics."""
        if not self.meter:
            return

        try:
            # Record screening counter
            self.screening_counter.add(
                1,
                {
                    "stocks_returned": str(stocks_returned),
                    "filters_applied": str(len(filters_applied)),
                },
            )

            # Record screening duration
            self.screening_duration.record(
                duration,
                {
                    "stocks_returned": str(stocks_returned),
                    "filters_applied": str(len(filters_applied)),
                },
            )

        except Exception as e:
            logger.error(f"Failed to record screening metrics: {e}")

    def record_cache_operation(self, hit: bool, cache_key: str) -> None:
        """Record cache operation metrics."""
        if not self.meter:
            return

        try:
            if hit:
                self.cache_hits.add(1, {"cache_key": cache_key})
            else:
                self.cache_misses.add(1, {"cache_key": cache_key})

        except Exception as e:
            logger.error(f"Failed to record cache metrics: {e}")

    def record_error(self, error_type: str, error_message: str, endpoint: str) -> None:
        """Record error metrics."""
        if not self.meter:
            return

        try:
            self.error_counter.add(
                1,
                {
                    "error_type": error_type,
                    "endpoint": endpoint,
                },
            )

        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}")

    @asynccontextmanager
    async def trace_operation(
        self, operation_name: str, attributes: dict[str, Any] | None = None
    ):
        """Context manager for tracing operations."""
        if not self.tracer:
            yield
            return

        try:
            with self.tracer.start_as_current_span(
                operation_name, attributes=attributes or {}
            ) as span:
                yield span
        except Exception as e:
            logger.error(f"Failed to trace operation {operation_name}: {e}")
            yield None

    def log_business_event(
        self, event_type: str, event_data: dict[str, Any], user_id: str | None = None
    ) -> None:
        """Log structured business events."""
        log_data = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": time.time(),
            "service": "dgi-toolkit",
        }

        if user_id:
            log_data["user_id"] = user_id

        logger.info(f"Business event: {event_type}", extra=log_data)


# Global observability manager instance
observability = ObservabilityManager()


def get_observability_manager() -> ObservabilityManager:
    """Get the global observability manager instance."""
    return observability


def instrument_fastapi(app) -> None:
    """Instrument FastAPI application with OpenTelemetry."""
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not available - FastAPI instrumentation skipped")
        return

    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        # Instrument HTTPX client
        HTTPXClientInstrumentor().instrument()

        logger.info("FastAPI instrumentation completed")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def get_metrics() -> str:
    """Get Prometheus metrics in text format."""
    if not PROMETHEUS_AVAILABLE:
        return "# Prometheus metrics not available - prometheus-client not installed"

    try:
        return generate_latest().decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return ""


# Prometheus metrics for backward compatibility (only if available)
if PROMETHEUS_AVAILABLE:
    REQUEST_COUNTER = PrometheusCounter(
        "dgi_requests_total",
        "Total number of API requests",
        ["method", "path", "status_code"],
    )

    REQUEST_DURATION = PrometheusHistogram(
        "dgi_request_duration_seconds",
        "Request duration in seconds",
        ["method", "path", "status_code"],
    )

    SCREENING_COUNTER = PrometheusCounter(
        "dgi_screening_operations_total",
        "Total number of stock screening operations",
        ["stocks_returned", "filters_applied"],
    )

    SCREENING_DURATION = PrometheusHistogram(
        "dgi_screening_duration_seconds",
        "Stock screening duration in seconds",
        ["stocks_returned", "filters_applied"],
    )

    CACHE_HITS = PrometheusCounter(
        "dgi_cache_hits_total", "Total number of cache hits", ["cache_key"]
    )

    CACHE_MISSES = PrometheusCounter(
        "dgi_cache_misses_total", "Total number of cache misses", ["cache_key"]
    )

    ERROR_COUNTER = PrometheusCounter(
        "dgi_errors_total", "Total number of errors", ["error_type", "endpoint"]
    )

    # Service information
    SERVICE_INFO = Info("dgi_service", "DGI Toolkit service information")
    SERVICE_INFO.info(
        {
            "version": "1.0.0",
            "service": "dgi-toolkit",
            "environment": get_settings().environment,
        }
    )
else:
    # Dummy metrics for when Prometheus is not available
    REQUEST_COUNTER = None
    REQUEST_DURATION = None
    SCREENING_COUNTER = None
    SCREENING_DURATION = None
    CACHE_HITS = None
    CACHE_MISSES = None
    ERROR_COUNTER = None
    SERVICE_INFO = None
