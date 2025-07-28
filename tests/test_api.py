"""Integration tests for FastAPI service endpoints."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

# Note: We don't import app directly anymore - it's provided by the test_client fixture


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint_returns_200(self, test_client: TestClient) -> None:
        """Test that /healthz returns 200 OK with correct response."""
        response = test_client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "up"}

    def test_health_endpoint_content_type(self, test_client: TestClient) -> None:
        """Test that /healthz returns correct content type."""
        response = test_client.get("/healthz")
        assert response.headers["content-type"] == "application/json"


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

    def test_screen_endpoint_returns_list(self, test_client: TestClient) -> None:
        """Test that /api/v1/screen returns a list of stocks."""
        params = {
            "min_yield": 0.02,
            "max_payout": 80.0,
            "min_cagr": 0.05,
            "top_n": 5,
        }
        response = test_client.get("/api/v1/screen", params=params)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5  # Should respect top_n parameter

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

        if data:  # If we have results
            stock = data[0]
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

        if len(data) > 1:
            # Check that scores are in descending order
            scores = [stock["score"] for stock in data]
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
        assert isinstance(data, list)
        assert len(data) == 0

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
        assert len(data) <= 2

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
        if data:
            symbols = [stock["symbol"] for stock in data]
            # All symbols should start with "TEST" (our test data)
            assert all(
                symbol.startswith("TEST") for symbol in symbols
            ), f"Expected test symbols, got: {symbols}"


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


class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_endpoint_returns_info(self, test_client: TestClient) -> None:
        """Test that root endpoint returns API information."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data


class TestEnvironmentIsolation:
    """Test that the test environment is properly isolated."""

    def test_environment_variable_isolation(self, test_client: TestClient) -> None:
        """Test that test environment variables are properly set."""
        import os

        # Verify we're in test environment
        assert os.environ.get("DGI_ENVIRONMENT") == "test"

        # Verify sensitive API keys are not set in test environment
        assert "OPENAI_API_KEY" not in os.environ
        assert "ANTHROPIC_API_KEY" not in os.environ

    def test_data_path_isolation(self, test_client: TestClient, test_csv_file) -> None:
        """Test that test data path is properly isolated."""
        import os

        # Verify test data path is set
        assert os.environ.get("DGI_DATA_PATH") == str(test_csv_file)

        # Verify it's not pointing to production data
        assert "fundamentals_small.csv" not in str(test_csv_file)
        assert "test_fundamentals.csv" in str(test_csv_file)
