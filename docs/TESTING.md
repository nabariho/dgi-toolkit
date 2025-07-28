# Testing Strategy & Environment Isolation

This document outlines our comprehensive testing strategy that ensures complete
isolation between test and production environments.

## 🛡️ **Test Environment Isolation**

### **Core Principles**

1. **🔒 Complete Data Isolation**: Tests never touch production data
2. **🌍 Environment Separation**: Test environment variables are isolated
3. **🧪 Deterministic Results**: Tests use controlled, predictable data
4. **🔄 Clean State**: Each test starts with a clean, known state
5. **🚫 No Side Effects**: Tests cannot modify production systems

## 🏗️ **Test Architecture**

### **Test Data Management**

```python
# Test data is created in tests/test_data/
# Each test uses isolated test data files
tests/
├── test_data/
│   └── test_fundamentals.csv  # Isolated test data
├── conftest.py               # Test configuration
└── test_api.py              # API tests
```

### **Environment Variable Isolation**

```python
# Tests automatically set and restore environment variables
@pytest.fixture(autouse=True)
def test_environment():
    # Store original environment
    original_env = {...}

    try:
        # Set test environment
        os.environ["DGI_ENVIRONMENT"] = "test"
        os.environ["DGI_DATA_PATH"] = "tests/test_data/test_fundamentals.csv"

        # Clear sensitive API keys
        del os.environ["OPENAI_API_KEY"]

        yield

    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
```

## 🧪 **Test Types**

### **1. Unit Tests**

- **Scope**: Individual functions and classes
- **Data**: Mocked or minimal test data
- **Isolation**: Complete isolation from external systems
- **Speed**: Fast execution (< 1 second per test)

### **2. Integration Tests**

- **Scope**: Component interactions
- **Data**: Test data files
- **Isolation**: Isolated test environment
- **Speed**: Medium execution (1-5 seconds per test)

### **3. API Tests**

- **Scope**: HTTP endpoints and responses
- **Data**: Dedicated test data
- **Isolation**: Test server with test data
- **Speed**: Medium execution (1-10 seconds per test)

## 🚀 **Running Tests**

### **Run All Tests**

```bash
# Run all tests with isolation
poetry run pytest

# Run with coverage
poetry run pytest --cov=dgi --cov=api --cov-report=html
```

### **Run Specific Test Types**

```bash
# Unit tests only
poetry run pytest -m unit

# Integration tests only
poetry run pytest -m integration

# API tests only
poetry run pytest -m api

# Fast tests (skip slow ones)
poetry run pytest -m "not slow"
```

### **Run Test Server**

```bash
# Start test server with isolated data
poetry run python run_test_server.py

# This will:
# 1. Create temporary test data
# 2. Set test environment variables
# 3. Start server on localhost:8000
# 4. Clean up test data on shutdown
```

## 📊 **Test Data Strategy**

### **Test Data Characteristics**

1. **🎯 Predictable**: Known values for consistent testing
2. **🔒 Isolated**: Separate from production data
3. **📝 Minimal**: Only data needed for tests
4. **🧹 Clean**: No sensitive or real company data
5. **🔄 Disposable**: Can be recreated at any time

### **Example Test Data**

```csv
symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield
TEST1,Test Company 1,Technology,Software,0.025,30.0,0.08,5.0
TEST2,Test Company 2,Healthcare,Pharmaceuticals,0.035,45.0,0.12,4.5
TEST3,Test Company 3,Consumer,Retail,0.020,25.0,0.06,3.8
```

### **Test Data Validation**

```python
def test_screen_endpoint_uses_test_data(self, test_client: TestClient) -> None:
    """Test that the endpoint uses test data, not production data."""
    response = test_client.get("/api/v1/screen", params={"top_n": 10})
    data = response.json()

    if data:
        symbols = [stock["symbol"] for stock in data]
        # All symbols should start with "TEST" (our test data)
        assert all(symbol.startswith("TEST") for symbol in symbols)
```

## 🔧 **Test Configuration**

### **pytest.ini Configuration**

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --cov=dgi
    --cov=api
    --cov-fail-under=85
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
```

### **conftest.py Fixtures**

```python
@pytest.fixture(scope="session")
def test_csv_file(test_data_dir: Path) -> Path:
    """Create a test CSV file with minimal test data."""
    # Creates isolated test data file

@pytest.fixture
def test_client(test_csv_file: Path) -> Generator[TestClient, None, None]:
    """Create a test client with isolated test data."""
    # Sets up test environment and client

@pytest.fixture(autouse=True)
def test_environment():
    """Ensure test environment isolation."""
    # Manages environment variable isolation
```

## 🛡️ **Security & Safety Measures**

### **API Key Protection**

- **Test Environment**: API keys are automatically cleared
- **Production Keys**: Never used in tests
- **Mock Services**: External APIs are mocked when needed

### **Data Protection**

- **Test Data**: Uses fake company names and symbols
- **No Real Data**: Tests never contain real company information
- **Temporary Files**: Test data files are cleaned up automatically

### **Environment Isolation**

- **Separate Paths**: Test data uses different file paths
- **Environment Variables**: Test environment is clearly marked
- **Clean State**: Each test starts with a clean environment

## 📈 **Test Coverage Requirements**

### **Coverage Targets**

- **Overall Coverage**: ≥ 85%
- **API Code**: ≥ 90%
- **Core Business Logic**: ≥ 95%
- **New Features**: 100% for critical paths

### **Coverage Reports**

```bash
# Generate HTML coverage report
poetry run pytest --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## 🔍 **Test Validation**

### **Automated Checks**

```bash
# Run quality checks
./scripts/check-quality.sh

# This includes:
# - Code formatting (Black, Ruff)
# - Linting (Ruff, MyPy)
# - Security scanning (Bandit)
# - Test execution with coverage
```

### **Manual Validation**

```bash
# Test the API manually
poetry run python run_test_server.py

# In another terminal:
curl http://localhost:8000/healthz
curl "http://localhost:8000/api/v1/screen?min_yield=0.02&top_n=3"
```

## 🚨 **Best Practices**

### **Do's**

- ✅ Use test fixtures for data setup
- ✅ Always clean up test data
- ✅ Use descriptive test names
- ✅ Test both success and failure cases
- ✅ Mock external dependencies
- ✅ Use isolated test data

### **Don'ts**

- ❌ Never use production data in tests
- ❌ Don't hardcode API keys in tests
- ❌ Avoid testing implementation details
- ❌ Don't create tests that depend on each other
- ❌ Never skip cleanup in test teardown

## 🔄 **Continuous Integration**

### **CI Pipeline**

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    poetry run pytest --cov=dgi --cov=api --cov-fail-under=85
    poetry run pytest --cov-report=xml
```

### **Pre-commit Hooks**

```bash
# Pre-commit automatically runs tests
pre-commit run --all-files

# This ensures:
# - All tests pass before commit
# - Code quality standards are met
# - No production data is accidentally committed
```

## 📚 **Additional Resources**

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test Isolation Best Practices](https://martinfowler.com/articles/microservice-testing/)
- [Environment Variable Management](https://12factor.net/config)
