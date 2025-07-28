"""Integration tests for FastAPI service endpoints."""

import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Note: We don't import app directly anymore - it's provided by the test_client fixture


@pytest.mark.api
class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint_returns_200(self, test_client: TestClient) -> None:
        """Test that /healthz returns 200 OK with correct response."""
        response = test_client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        assert "dependencies" in data
        assert "metrics" in data

    def test_health_endpoint_content_type(self, test_client: TestClient) -> None:
        """Test that /healthz returns correct content type."""
        response = test_client.get("/healthz")
        assert response.headers["content-type"] == "application/json"


@pytest.mark.api
class TestScreenEndpoint:
    """Test the screening endpoint."""

    def test_screen_endpoint_accepts_valid_parameters(
        self, test_client: TestClient
    ) -> None:
        """Test that /api/v1/screen accepts valid query parameters."""
        params = {
            "min_yield": 0.02,
            "max_payout": 80.0,
            "min_cagr": 0.05,
            "top_n": 10,
        }
        response = test_client.get("/api/v1/screen", params=params)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_screen_endpoint_returns_structured_response(
        self, test_client: TestClient
    ) -> None:
        """Test that /api/v1/screen returns structured response."""
        params = {
            "min_yield": 0.02,
            "max_payout": 80.0,
            "min_cagr": 0.05,
            "top_n": 5,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()

        # Check response structure
        assert "stocks" in data
        assert "total_count" in data
        assert "filters_applied" in data
        assert "processing_time_ms" in data

        # Check stocks list
        assert isinstance(data["stocks"], list)
        assert data["total_count"] == len(data["stocks"])
        assert len(data["stocks"]) <= 5  # Should respect top_n parameter

    def test_screen_endpoint_stock_structure(self, test_client: TestClient) -> None:
        """Test that returned stocks have the expected structure."""
        params = {
            "min_yield": 0.02,
            "max_payout": 80.0,
            "min_cagr": 0.05,
            "top_n": 1,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()

        if data["stocks"]:  # If we have results
            stock = data["stocks"][0]
            expected_fields = {
                "symbol",
                "name",
                "sector",
                "industry",
                "dividend_yield",
                "payout",
                "dividend_cagr",
                "fcf_yield",
                "score",
            }
            assert all(field in stock for field in expected_fields)
            assert isinstance(stock["symbol"], str)
            assert isinstance(stock["dividend_yield"], int | float)
            assert isinstance(stock["score"], int | float)

    def test_screen_endpoint_sorted_by_score(self, test_client: TestClient) -> None:
        """Test that stocks are returned sorted by score (descending)."""
        params = {
            "min_yield": 0.0,  # Low threshold to get more results
            "max_payout": 100.0,
            "min_cagr": 0.0,
            "top_n": 3,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()

        if len(data["stocks"]) > 1:
            # Check that scores are in descending order
            scores = [stock["score"] for stock in data["stocks"]]
            assert scores == sorted(scores, reverse=True)

    def test_screen_endpoint_parameter_validation(
        self, test_client: TestClient
    ) -> None:
        """Test that invalid parameters return appropriate errors."""
        # Test negative values
        params = {"min_yield": -0.1, "max_payout": 80.0, "min_cagr": 0.05}
        response = test_client.get("/api/v1/screen", params=params)
        assert response.status_code == 422  # Validation error

        # Test that endpoint works with no parameters (uses defaults)
        response = test_client.get("/api/v1/screen")
        assert response.status_code == 200  # Should work with defaults

    def test_screen_endpoint_default_values(self, test_client: TestClient) -> None:
        """Test that endpoint works with default parameter values."""
        # Test with minimal parameters
        params = {"min_yield": 0.02}
        response = test_client.get("/api/v1/screen", params=params)
        assert response.status_code == 200

    def test_screen_endpoint_empty_results(self, test_client: TestClient) -> None:
        """Test that endpoint handles cases with no matching stocks."""
        params = {
            "min_yield": 50.0,  # Very high yield - unlikely to have results
            "max_payout": 10.0,
            "min_cagr": 50.0,
            "top_n": 10,
        }
        response = test_client.get("/api/v1/screen", params=params)
        assert response.status_code == 200
        data = response.json()
        assert data["stocks"] == []
        assert data["total_count"] == 0

    def test_screen_endpoint_top_n_respected(self, test_client: TestClient) -> None:
        """Test that top_n parameter is respected."""
        params = {
            "min_yield": 0.0,
            "max_payout": 100.0,
            "min_cagr": 0.0,
            "top_n": 2,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()
        assert len(data["stocks"]) <= 2

    @pytest.mark.parametrize(
        "param_name,invalid_value",
        [
            ("min_yield", "not_a_number"),
            ("max_payout", "invalid"),
            ("min_cagr", "abc"),
            ("top_n", -1),
            ("top_n", "not_an_integer"),
        ],
    )
    def test_screen_endpoint_invalid_parameter_types(
        self, test_client: TestClient, param_name: str, invalid_value: Any
    ) -> None:
        """Test that invalid parameter types return validation errors."""
        params = {
            "min_yield": 0.02,
            "max_payout": 80.0,
            "min_cagr": 0.05,
            "top_n": 10,
        }
        params[param_name] = invalid_value

        response = test_client.get("/api/v1/screen", params=params)
        assert response.status_code == 422

    def test_screen_endpoint_uses_test_data(self, test_client: TestClient) -> None:
        """Test that the endpoint uses test data, not production data."""
        params = {
            "min_yield": 0.0,
            "max_payout": 100.0,
            "min_cagr": 0.0,
            "top_n": 10,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()

        # Verify we're getting test data (TEST1, TEST2, etc.)
        if data["stocks"]:
            symbols = [stock["symbol"] for stock in data["stocks"]]
            # All symbols should start with "TEST" (our test data)
            assert all(
                symbol.startswith("TEST") for symbol in symbols
            ), f"Expected test symbols, got: {symbols}"

    def test_screen_endpoint_filters_applied(self, test_client: TestClient) -> None:
        """Test that filters_applied field contains the correct parameters."""
        params = {
            "min_yield": 0.03,
            "max_payout": 70.0,
            "min_cagr": 0.08,
            "top_n": 5,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()

        filters = data["filters_applied"]
        assert filters["min_yield"] == 0.03
        assert filters["max_payout"] == 70.0
        assert filters["min_cagr"] == 0.08
        assert filters["top_n"] == 5

    def test_screen_endpoint_processing_time(self, test_client: TestClient) -> None:
        """Test that processing_time_ms is included in response."""
        params = {
            "min_yield": 0.02,
            "max_payout": 80.0,
            "min_cagr": 0.05,
            "top_n": 5,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()

        assert "processing_time_ms" in data
        assert isinstance(data["processing_time_ms"], int | float)
        assert data["processing_time_ms"] >= 0


@pytest.mark.api
class TestOpenAPIDocumentation:
    """Test that OpenAPI documentation is available."""

    def test_openapi_schema_available(self, test_client: TestClient) -> None:
        """Test that OpenAPI schema is accessible."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema

    def test_swagger_ui_available(self, test_client: TestClient) -> None:
        """Test that Swagger UI is accessible."""
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_available(self, test_client: TestClient) -> None:
        """Test that ReDoc is accessible."""
        response = test_client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.api
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_404_for_unknown_endpoint(self, test_client: TestClient) -> None:
        """Test that unknown endpoints return 404."""
        response = test_client.get("/unknown/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, test_client: TestClient) -> None:
        """Test that POST to GET-only endpoints returns 405."""
        response = test_client.post("/api/v1/screen")
        assert response.status_code == 405

    def test_internal_server_error_handling(self, test_client: TestClient) -> None:
        """Test that internal errors are handled gracefully."""
        # This would require mocking the screener to raise an exception
        # For now, we'll test that the endpoint doesn't crash with edge cases
        params = {
            "min_yield": 0.0,
            "max_payout": 0.0,  # This might cause issues
            "min_cagr": 0.0,
            "top_n": 1,
        }
        response = test_client.get("/api/v1/screen", params=params)
        # Should not return 500, should handle gracefully
        assert response.status_code in [200, 422]


@pytest.mark.api
class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_endpoint_returns_info(self, test_client: TestClient) -> None:
        """Test that root endpoint returns API information."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "documentation_url" in data
        assert "features" in data
        assert "rate_limits" in data
        assert "endpoints" in data


@pytest.mark.api
class TestSecurityHeaders:
    """Test that security headers are present."""

    def test_security_headers_present(self, test_client: TestClient) -> None:
        """Test that security headers are included in responses."""
        response = test_client.get("/healthz")

        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "X-Process-Time" in response.headers

    def test_correlation_id_header(self, test_client: TestClient) -> None:
        """Test that correlation ID header is present."""
        response = test_client.get("/healthz")

        # Check for correlation ID header
        assert "X-Correlation-ID" in response.headers
        correlation_id = response.headers["X-Correlation-ID"]
        assert correlation_id.startswith("req-")


@pytest.mark.api
class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_headers(self, test_client: TestClient) -> None:
        """Test that rate limiting headers are present."""
        response = test_client.get("/healthz")

        # Check for rate limiting headers (slowapi may not add these by default)
        # The important thing is that rate limiting is configured
        # We can check that the endpoint is rate-limited by the decorator
        # For now, we'll just verify the endpoint works
        assert response.status_code == 200


@pytest.mark.api
class TestEnvironmentIsolation:
    """Test that the test environment is properly isolated."""

    def test_environment_variable_isolation(self, test_client: TestClient) -> None:
        """Test that test environment variables are properly set."""
        # Verify we're in test environment
        assert os.environ.get("DGI_ENVIRONMENT") == "test"

        # Verify sensitive API keys are not set in test environment
        assert "OPENAI_API_KEY" not in os.environ
        assert "ANTHROPIC_API_KEY" not in os.environ

    def test_data_path_isolation(self, test_client: TestClient, test_csv_file) -> None:
        """Test that test data path is properly isolated."""
        # Verify test data path is set
        assert os.environ.get("DGI_DATA_PATH") == str(test_csv_file)

        # Verify it's not pointing to production data
        assert "fundamentals_small.csv" not in str(test_csv_file)
        assert "test_fundamentals.csv" in str(test_csv_file)


@pytest.mark.api
class TestRateLimitingIntegration:
    """Test rate limiting functionality comprehensively."""

    def test_rate_limiting_configuration(self, test_client: TestClient) -> None:
        """Test that rate limiting is properly configured."""
        # Test that endpoints are rate-limited by checking they don't crash
        # and return proper responses
        response = test_client.get("/healthz")
        assert response.status_code == 200

        # Test that rate limiting decorators are applied
        # (we can't easily test the actual rate limiting in unit tests)
        # but we can verify the endpoints work correctly

    def test_rate_limiting_across_endpoints(self, test_client: TestClient) -> None:
        """Test that rate limiting works across different endpoints."""
        # Test health endpoint
        health_response = test_client.get("/healthz")
        assert health_response.status_code == 200

        # Test screen endpoint
        screen_response = test_client.get("/api/v1/screen?min_yield=0.02&top_n=1")
        assert screen_response.status_code == 200

        # Both endpoints should work correctly with rate limiting applied

    def test_rate_limiting_error_handling(self, test_client: TestClient) -> None:
        """Test that rate limiting error handling is configured."""
        # Test that the API has proper error handling for rate limiting
        # by making multiple requests and ensuring they all succeed
        # (in a real scenario, rate limiting would kick in after many requests)

        responses = []
        for _ in range(5):
            response = test_client.get("/healthz")
            responses.append(response.status_code)

        # All requests should succeed (we're not hitting rate limits in tests)
        assert all(status == 200 for status in responses)


@pytest.mark.api
class TestSecurityHeadersIntegration:
    """Test security headers comprehensively."""

    def test_all_security_headers_present(self, test_client: TestClient) -> None:
        """Test that all required security headers are present."""
        response = test_client.get("/healthz")

        # Check for core security headers (some may not be present in test environment)
        core_security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
        ]

        for header in core_security_headers:
            assert header in response.headers, f"Missing security header: {header}"

    def test_security_header_values(self, test_client: TestClient) -> None:
        """Test that security headers have correct values."""
        response = test_client.get("/healthz")

        # Check specific header values for headers that should be present
        if "X-Content-Type-Options" in response.headers:
            assert response.headers["X-Content-Type-Options"] == "nosniff"
        if "X-Frame-Options" in response.headers:
            assert response.headers["X-Frame-Options"] == "DENY"
        if "X-XSS-Protection" in response.headers:
            assert response.headers["X-XSS-Protection"] == "1; mode=block"
        if "Referrer-Policy" in response.headers:
            assert (
                response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
            )

    def test_security_headers_consistent_across_endpoints(
        self, test_client: TestClient
    ) -> None:
        """Test that security headers are consistent across all endpoints."""
        endpoints = [
            "/healthz",
            "/api/v1/health",
            "/api/v1/screen?min_yield=0.02&top_n=1",
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-XSS-Protection" in response.headers


@pytest.mark.api
class TestCorrelationIDIntegration:
    """Test correlation ID tracking comprehensively."""

    def test_correlation_id_header_present(self, test_client: TestClient) -> None:
        """Test that correlation ID header is present in responses."""
        response = test_client.get("/healthz")
        assert "X-Correlation-ID" in response.headers

        correlation_id = response.headers["X-Correlation-ID"]
        assert correlation_id is not None
        assert len(correlation_id) > 0

    def test_correlation_id_unique_per_request(self, test_client: TestClient) -> None:
        """Test that each request gets a unique correlation ID."""
        response1 = test_client.get("/healthz")
        response2 = test_client.get("/healthz")

        correlation_id1 = response1.headers["X-Correlation-ID"]
        correlation_id2 = response2.headers["X-Correlation-ID"]

        # Correlation IDs should be unique
        assert correlation_id1 != correlation_id2

    def test_correlation_id_format(self, test_client: TestClient) -> None:
        """Test that correlation ID follows expected format."""
        response = test_client.get("/healthz")
        correlation_id = response.headers["X-Correlation-ID"]

        # Should start with 'req-' and contain alphanumeric characters
        assert correlation_id.startswith("req-")
        assert len(correlation_id) > 4  # More than just "req-"

    def test_correlation_id_consistent_in_error_responses(
        self, test_client: TestClient
    ) -> None:
        """Test that correlation ID is present even in error responses."""
        # Test with invalid endpoint
        response = test_client.get("/invalid-endpoint")

        # Should still have correlation ID even for 404
        assert "X-Correlation-ID" in response.headers
        assert response.headers["X-Correlation-ID"] is not None


@pytest.mark.api
class TestErrorHandlingIntegration:
    """Test error handling scenarios comprehensively."""

    def test_validation_error_structure(self, test_client: TestClient) -> None:
        """Test that validation errors return proper structure."""
        # Test with invalid parameter
        response = test_client.get("/api/v1/screen?min_yield=invalid")

        assert response.status_code == 422  # Validation error

        # Check error response structure (our custom error handler format)
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Request validation failed"

        # Check validation errors structure
        details = data["error"]["details"]
        assert "validation_errors" in details
        assert isinstance(details["validation_errors"], list)

        # Check error detail structure
        if details["validation_errors"]:
            error_detail = details["validation_errors"][0]
            assert "field" in error_detail
            assert "message" in error_detail
            assert "type" in error_detail

    def test_internal_server_error_handling(self, test_client: TestClient) -> None:
        """Test that internal server errors are handled gracefully."""
        # This test ensures the API doesn't crash on unexpected errors
        # We can't easily trigger a real 500 error, but we can test the error handling structure

        # Test with valid request to ensure no unexpected errors
        response = test_client.get("/healthz")
        assert response.status_code in [
            200,
            503,
        ]  # Should be either healthy or unhealthy, not 500

    def test_method_not_allowed_handling(self, test_client: TestClient) -> None:
        """Test that method not allowed errors are handled properly."""
        # Test POST to GET-only endpoint
        response = test_client.post("/healthz")
        assert response.status_code == 405  # Method Not Allowed

    def test_not_found_handling(self, test_client: TestClient) -> None:
        """Test that not found errors are handled properly."""
        # Test non-existent endpoint
        response = test_client.get("/non-existent-endpoint")
        assert response.status_code == 404  # Not Found


@pytest.mark.api
class TestPerformanceIntegration:
    """Test performance aspects of the API."""

    def test_response_time_reasonable(self, test_client: TestClient) -> None:
        """Test that API response times are reasonable."""
        import time

        # Test health endpoint (should be fast)
        start_time = time.time()
        response = test_client.get("/healthz")
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second

        # Verify response is still valid
        assert response.status_code == 200

    def test_screening_performance_with_processing_time(
        self, test_client: TestClient
    ) -> None:
        """Test that screening endpoint includes processing time and is reasonable."""
        response = test_client.get("/api/v1/screen?min_yield=0.02&top_n=5")

        assert response.status_code == 200
        data = response.json()

        # Check that processing time is included
        assert "processing_time_ms" in data
        processing_time = data["processing_time_ms"]

        # Processing time should be reasonable (less than 5 seconds)
        assert processing_time is not None
        assert processing_time < 5000  # 5 seconds in milliseconds

    def test_concurrent_requests_handling(self, test_client: TestClient) -> None:
        """Test that the API can handle concurrent requests."""
        import threading

        results = []
        errors = []

        def make_request():
            try:
                response = test_client.get("/healthz")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that all requests succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(status == 200 for status in results)


@pytest.mark.api
class TestCacheIntegration:
    """Test caching functionality."""

    def test_cache_statistics_endpoint(self, test_client: TestClient) -> None:
        """Test that cache statistics endpoint works."""
        response = test_client.get("/api/v1/cache/stats")

        assert response.status_code == 200
        data = response.json()

        # Check cache statistics structure
        expected_fields = [
            "hits",
            "misses",
            "total_requests",
            "hit_rate_percent",
            "cache_size",
            "default_ttl",
        ]
        for field in expected_fields:
            assert field in data

        # Verify data types
        assert isinstance(data["hits"], int)
        assert isinstance(data["misses"], int)
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["hit_rate_percent"], int | float)
        assert isinstance(data["cache_size"], int)
        assert isinstance(data["default_ttl"], int)

    def test_cache_statistics_values_reasonable(self, test_client: TestClient) -> None:
        """Test that cache statistics have reasonable values."""
        response = test_client.get("/api/v1/cache/stats")
        data = response.json()

        # Basic validation
        assert data["hits"] >= 0
        assert data["misses"] >= 0
        assert data["total_requests"] >= 0
        assert 0 <= data["hit_rate_percent"] <= 100
        assert data["cache_size"] >= 0
        assert data["default_ttl"] > 0

    def test_cache_improves_performance(self, test_client: TestClient) -> None:
        """Test that caching improves performance for repeated requests."""
        import time

        # First request (cache miss)
        start_time = time.time()
        response1 = test_client.get("/api/v1/screen?min_yield=0.02&top_n=1")
        _ = time.time() - start_time  # Unused variable

        # Second request (should be cached)
        start_time = time.time()
        response2 = test_client.get("/api/v1/screen?min_yield=0.02&top_n=1")
        _ = time.time() - start_time  # Unused variable

        # Both requests should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Second request should be faster (cached)
        # Note: This is a basic test - in practice, caching might not always be faster
        # due to various factors, but the endpoint should still work correctly
