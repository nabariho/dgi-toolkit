"""Pytest configuration and test fixtures for DGI Toolkit."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.validation import DgiRowValidator, PydanticRowValidation


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Create a temporary directory for test data."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def test_csv_file(test_data_dir: Path) -> Path:
    """Create a test CSV file with minimal test data."""
    test_data_dir.mkdir(exist_ok=True)
    test_file = test_data_dir / "test_fundamentals.csv"

    # Create minimal test data that won't interfere with production
    test_csv_content = """symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield
TEST1,Test Company 1,Technology,Software,0.025,30.0,0.08,5.0
TEST2,Test Company 2,Healthcare,Pharmaceuticals,0.035,45.0,0.12,4.5
TEST3,Test Company 3,Consumer,Retail,0.020,25.0,0.06,3.8
TEST4,Test Company 4,Finance,Banking,0.040,60.0,0.15,6.2
TEST5,Test Company 5,Energy,Oil & Gas,0.050,70.0,0.10,7.1"""

    test_file.write_text(test_csv_content)
    return test_file


@pytest.fixture
def test_client(test_csv_file: Path) -> Generator[TestClient, None, None]:
    """Create a test client with isolated test data."""
    # Store original environment
    original_data_path = os.environ.get("DGI_DATA_PATH")

    try:
        # Set test data path
        os.environ["DGI_DATA_PATH"] = str(test_csv_file)

        # Create test client
        with TestClient(app) as client:
            yield client

    finally:
        # Restore original environment
        if original_data_path:
            os.environ["DGI_DATA_PATH"] = original_data_path
        else:
            os.environ.pop("DGI_DATA_PATH", None)


@pytest.fixture
def mock_screener(test_csv_file: Path):
    """Create a mock screener with test data."""
    validator = DgiRowValidator(PydanticRowValidation())
    repo = CsvCompanyDataRepository(str(test_csv_file), validator)
    return repo


@pytest.fixture(autouse=True)
def test_environment():
    """Ensure test environment isolation."""
    # Store original environment variables
    original_env = {}
    test_env_vars = [
        "DGI_DATA_PATH",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DGI_ENVIRONMENT",
    ]

    for var in test_env_vars:
        original_env[var] = os.environ.get(var)

    try:
        # Set test environment
        os.environ["DGI_ENVIRONMENT"] = "test"

        # Clear sensitive API keys in test environment
        for key_var in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            if key_var in os.environ:
                del os.environ[key_var]

        yield

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            else:
                os.environ.pop(var, None)


@pytest.fixture(scope="session")
def test_server_port() -> int:
    """Get a unique test server port."""
    import socket

    def find_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    return find_free_port()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for test isolation."""
    # Add custom markers
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark API tests
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)

        # Mark integration tests
        if any(keyword in item.nodeid for keyword in ["integration", "e2e", "api"]):
            item.add_marker(pytest.mark.integration)

        # Mark unit tests (default)
        if not any(keyword in item.nodeid for keyword in ["integration", "e2e", "api"]):
            item.add_marker(pytest.mark.unit)
