"""Tests for the observability module."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from api.observability import (
    ObservabilityManager,
    get_metrics,
    get_observability_manager,
    instrument_fastapi,
)


class TestObservabilityManager:
    """Test the ObservabilityManager class."""

    def test_initialization(self):
        """Test ObservabilityManager initialization."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            assert manager.settings is not None
            assert manager._correlation_id is None

    def test_correlation_id_management(self):
        """Test correlation ID setting and getting."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Test setting correlation ID
            test_id = "test-correlation-id"
            manager.set_correlation_id(test_id)
            assert manager.get_correlation_id() == test_id

            # Test generating new correlation ID
            new_id = manager.generate_correlation_id()
            assert new_id is not None
            assert isinstance(new_id, str)
            assert len(new_id) > 0

    def test_record_request(self):
        """Test request recording functionality."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Mock the meter and metrics properly
            mock_meter = Mock()
            mock_counter = Mock()
            mock_histogram = Mock()
            mock_meter.create_counter.return_value = mock_counter
            mock_meter.create_histogram.return_value = mock_histogram
            manager.meter = mock_meter

            # Set up the metrics that the manager expects
            manager.request_counter = mock_counter
            manager.request_duration = mock_histogram

            # Test recording a request
            manager.record_request("GET", "/test", 200, 0.5)

            # Verify metrics were called
            assert mock_counter.add.called
            assert mock_histogram.record.called

    def test_record_screening_operation(self):
        """Test screening operation recording."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Mock the meter and metrics
            mock_meter = Mock()
            mock_counter = Mock()
            mock_meter.create_counter.return_value = mock_counter
            manager.meter = mock_meter

            # Set up the metrics that the manager expects
            manager.screening_operations = mock_counter

            # Test recording screening operation
            filters = {"min_yield": 0.02, "max_payout": 80.0}
            manager.record_screening_operation(10, 0.5, filters)

            # Verify metrics were called
            assert mock_counter.add.called

    def test_record_cache_operation(self):
        """Test cache operation recording."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Mock the meter and metrics
            mock_meter = Mock()
            mock_counter = Mock()
            mock_meter.create_counter.return_value = mock_counter
            manager.meter = mock_meter

            # Set up the metrics that the manager expects
            manager.cache_operations = mock_counter

            # Test recording cache hit
            manager.record_cache_operation(True, "test-key", "default")
            assert mock_counter.add.called

            # Test recording cache miss
            manager.record_cache_operation(False, "test-key", "default")
            assert mock_counter.add.called

    def test_record_error(self):
        """Test error recording functionality."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Mock the meter and metrics
            mock_meter = Mock()
            mock_counter = Mock()
            mock_meter.create_counter.return_value = mock_counter
            manager.meter = mock_meter

            # Set up the metrics that the manager expects
            manager.error_counter = mock_counter

            # Test recording an error
            manager.record_error("validation_error", "Invalid input", "/test")
            assert mock_counter.add.called

    def test_record_job_operation(self):
        """Test job operation recording."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Mock the meter and metrics
            mock_meter = Mock()
            mock_counter = Mock()
            mock_meter.create_counter.return_value = mock_counter
            manager.meter = mock_meter

            # Set up the metrics that the manager expects
            manager.job_operations = mock_counter

            # Test recording job operation
            manager.record_job_operation("completed", 1.5)
            assert mock_counter.add.called

    @pytest.mark.asyncio
    async def test_trace_operation_success(self):
        """Test tracing operation with successful execution."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Mock the tracer properly with start_as_current_span
            mock_tracer = Mock()
            mock_span = Mock()
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_span)
            mock_context.__exit__ = Mock(return_value=None)
            mock_tracer.start_as_current_span.return_value = mock_context
            manager.tracer = mock_tracer

            # Test tracing operation
            async with manager.trace_operation("test_operation", {"key": "value"}):
                await asyncio.sleep(0.01)  # Small delay to simulate work

            # Verify span was created and attributes were set
            assert mock_tracer.start_as_current_span.called
            assert mock_span.set_attributes.called

    @pytest.mark.asyncio
    async def test_trace_operation_exception(self):
        """Test tracing operation with exception handling."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Mock the tracer properly with start_as_current_span
            mock_tracer = Mock()
            mock_span = Mock()
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_span)
            mock_context.__exit__ = Mock(return_value=None)
            mock_tracer.start_as_current_span.return_value = mock_context
            manager.tracer = mock_tracer

            # Test tracing operation with exception
            with pytest.raises(ValueError):
                async with manager.trace_operation("test_operation"):
                    raise ValueError("Test exception")

            # Verify span was created and exception was recorded
            assert mock_tracer.start_as_current_span.called
            assert mock_span.record_exception.called

    @pytest.mark.asyncio
    async def test_log_business_event(self):
        """Test business event logging."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Test logging business event (this method doesn't use tracer)
            event_data = {"user_id": "123", "action": "screening"}
            await manager.log_business_event("user_action", event_data, "user123")

            # Verify the method completes without errors
            assert True

    def test_log_performance_event(self):
        """Test performance event logging."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Test logging performance event
            metadata = {"operation": "screening", "stocks_processed": 100}
            manager.log_performance_event("screening", 1.5, metadata)

            # Verify logging occurred (we can't easily test the actual log call)
            # but we can verify the method doesn't raise exceptions
            assert True

    def test_log_security_event(self):
        """Test security event logging."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Test logging security event
            details = {"ip": "192.168.1.1", "user_agent": "test-agent"}
            manager.log_security_event("failed_login", details, "warning")

            # Verify logging occurred
            assert True

    def test_initialization_without_opentelemetry(self):
        """Test initialization when OpenTelemetry is not available."""
        with (
            patch("api.observability.OPENTELEMETRY_AVAILABLE", False),
            patch("api.observability.get_settings") as mock_settings,
        ):
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Should not crash and should handle missing OpenTelemetry gracefully
            assert manager.meter is None
            assert manager.tracer is None

    def test_initialization_without_prometheus(self):
        """Test initialization when Prometheus is not available."""
        with (
            patch("api.observability.PROMETHEUS_AVAILABLE", False),
            patch("api.observability.get_settings") as mock_settings,
        ):
            mock_settings.return_value = Mock()
            ObservabilityManager()

            # Should not crash and should handle missing Prometheus gracefully
            assert True


class TestObservabilityFunctions:
    """Test the module-level functions."""

    def test_get_observability_manager_singleton(self):
        """Test that get_observability_manager returns a singleton."""
        # Reset the global instance for testing
        with patch("api.observability._observability_manager", None):
            manager1 = get_observability_manager()
            manager2 = get_observability_manager()

            assert manager1 is manager2

    def test_instrument_fastapi(self):
        """Test FastAPI instrumentation."""
        mock_app = Mock()

        with (
            patch("api.observability.OPENTELEMETRY_AVAILABLE", True),
            patch("api.observability.FastAPIInstrumentor") as mock_instrumentor,
        ):
            instrument_fastapi(mock_app)
            assert mock_instrumentor.instrument_app.called

    def test_instrument_fastapi_without_opentelemetry(self):
        """Test FastAPI instrumentation when OpenTelemetry is not available."""
        mock_app = Mock()

        with patch("api.observability.OPENTELEMETRY_AVAILABLE", False):
            # Should not crash when OpenTelemetry is not available
            instrument_fastapi(mock_app)
            assert True

    def test_get_metrics(self):
        """Test metrics generation."""
        with (
            patch("api.observability.PROMETHEUS_AVAILABLE", True),
            patch("api.observability.generate_latest") as mock_generate,
        ):
            mock_generate.return_value = b"test_metrics"
            metrics = get_metrics()
            assert metrics == "test_metrics"

    def test_get_metrics_without_prometheus(self):
        """Test metrics generation when Prometheus is not available."""
        with patch("api.observability.PROMETHEUS_AVAILABLE", False):
            metrics = get_metrics()
            assert "Prometheus client not available" in metrics


class TestObservabilityIntegration:
    """Integration tests for observability features."""

    @pytest.mark.asyncio
    async def test_full_observability_workflow(self):
        """Test a complete observability workflow."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Set up correlation ID
            correlation_id = manager.generate_correlation_id()
            manager.set_correlation_id(correlation_id)

            # Mock metrics and tracing
            mock_meter = Mock()
            mock_tracer = Mock()
            mock_span = Mock()
            mock_counter = Mock()
            mock_histogram = Mock()
            mock_context = Mock()

            mock_meter.create_counter.return_value = mock_counter
            mock_meter.create_histogram.return_value = mock_histogram
            mock_context.__enter__ = Mock(return_value=mock_span)
            mock_context.__exit__ = Mock(return_value=None)
            mock_tracer.start_as_current_span.return_value = mock_context

            manager.meter = mock_meter
            manager.tracer = mock_tracer

            # Set up the metrics that the manager expects
            manager.request_counter = mock_counter
            manager.request_duration = mock_histogram
            manager.screening_operations = mock_counter
            manager.cache_operations = mock_counter

            # Simulate a complete request workflow
            manager.record_request("POST", "/api/v1/screen", 200, 0.5)

            async with manager.trace_operation("screening", {"top_n": 10}):
                manager.record_screening_operation(5, 0.3, {"min_yield": 0.02})
                manager.record_cache_operation(False, "cache_key", "default")
                await manager.log_business_event("screening_completed", {"stocks": 5})

            # Verify all observability features were used
            assert mock_counter.add.called
            assert mock_histogram.record.called
            assert mock_tracer.start_as_current_span.called
            assert mock_span.set_attributes.called
            # Note: log_business_event doesn't use tracer, so we don't check add_event

    def test_error_handling_in_observability(self):
        """Test that observability features handle errors gracefully."""
        with patch("api.observability.get_settings") as mock_settings:
            mock_settings.return_value = Mock()
            manager = ObservabilityManager()

            # Test that recording operations don't crash when metrics are not available
            manager.record_request("GET", "/test", 500, 1.0)
            manager.record_screening_operation(0, 0.1, {})
            manager.record_cache_operation(True, "key", "default")
            manager.record_error("test_error", "Test error message", "/test")
            manager.record_job_operation("failed", 0.5)

            # All operations should complete without raising exceptions
            assert True
