"""
Enhanced observability system for DGI Toolkit.

This module provides enterprise-grade observability features:
- Structured logging with correlation IDs
- Business metrics and KPI tracking
- Performance monitoring and alerting
- Request tracing across service boundaries
- Context-aware logging with business metadata
"""

import contextvars
import functools
import logging
import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

# Context variables for correlation tracking
correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)
user_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics for business monitoring."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(Enum):
    """Standard log levels for business operations."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class BusinessMetric:
    """Business metric definition with metadata."""

    name: str
    metric_type: MetricType
    description: str
    labels: list[str] = field(default_factory=list)
    unit: str | None = None
    threshold_warning: float | None = None
    threshold_critical: float | None = None


@dataclass
class OperationContext:
    """Context information for business operations."""

    operation_name: str
    correlation_id: str
    user_id: str | None = None
    request_id: str | None = None
    start_time: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "operation": self.operation_name,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "start_time": self.start_time.isoformat(),
            "metadata": self.metadata,
        }


class StructuredLogger:
    """Enhanced logger with structured logging and business context."""

    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self._setup_formatter()

    def _setup_formatter(self) -> None:
        """Set up structured logging formatter."""
        # Check if handlers are already configured to avoid duplicate setup
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
                '"message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", '
                '"line": "%(lineno)d"%(extras)s}'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _get_context_extras(
        self, extra: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Get current context information for logging."""
        context = {
            "correlation_id": correlation_id_var.get(),
            "user_id": user_id_var.get(),
            "request_id": request_id_var.get(),
        }

        # Filter out None values
        context = {k: v for k, v in context.items() if v is not None}

        if extra:
            context.update(extra)

        return context

    def _format_extras(self, extras: dict[str, Any]) -> str:
        """Format extra context for logging."""
        if not extras:
            return ""

        formatted_extras = []
        for key, value in extras.items():
            if isinstance(value, str):
                formatted_extras.append(f'"{key}": "{value}"')
            else:
                formatted_extras.append(f'"{key}": {value}')

        return ", " + ", ".join(formatted_extras)

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log info message with business context."""
        context = self._get_context_extras(extra)
        extras_str = self._format_extras(context)
        self.logger.info(message, extra={"extras": extras_str})

    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log warning message with business context."""
        context = self._get_context_extras(extra)
        extras_str = self._format_extras(context)
        self.logger.warning(message, extra={"extras": extras_str})

    def error(
        self,
        message: str,
        extra: dict[str, Any] | None = None,
        exc_info: bool = False,
    ) -> None:
        """Log error message with business context."""
        context = self._get_context_extras(extra)
        extras_str = self._format_extras(context)
        self.logger.error(message, extra={"extras": extras_str}, exc_info=exc_info)

    def debug(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log debug message with business context."""
        context = self._get_context_extras(extra)
        extras_str = self._format_extras(context)
        self.logger.debug(message, extra={"extras": extras_str})


class BusinessMetricsCollector:
    """Collect and track business metrics for monitoring."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._metrics: dict[str, Any] = {}
        self._business_metrics: dict[str, BusinessMetric] = {}
        self._init_default_metrics()

    def _init_default_metrics(self) -> None:
        """Initialize default business metrics."""
        # Screening operation metrics
        self.register_metric(
            BusinessMetric(
                name="screening_requests_total",
                metric_type=MetricType.COUNTER,
                description="Total number of screening requests",
                labels=["status", "user_type"],
            )
        )

        self.register_metric(
            BusinessMetric(
                name="screening_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="Time spent on screening operations",
                labels=["operation_type"],
                unit="seconds",
            )
        )

        self.register_metric(
            BusinessMetric(
                name="data_load_errors_total",
                metric_type=MetricType.COUNTER,
                description="Total number of data loading errors",
                labels=["error_type", "data_source"],
            )
        )

        self.register_metric(
            BusinessMetric(
                name="active_screening_operations",
                metric_type=MetricType.GAUGE,
                description="Number of currently active screening operations",
                threshold_warning=10.0,
                threshold_critical=20.0,
            )
        )

        self.register_metric(
            BusinessMetric(
                name="stocks_screened_total",
                metric_type=MetricType.COUNTER,
                description="Total number of stocks processed",
                labels=["criteria_type"],
            )
        )

    def register_metric(self, metric: BusinessMetric) -> None:
        """Register a new business metric."""
        self._business_metrics[metric.name] = metric

        # Create Prometheus metric
        if metric.metric_type == MetricType.COUNTER:
            self._metrics[metric.name] = Counter(
                metric.name, metric.description, metric.labels
            )
        elif metric.metric_type == MetricType.GAUGE:
            self._metrics[metric.name] = Gauge(
                metric.name, metric.description, metric.labels
            )
        elif metric.metric_type == MetricType.HISTOGRAM:
            self._metrics[metric.name] = Histogram(
                metric.name, metric.description, metric.labels
            )
        elif metric.metric_type == MetricType.SUMMARY:
            self._metrics[metric.name] = Summary(
                metric.name, metric.description, metric.labels
            )

        logger.info(f"Registered business metric: {metric.name}")

    def increment_counter(
        self,
        metric_name: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Increment a counter metric."""
        if metric_name in self._metrics:
            metric = self._metrics[metric_name]
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

    def set_gauge(
        self, metric_name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Set a gauge metric value."""
        if metric_name in self._metrics:
            metric = self._metrics[metric_name]
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

    def observe_histogram(
        self, metric_name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Observe a value in a histogram metric."""
        if metric_name in self._metrics:
            metric = self._metrics[metric_name]
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

    def get_metric_value(self, metric_name: str) -> float | None:
        """Get current value of a metric."""
        if metric_name in self._metrics:
            metric = self._metrics[metric_name]
            if hasattr(metric, "_value"):
                # Access the internal value safely
                value = getattr(metric._value, "_value", None)
                if isinstance(value, int | float):
                    return float(value)
        return None

    def check_thresholds(self) -> list[dict[str, Any]]:
        """Check metric thresholds and return alerts."""
        alerts = []

        for name, business_metric in self._business_metrics.items():
            if business_metric.threshold_warning or business_metric.threshold_critical:
                current_value = self.get_metric_value(name)
                if current_value is not None:
                    if (
                        business_metric.threshold_critical
                        and current_value >= business_metric.threshold_critical
                    ):
                        alerts.append(
                            {
                                "metric": name,
                                "level": "critical",
                                "value": current_value,
                                "threshold": business_metric.threshold_critical,
                                "description": business_metric.description,
                            }
                        )
                    elif (
                        business_metric.threshold_warning
                        and current_value >= business_metric.threshold_warning
                    ):
                        alerts.append(
                            {
                                "metric": name,
                                "level": "warning",
                                "value": current_value,
                                "threshold": business_metric.threshold_warning,
                                "description": business_metric.description,
                            }
                        )

        return alerts


class PerformanceMonitor:
    """Monitor performance of business operations."""

    def __init__(self, metrics_collector: BusinessMetricsCollector):
        """Initialize performance monitor."""
        self.metrics = metrics_collector
        self.structured_logger = StructuredLogger(__name__)

    @contextmanager
    def monitor_operation(self, operation_name: str, **metadata: Any) -> Any:
        """Context manager to monitor operation performance."""
        context = OperationContext(
            operation_name=operation_name,
            correlation_id=correlation_id_var.get() or str(uuid.uuid4()),
            user_id=user_id_var.get(),
            request_id=request_id_var.get(),
            metadata=metadata,
        )

        # Set correlation ID if not already set
        if not correlation_id_var.get():
            correlation_id_var.set(context.correlation_id)

        start_time = time.time()

        # Log operation start
        self.structured_logger.info(
            f"Operation started: {operation_name}",
            extra={"operation_type": "start", "operation_metadata": metadata},
        )

        # Increment active operations gauge
        self.metrics.set_gauge("active_screening_operations", 1.0)

        try:
            yield context

            # Operation succeeded
            duration = time.time() - start_time

            self.structured_logger.info(
                f"Operation completed: {operation_name}",
                extra={
                    "operation_type": "success",
                    "duration_seconds": duration,
                    "operation_metadata": metadata,
                },
            )

            # Record metrics
            self.metrics.observe_histogram(
                "screening_duration_seconds",
                duration,
                labels={"operation_type": operation_name},
            )
            self.metrics.increment_counter(
                "screening_requests_total",
                labels={
                    "status": "success",
                    "user_type": context.user_id or "anonymous",
                },
            )

        except Exception as e:
            # Operation failed
            duration = time.time() - start_time

            self.structured_logger.error(
                f"Operation failed: {operation_name}",
                extra={
                    "operation_type": "error",
                    "duration_seconds": duration,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation_metadata": metadata,
                },
                exc_info=True,
            )

            # Record error metrics
            self.metrics.increment_counter(
                "screening_requests_total",
                labels={"status": "error", "user_type": context.user_id or "anonymous"},
            )

            raise

        finally:
            # Decrement active operations gauge
            self.metrics.set_gauge("active_screening_operations", -1.0)


class ObservabilityManager:
    """Central manager for observability features."""

    def __init__(self) -> None:
        """Initialize observability manager."""
        self.metrics = BusinessMetricsCollector()
        self.performance = PerformanceMonitor(self.metrics)
        self.structured_logger = StructuredLogger(__name__)
        self._alert_callbacks: list[Callable[[list[dict[str, Any]]], None]] = []

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current context."""
        correlation_id_var.set(correlation_id)

    def set_user_id(self, user_id: str) -> None:
        """Set user ID for current context."""
        user_id_var.set(user_id)

    def set_request_id(self, request_id: str) -> None:
        """Set request ID for current context."""
        request_id_var.set(request_id)

    def get_correlation_id(self) -> str | None:
        """Get current correlation ID."""
        return correlation_id_var.get()

    @contextmanager
    def request_context(
        self,
        correlation_id: str | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
    ) -> Any:
        """Context manager for request-scoped observability."""
        # Store original values
        original_correlation = correlation_id_var.get()
        original_user = user_id_var.get()
        original_request = request_id_var.get()

        try:
            # Set new values
            if correlation_id:
                correlation_id_var.set(correlation_id)
            elif not original_correlation:
                correlation_id_var.set(str(uuid.uuid4()))

            if user_id:
                user_id_var.set(user_id)
            if request_id:
                request_id_var.set(request_id)

            yield

        finally:
            # Restore original values
            correlation_id_var.set(original_correlation)
            user_id_var.set(original_user)
            request_id_var.set(original_request)

    def add_alert_callback(
        self, callback: Callable[[list[dict[str, Any]]], None]
    ) -> None:
        """Add callback for metric threshold alerts."""
        self._alert_callbacks.append(callback)

    def check_alerts(self) -> None:
        """Check metric thresholds and trigger alerts."""
        alerts = self.metrics.check_thresholds()
        if alerts:
            self.structured_logger.warning(
                f"Metric threshold alerts triggered: {len(alerts)} alerts",
                extra={"alerts": alerts},
            )

            # Trigger alert callbacks
            for callback in self._alert_callbacks:
                try:
                    callback(alerts)
                except Exception as e:
                    self.structured_logger.error(
                        f"Alert callback failed: {e}", exc_info=True
                    )

    def start_metrics_server(self, port: int = 8001) -> None:
        """Start Prometheus metrics HTTP server."""
        start_http_server(port)
        self.structured_logger.info(
            f"Metrics server started on port {port}", extra={"metrics_port": port}
        )


# Global observability manager instance
observability_manager = ObservabilityManager()


def track_business_operation(operation_name: str, **metadata: Any) -> Callable[[F], F]:
    """Decorator to track business operations with metrics and logging."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with observability_manager.performance.monitor_operation(
                operation_name, **metadata
            ):
                return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger for a module."""
    return StructuredLogger(name)


# Convenience functions
def log_business_event(event_name: str, **metadata: Any) -> None:
    """Log a business event with structured logging."""
    logger = get_structured_logger("business_events")
    logger.info(f"Business event: {event_name}", extra=metadata)


def track_data_quality_metric(metric_name: str, value: float, **labels: Any) -> None:
    """Track a data quality metric."""
    observability_manager.metrics.observe_histogram(
        f"data_quality_{metric_name}", value, labels=labels
    )


def track_user_action(action: str, user_id: str | None = None, **metadata: Any) -> None:
    """Track user actions for analytics."""
    observability_manager.metrics.increment_counter(
        "user_actions_total",
        labels={"action": action, "user_id": user_id or "anonymous"},
    )

    log_business_event(
        f"user_action_{action}", user_id=user_id, action_metadata=metadata
    )
