# Development Guide

## 🚀 Feature Development Process

This project follows a systematic approach to feature development that ensures quality,
maintainability, and adherence to industry best practices.

### Feature Development Workflow

For each feature in the backlog, we follow this 8-step process:

#### 1. **Feature Selection** 🎯

- Pick a feature from the Planned Features section in `docs/FEATURES.md`
- Prioritize based on business value and technical dependencies
- Ensure feature is well-defined with clear acceptance criteria

#### 2. **Status Update** 📋

- Move the feature from "📋 Planned" to "🔄 In Progress" in `docs/FEATURES.md`
- Update the status table with current date
- Commit the status change

#### 3. **Branch Creation** 🌿

- Create a new feature branch: `git checkout -b feature/DGIT-XXX-feature-name`
- Follow naming convention: `feature/DGIT-XXX-descriptive-name`
- Example: `feature/DGIT-301-fastapi-service-skeleton`

#### 4. **Test-Driven Development (TDD)** 🧪

- Write comprehensive tests first (unit, integration, edge cases)
- **CRITICAL**: Use isolated test data and environment
- Ensure tests cover all acceptance criteria
- Use pytest with proper fixtures and mocking
- Target ≥ 85% test coverage for new code
- **NEVER use production data in tests**

#### 5. **Feature Implementation** 💻

- Implement the feature behavior following the acceptance criteria
- Use existing architecture patterns (Strategy, Repository, etc.)
- Follow the technical implementation notes from FEATURES.md
- Ensure type safety with mypy compliance

#### 6. **Acceptance Criteria Validation** ✅

- Verify all acceptance criteria are met
- Run the complete test suite with isolation
- Validate against business requirements
- Document any deviations or improvements

#### 7. **Code Quality & Best Practices** 🏗️

- Follow SOLID principles (Single Responsibility, Open/Closed, etc.)
- Write clean, readable, and maintainable code
- Use dependency injection and loose coupling
- Ensure proper error handling and logging
- Follow the project's coding standards (Black, Ruff, MyPy)

#### 8. **Code Review & Merge** 🔄

- Push feature branch to repository
- Create pull request with detailed description
- Include:
  - Feature summary and business value
  - Technical implementation details
  - Test coverage report
  - Any breaking changes or migration notes
- Address review feedback
- Merge to main branch
- Update feature status to "✅ Complete" in FEATURES.md

### Quality Gates

Each feature must pass these quality gates before merging:

- ✅ **Tests**: All tests pass with ≥ 85% coverage
- ✅ **Test Isolation**: Tests use isolated environment and data
- ✅ **Linting**: Ruff, Black, and MyPy checks pass
- ✅ **Security**: Bandit security scan passes
- ✅ **Documentation**: README and docstrings updated
- ✅ **Acceptance Criteria**: All criteria met and validated

### Branch Naming Convention

```
feature/DGIT-XXX-descriptive-name
```

Examples:

- `feature/DGIT-301-fastapi-service-skeleton`
- `feature/DGIT-401-finviz-scraper-tool`
- `feature/DGIT-403-research-agent-orchestrator`

### Commit Message Convention

Follow conventional commits:

```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- test: adding or updating tests
- refactor: code refactoring
- chore: maintenance tasks
```

### Pull Request Template

```markdown
## Feature Summary

- **Feature ID**: DGIT-XXX
- **Title**: Brief description
- **Business Value**: What problem does this solve?

## Technical Implementation

- **Files Changed**: List of key files
- **Architecture**: How it fits into existing patterns
- **Dependencies**: New dependencies added

## Testing

- **Coverage**: Test coverage percentage
- **Test Types**: Unit, integration, etc.
- **Test Isolation**: Confirmed isolated test environment
- **Edge Cases**: Special scenarios tested

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Breaking Changes

- None / List any breaking changes

## Migration Notes

- Any required migration steps
```

---

## 🏗️ **Architecture & Design Principles**

### **SOLID Principles Implementation**

This project strictly follows SOLID principles. All code must adhere to these standards:

#### **1. Single Responsibility Principle (SRP)**

**Rule**: Every class should have only one reason to change.

**Implementation Guidelines**:

```python
# ✅ GOOD: Single responsibility
class DataLoader:
    """Responsible only for loading data."""
    def load_universe(self) -> DataFrame: ...

class ResourceManager:
    """Responsible only for resource management."""
    def track_resource(self, resource: Any): ...

# ❌ BAD: Multiple responsibilities
class Screener:
    """Handles screening, data loading, validation, and API responses."""
    def screen(self): ...
    def load_data(self): ...
    def validate_data(self): ...
    def format_response(self): ...
```

**Best Practices**:

- Each class should have a clear, single purpose
- Extract focused services for different concerns
- Use dependency injection to compose functionality
- Keep methods focused on one task

#### **2. Open/Closed Principle (OCP)**

**Rule**: Software entities should be open for extension but closed for modification.

**Implementation Guidelines**:

```python
# ✅ GOOD: Open for extension
class ScoringStrategy(ABC):
    @abstractmethod
    def calculate_score(self, company: CompanyData) -> float: ...

class DefaultScoring(ScoringStrategy):
    def calculate_score(self, company: CompanyData) -> float: ...

class AdvancedScoring(ScoringStrategy):
    def calculate_score(self, company: CompanyData) -> float: ...

# Strategy registry for runtime extension
class ScoringRegistry:
    _strategies: Dict[str, Type[ScoringStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy: Type[ScoringStrategy]):
        cls._strategies[name] = strategy

# ❌ BAD: Requires modification to add new strategies
class Screener:
    def calculate_score(self, company: CompanyData) -> float:
        if self.strategy == "default":
            return self._default_score(company)
        elif self.strategy == "advanced":
            return self._advanced_score(company)
        # Need to modify this method for new strategies
```

**Best Practices**:

- Use abstract base classes and interfaces
- Implement strategy patterns for algorithms
- Use dependency injection for behavior composition
- Create registries for runtime extension

#### **3. Liskov Substitution Principle (LSP)**

**Rule**: Subtypes must be substitutable for their base types.

**Implementation Guidelines**:

```python
# ✅ GOOD: Proper inheritance
class CompanyDataRepository(ABC):
    @abstractmethod
    def get_rows(self) -> List[CompanyData]: ...

class CsvCompanyDataRepository(CompanyDataRepository):
    def get_rows(self) -> List[CompanyData]: ...

class DatabaseCompanyDataRepository(CompanyDataRepository):
    def get_rows(self) -> List[CompanyData]: ...

# Can substitute any implementation
def process_data(repo: CompanyDataRepository):
    data = repo.get_rows()  # Works with any implementation

# ❌ BAD: Violates LSP
class BaseRepository:
    def get_rows(self) -> List[CompanyData]: ...

class AsyncRepository(BaseRepository):
    async def get_rows(self) -> List[CompanyData]:  # Different signature!
        ...
```

**Best Practices**:

- Ensure derived classes can be used anywhere the base class is expected
- Maintain consistent method signatures
- Don't throw new exceptions that base class doesn't throw
- Preserve behavioral contracts

#### **4. Interface Segregation Principle (ISP)**

**Rule**: Clients should not be forced to depend on interfaces they don't use.

**Implementation Guidelines**:

```python
# ✅ GOOD: Focused interfaces
class DataReader(ABC):
    @abstractmethod
    def read_data(self) -> List[CompanyData]: ...

class DataValidator(ABC):
    @abstractmethod
    def validate_data(self, data: List[CompanyData]) -> List[CompanyData]: ...

class DataCache(ABC):
    @abstractmethod
    def get_cached_data(self) -> Optional[List[CompanyData]]: ...

# Clients depend only on what they need
class ScreeningService:
    def __init__(self, reader: DataReader, validator: DataValidator):
        self._reader = reader
        self._validator = validator

# ❌ BAD: Large interface forcing unnecessary dependencies
class DataManager(ABC):
    @abstractmethod
    def read_data(self) -> List[CompanyData]: ...
    @abstractmethod
    def validate_data(self, data: List[CompanyData]) -> List[CompanyData]: ...
    @abstractmethod
    def cache_data(self, data: List[CompanyData]): ...
    @abstractmethod
    def backup_data(self, data: List[CompanyData]): ...
    @abstractmethod
    def archive_data(self, data: List[CompanyData]): ...
```

**Best Practices**:

- Create small, focused interfaces
- Use composition over inheritance
- Split large interfaces into smaller, cohesive ones
- Design interfaces from the client's perspective

#### **5. Dependency Inversion Principle (DIP)**

**Rule**: High-level modules should not depend on low-level modules. Both should depend
on abstractions.

**Implementation Guidelines**:

```python
# ✅ GOOD: Depend on abstractions
class ScreeningService:
    def __init__(
        self,
        data_loader: DataLoader,  # Abstract interface
        scoring_strategy: ScoringStrategy,  # Abstract interface
        filter_strategy: FilterStrategy,  # Abstract interface
    ):
        self._data_loader = data_loader
        self._scoring_strategy = scoring_strategy
        self._filter_strategy = filter_strategy

# Factory creates concrete implementations
class ServiceFactory:
    def create_screening_service(self) -> ScreeningService:
        return ScreeningService(
            data_loader=self.create_data_loader(),
            scoring_strategy=self.create_scoring_strategy(),
            filter_strategy=self.create_filter_strategy(),
        )

# ❌ BAD: Direct dependency on concrete classes
class ScreeningService:
    def __init__(self):
        self._data_loader = CsvCompanyDataRepository()  # Concrete dependency
        self._scoring_strategy = DefaultScoring()  # Concrete dependency
```

**Best Practices**:

- Define interfaces for all dependencies
- Use dependency injection containers
- Create factories for object creation
- Mock interfaces in tests, not concrete classes

### **Design Patterns**

#### **Strategy Pattern**

Use for interchangeable algorithms:

```python
class ScoringStrategy(ABC):
    @abstractmethod
    def calculate_score(self, company: CompanyData) -> float: ...

class DefaultScoring(ScoringStrategy):
    def calculate_score(self, company: CompanyData) -> float:
        return company.dividend_yield * 0.4 + company.fcf_yield * 0.6

class ConservativeScoring(ScoringStrategy):
    def calculate_score(self, company: CompanyData) -> float:
        return company.dividend_yield * 0.7 + company.fcf_yield * 0.3
```

#### **Repository Pattern**

Use for data access abstraction:

```python
class CompanyDataRepository(ABC):
    @abstractmethod
    def get_rows(self) -> List[CompanyData]: ...
    @abstractmethod
    async def get_rows_async(self) -> List[CompanyData]: ...

class CsvCompanyDataRepository(CompanyDataRepository):
    def __init__(self, file_path: str, validator: DataValidator):
        self._file_path = file_path
        self._validator = validator
```

#### **Factory Pattern**

Use for object creation:

```python
class ServiceFactory:
    def create_data_loader(self, source: str) -> DataLoader:
        if source == "csv":
            return CsvDataLoader()
        elif source == "database":
            return DatabaseDataLoader()
        else:
            raise ValueError(f"Unknown data source: {source}")
```

#### **Observer Pattern**

Use for event handling:

```python
class ScreeningEvent(ABC):
    @abstractmethod
    def notify(self, data: Any): ...

class ScreeningService:
    def __init__(self, observers: List[ScreeningEvent]):
        self._observers = observers

    def screen(self, criteria: ScreeningCriteria):
        results = self._do_screening(criteria)
        for observer in self._observers:
            observer.notify(results)
```

### **Error Handling Patterns**

#### **Unified Exception Hierarchy**

```python
class DgiException(Exception):
    """Base exception for all DGI toolkit errors."""
    pass

class DataLoadError(DgiException):
    """Raised when data loading fails."""
    pass

class ValidationError(DgiException):
    """Raised when data validation fails."""
    pass

class ScreeningError(DgiException):
    """Raised when screening operations fail."""
    pass
```

#### **Proper Exception Handling**

```python
# ✅ GOOD: Specific exception handling
try:
    data = self._repository.get_rows()
except FileNotFoundError as e:
    logger.error(f"Data file not found: {e}")
    raise DataLoadError(f"Data file not found: {e}") from e
except ValidationError as e:
    logger.error(f"Data validation failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error loading data: {e}")
    raise DataLoadError(f"Unexpected error: {e}") from e

# ❌ BAD: Generic exception handling
try:
    data = self._repository.get_rows()
except Exception as e:  # Too broad
    print(f"Error: {e}")  # No logging, no context
    raise  # Loses original context
```

### **Async Programming Best Practices**

#### **Proper Async Error Handling**

```python
async def screen_async(self, timeout: float = 30.0) -> DataFrame:
    try:
        return await asyncio.wait_for(
            self._do_screening_async(),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Screening timed out after {timeout}s")
        raise ScreeningTimeoutError(f"Operation timed out after {timeout}s")
    except Exception as e:
        logger.error(f"Async screening failed: {e}")
        raise ScreeningError(f"Async screening failed: {e}") from e
```

#### **Resource Management**

```python
async def process_data_async(self):
    async with aiofiles.open(self._file_path, 'r') as file:
        content = await file.read()
        # File automatically closed after context
```

---

## ✅ **Before Committing Checklist**

**⚠️ MANDATORY: Complete this checklist before every commit!**

### **🧪 Testing & Isolation (CRITICAL)**

- [ ] **Run tests with isolation**: `make test` or `./scripts/run-tests.sh`
- [ ] **Verify test environment**: `echo $DGI_ENVIRONMENT` should be "test"
- [ ] **Check test data usage**: All tests use `TEST*` symbols (no real company data)
- [ ] **Confirm API keys cleared**: `echo $OPENAI_API_KEY` should be empty
- [ ] **Test coverage**: Run `make test-coverage` for new features
- [ ] **Test isolation validation**: Verify tests don't access production data

```bash
# Quick isolation check
make test
echo "Environment: $DGI_ENVIRONMENT"
echo "Data path: $DGI_DATA_PATH"
echo "API keys: ${OPENAI_API_KEY:-'CLEARED'}"
```

### **🔍 Code Quality & Standards**

- [ ] **Run quality checks**: `make quality` or `./scripts/check-quality.sh`
- [ ] **Format code**: `poetry run ruff format .` (auto-fixes formatting)
- [ ] **Lint code**: `poetry run ruff check .` (no errors)
- [ ] **Type checking**: `poetry run mypy dgi/` (core business logic only)
- [ ] **Security scan**: `poetry run bandit -r dgi/` (no high/critical issues)
- [ ] **Import sorting**: `poetry run isort .` (imports properly organized)

### **📝 Documentation & Commit**

- [ ] **Update documentation**: README, docstrings, or relevant docs
- [ ] **Conventional commit**: Use proper format (`feat:`, `fix:`, `docs:`, etc.)
- [ ] **Clear commit message**: Descriptive and concise
- [ ] **No debug code**: Remove `print()`, `debugger`, or temporary code
- [ ] **No sensitive data**: No API keys, passwords, or secrets in code

### **🏗️ Architecture & Best Practices**

- [ ] **SOLID principles**: Code follows single responsibility, dependency injection
- [ ] **Error handling**: Proper exception handling and logging
- [ ] **Type safety**: Type hints for new functions and classes
- [ ] **Test coverage**: New code has adequate test coverage
- [ ] **No hardcoded values**: Use configuration or environment variables

### **🚨 Security & Safety**

- [ ] **No production data**: Tests use only test data with `TEST*` symbols
- [ ] **No API keys in code**: Use environment variables for sensitive data
- [ ] **No secrets in commits**: Check for accidental credential commits
- [ ] **Input validation**: Validate all user inputs and API parameters
- [ ] **Error messages**: Don't expose sensitive information in error messages

### **🔄 Pre-commit Validation**

```bash
# Complete pre-commit checklist
echo "=== PRE-COMMIT CHECKLIST ==="

# 1. Test isolation
echo "1. Running tests with isolation..."
make test

# 2. Quality checks
echo "2. Running quality checks..."
make quality

# 3. Environment validation
echo "3. Validating environment..."
echo "DGI_ENVIRONMENT: $DGI_ENVIRONMENT"
echo "DGI_DATA_PATH: $DGI_DATA_PATH"
echo "API Keys cleared: ${OPENAI_API_KEY:-'YES'}"

# 4. Test data validation
echo "4. Validating test data..."
if grep -r "TEST[0-9]" tests/ > /dev/null; then
    echo "✅ Test data uses TEST* symbols"
else
    echo "❌ WARNING: No TEST* symbols found in tests!"
fi

echo "=== CHECKLIST COMPLETE ==="
```

### **🚨 Common Mistakes to Avoid**

- ❌ **Using production data in tests** (use `TEST*` symbols only)
- ❌ **Committing API keys or secrets** (use environment variables)
- ❌ **Skipping quality checks** (always run `make quality`)
- ❌ **Incomplete test coverage** (aim for ≥ 85% coverage)
- ❌ **Non-conventional commit messages** (use `feat:`, `fix:`, etc.)
- ❌ **Debug code in commits** (remove `print()`, `debugger`)
- ❌ **Hardcoded configuration** (use environment variables)
- ❌ **Breaking existing functionality** (ensure backward compatibility)
- ❌ **Violating SOLID principles** (follow design principles)
- ❌ **Poor error handling** (use proper exception hierarchy)
- ❌ **Missing type hints** (add types to all new code)

### **🆘 Quick Fixes**

```bash
# If tests fail
make test  # Check for isolation issues

# If quality checks fail
make quality  # Auto-fixes most issues

# If environment issues
make clean
./scripts/run-tests.sh --help

# If commit fails pre-commit hooks
git add .  # Re-add files after auto-fixes
git commit -m "feat: your message"
```

---

## 🧪 **Testing Best Practices & Environment Isolation**

### **CRITICAL: Test Environment Isolation**

**⚠️ NEVER use production data in tests!** This is a fundamental requirement for all
development work.

#### **Test Isolation Requirements**

1. **🔒 Data Isolation**
   - Use test data with `TEST*` symbols (e.g., `TEST1`, `TEST2`)
   - Never use real company names or symbols in tests
   - Test data should be predictable and minimal
   - All test data files should be in `tests/test_data/`

2. **🌍 Environment Isolation**
   - Set `DGI_ENVIRONMENT=test` for all tests
   - Clear sensitive API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
   - Use isolated file paths for test data
   - Restore original environment after tests

3. **🛡️ Security Protection**
   - API keys are automatically cleared in test environment
   - Test data contains no sensitive information
   - Tests cannot access production systems
   - All external dependencies are mocked when needed

### **Automated Test Execution**

We provide automated tools to ensure proper test isolation:

#### **Using Make Commands (Recommended)**

```bash
# Run all tests with isolation
make test

# Run specific test types
make test-unit
make test-integration
make test-api
make test-fast

# Run tests with coverage
make test-coverage

# Start test server with isolated data
make test-server
```

#### **Using Test Script Directly**

```bash
# Run all tests
./scripts/run-tests.sh

# Run API tests with coverage
./scripts/run-tests.sh -c api

# Start test server
./scripts/run-tests.sh -s

# Get help
./scripts/run-tests.sh --help
```

#### **Manual pytest (Advanced)**

```bash
# Set environment variables manually
export DGI_ENVIRONMENT=test
export DGI_DATA_PATH=tests/test_data/test_fundamentals.csv
unset OPENAI_API_KEY
unset ANTHROPIC_API_KEY

# Run tests
poetry run pytest
```

### **Test Data Management**

#### **Test Data Structure**

```
tests/
├── test_data/
│   └── test_fundamentals.csv  # Isolated test data
├── conftest.py               # Test configuration
└── test_*.py                 # Test files
```

#### **Test Data Content**

```csv
symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield
TEST1,Test Company 1,Technology,Software,0.025,30.0,0.08,5.0
TEST2,Test Company 2,Healthcare,Pharmaceuticals,0.035,45.0,0.12,4.5
TEST3,Test Company 3,Consumer,Retail,0.020,25.0,0.06,3.8
```

### **Test Validation**

#### **Verify Test Isolation**

```python
def test_environment_isolation(self, test_client: TestClient):
    """Verify we're using test environment and data."""
    import os

    # Check environment
    assert os.environ.get("DGI_ENVIRONMENT") == "test"
    assert "OPENAI_API_KEY" not in os.environ

    # Check test data usage
    response = test_client.get("/api/v1/screen", params={"top_n": 10})
    data = response.json()

    if data:
        symbols = [stock["symbol"] for stock in data]
        assert all(symbol.startswith("TEST") for symbol in symbols)
```

### **Development Workflow with Testing**

#### **Daily Development Workflow**

```bash
# 1. Start development
git checkout -b feature/my-feature

# 2. Write tests first (TDD)
make test-unit  # Run unit tests during development

# 3. Implement feature
# ... write code ...

# 4. Test frequently
make test  # Run all tests with isolation

# 5. Quality checks
make quality  # Run all quality checks

# 6. Commit with isolation
git add .
git commit -m "feat: implement feature with isolated tests"
```

#### **Before Committing**

```bash
# Always run these before committing:
make test        # Ensure all tests pass with isolation
make quality     # Ensure code quality standards
```

### **Common Testing Scenarios**

#### **Adding New API Endpoints**

```python
# 1. Write test first
def test_new_endpoint(self, test_client: TestClient):
    """Test new endpoint with isolated data."""
    response = test_client.get("/api/v1/new-endpoint")
    assert response.status_code == 200
    # Verify response structure and test data usage

# 2. Implement endpoint
@app.get("/api/v1/new-endpoint")
async def new_endpoint():
    # Implementation using get_screener() (uses environment data)
    pass

# 3. Run tests
make test-api
```

#### **Adding New Data Sources**

```python
# 1. Create test data file
# tests/test_data/test_new_source.csv

# 2. Update test fixtures
@pytest.fixture
def test_new_source_file(test_data_dir: Path) -> Path:
    return test_data_dir / "test_new_source.csv"

# 3. Write tests with isolation
def test_new_data_source(self, test_new_source_file: Path):
    # Test with isolated data
    pass
```

### **Troubleshooting Test Issues**

#### **Test Environment Problems**

```bash
# Check current environment
echo $DGI_ENVIRONMENT
echo $DGI_DATA_PATH

# Reset test environment
make clean
./scripts/run-tests.sh --help
```

#### **Test Data Issues**

```bash
# Recreate test data
rm -rf tests/test_data/
make test  # This will recreate test data automatically
```

#### **Coverage Issues**

```bash
# Run with coverage to see what's missing
make test-coverage

# View coverage report
open htmlcov/index.html
```

---

## 🏗️ **Code Quality & Standards**

### **Type Safety Requirements**

#### **Core Business Logic (`dgi/` package)**

- ✅ **100% type safety** with strict mypy configuration
- ✅ **Type hints** for all functions, methods, and variables
- ✅ **Generic types** for collections and complex data structures
- ✅ **Protocols** for structural typing when appropriate

```python
# ✅ GOOD: Proper type hints
from typing import List, Dict, Optional, Union
from pandas import DataFrame

def calculate_score(
    company: CompanyData,
    weights: Dict[str, float],
    threshold: Optional[float] = None
) -> float:
    """Calculate company score with proper type hints."""
    pass

# ❌ BAD: Missing type hints
def calculate_score(company, weights, threshold=None):
    """Missing type information."""
    pass
```

#### **API Layer (`api/` package)**

- ✅ **Pydantic models** for request/response validation
- ✅ **Type hints** for all endpoint functions
- ✅ **Proper Field definitions** with modern Pydantic syntax

```python
# ✅ GOOD: Modern Pydantic usage
from pydantic import BaseModel, Field, ConfigDict

class ScreeningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_yield: float = Field(
        ge=0.0,
        le=1.0,
        description="Minimum dividend yield",
        examples=[0.03, 0.05]
    )
    top_n: int = Field(
        ge=1,
        le=100,
        description="Number of top results",
        examples=[10, 25]
    )

# ❌ BAD: Deprecated Pydantic syntax
class ScreeningRequest(BaseModel):
    class Config:
        extra = "forbid"

    min_yield: float = Field(
        ge=0.0,
        le=1.0,
        description="Minimum dividend yield",
        example=0.03  # Deprecated: use examples
    )
```

### **Error Handling Standards**

#### **Unified Exception Hierarchy**

```python
# Base exception for all DGI toolkit errors
class DgiException(Exception):
    """Base exception for all DGI toolkit errors."""
    pass

# Specific exception types
class DataLoadError(DgiException):
    """Raised when data loading fails."""
    pass

class ValidationError(DgiException):
    """Raised when data validation fails."""
    pass

class ScreeningError(DgiException):
    """Raised when screening operations fail."""
    pass

class ConfigurationError(DgiException):
    """Raised when configuration is invalid."""
    pass
```

#### **Proper Exception Handling**

```python
# ✅ GOOD: Specific exception handling with context
try:
    data = self._repository.get_rows()
except FileNotFoundError as e:
    logger.error(f"Data file not found: {e}")
    raise DataLoadError(f"Data file not found: {e}") from e
except ValidationError as e:
    logger.error(f"Data validation failed: {e}")
    raise  # Re-raise validation errors as-is
except Exception as e:
    logger.error(f"Unexpected error loading data: {e}")
    raise DataLoadError(f"Unexpected error: {e}") from e

# ❌ BAD: Generic exception handling
try:
    data = self._repository.get_rows()
except Exception as e:  # Too broad
    print(f"Error: {e}")  # No logging, no context
    raise  # Loses original context
```

### **Logging Standards**

#### **Structured Logging**

```python
# ✅ GOOD: Structured logging with context
logger.info(
    "Screening completed successfully",
    extra={
        "correlation_id": correlation_id,
        "user_id": user_id,
        "parameters": {
            "min_yield": min_yield,
            "max_payout": max_payout,
            "top_n": top_n
        },
        "results": {
            "total_companies": len(results),
            "execution_time_ms": execution_time
        }
    }
)

# ❌ BAD: Simple string logging
logger.info(f"Screening completed with {len(results)} results")
```

#### **Log Levels**

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about program execution
- **WARNING**: Something unexpected happened but the program can continue
- **ERROR**: A serious problem occurred
- **CRITICAL**: A critical problem that may prevent the program from running

### **Configuration Management**

#### **Environment-Based Configuration**

```python
# ✅ GOOD: Environment-based configuration
from dgi.config import get_config

config = get_config()

# Use configuration values
min_yield = config.get("default_min_yield", 0.03)
max_payout = config.get("default_max_payout", 0.75)

# ❌ BAD: Hardcoded values
min_yield = 0.03  # Hardcoded
max_payout = 0.75  # Hardcoded
```

#### **Configuration Validation**

```python
# ✅ GOOD: Validate configuration at startup
def validate_config(config: Dict[str, Any]) -> None:
    required_keys = ["data_path", "log_level", "api_keys"]
    for key in required_keys:
        if key not in config:
            raise ConfigurationError(f"Missing required config key: {key}")

    if not os.path.exists(config["data_path"]):
        raise ConfigurationError(f"Data path does not exist: {config['data_path']}")
```

### **Performance Considerations**

#### **Async Operations**

```python
# ✅ GOOD: Proper async resource management
async def process_data_async(self):
    async with aiofiles.open(self._file_path, 'r') as file:
        content = await file.read()
        # File automatically closed after context

    # Process content asynchronously
    results = await self._process_content_async(content)
    return results

# ❌ BAD: Blocking operations in async context
async def process_data_async(self):
    with open(self._file_path, 'r') as file:  # Blocking!
        content = file.read()
    return content
```

#### **Caching Strategies**

```python
# ✅ GOOD: Proper caching with TTL
class CachedDataLoader:
    def __init__(self, data_loader: DataLoader, cache_ttl: int = 300):
        self._data_loader = data_loader
        self._cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache_timestamps:
            return False
        return time.time() - self._cache_timestamps[key] < self._cache_ttl
```

---

## Quality Assurance Workflow

This project maintains high code quality standards through automated checks and
validations.

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit to ensure code quality:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install
pre-commit install --hook-type commit-msg
```

**What gets checked automatically:**

1. **Code Formatting** 📝
   - `ruff format` - Modern Python formatter
   - `black` - Backup formatter
   - `isort` - Import sorting

2. **Linting & Auto-fixes** 🔧
   - `ruff` - Fast linter with 100+ rules
   - Auto-fixes: unused imports, syntax issues, style violations

3. **Type Checking** 🔍
   - `mypy` - Static type checking (core business logic only)
   - Ensures type safety in `dgi/` package

4. **Security** 🔒
   - `bandit` - Security vulnerability scanner
   - Checks for common security issues

5. **File Quality** 📄
   - Trailing whitespace removal
   - End-of-file newlines
   - YAML/TOML validation
   - Merge conflict detection

6. **Commit Messages** 💬
   - Conventional commit format validation
   - Examples: `feat:`, `fix:`, `docs:`, `refactor:`

### Manual Quality Checks

Run comprehensive quality checks before pushing:

```bash
# Run all quality checks (includes isolated tests)
make quality

# Or run individual tools
poetry run ruff check --fix .        # Linting with autofix
poetry run ruff format .             # Formatting
poetry run mypy --config-file mypy.ini dgi/  # Type checking
poetry run pytest tests/ --cov=dgi   # Tests with coverage
poetry run bandit -r dgi/            # Security scan
```

### Development Workflow

1. **Make Changes** ✏️

   ```bash
   # Create feature branch
   git checkout -b feature/your-feature

   # Make your changes
   # ... edit files ...
   ```

2. **Test with Isolation** 🧪

   ```bash
   # Run tests with proper isolation
   make test

   # Or run specific test types
   make test-unit
   make test-api
   ```

3. **Quality Checks** 🔍

   ```bash
   # Run all quality checks
   make quality

   # Or let pre-commit handle it
   git add .
   git commit -m "feat: your feature description"
   # Pre-commit hooks run automatically
   ```

4. **Commit & Push** 🚀
   ```bash
   # If pre-commit fixes files, add them and commit again
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature
   ```

### Configuration Files

- **`.pre-commit-config.yaml`** - Pre-commit hook configuration
- **`pyproject.toml`** - Tool configurations (ruff, isort, bandit, mypy)
- **`mypy.ini`** - MyPy type checking configuration
- **`pytest.ini`** - Pytest configuration with test isolation

### Quality Standards

**Core Business Logic (`dgi/` package):**

- ✅ 100% type safety (strict mypy)
- ✅ Comprehensive test coverage with isolation
- ✅ Security scanning
- ✅ Consistent formatting

**Test Files:**

- ✅ Proper type annotations
- ✅ Clear test documentation
- ✅ **MANDATORY**: Environment isolation
- ✅ **MANDATORY**: Test data isolation

**Documentation:**

- ✅ Auto-formatted with Prettier
- ✅ Consistent markdown style

### Troubleshooting

**Pre-commit failing?**

```bash
# Run hooks manually to see issues
pre-commit run --all-files

# Skip hooks temporarily (NOT recommended)
git commit --no-verify
```

**Type checking errors?**

```bash
# Check specific files
poetry run mypy --config-file mypy.ini dgi/models.py

# Focus on core business logic first
poetry run mypy --config-file mypy.ini dgi/ --no-error-summary
```

**Test isolation issues?**

```bash
# Check test environment
make test  # This ensures proper isolation

# Manual environment check
echo $DGI_ENVIRONMENT
echo $DGI_DATA_PATH
```

**Import organization issues?**

```bash
# Fix import sorting
poetry run isort .

# Check import configuration
poetry run isort --diff .
```

### Best Practices

1. **Commit Often** - Small, focused commits are easier to review
2. **Use Conventional Commits** - `feat:`, `fix:`, `docs:`, `refactor:`
3. **Test with Isolation** - Always use `make test` for proper isolation
4. **Focus on Core Logic** - Business logic in `dgi/` has highest standards
5. **Document Changes** - Update relevant documentation
6. **NEVER Use Production Data** - Always use test data with `TEST*` symbols
7. **Follow SOLID Principles** - Apply design principles consistently
8. **Use Type Hints** - Add types to all new code
9. **Handle Errors Properly** - Use the unified exception hierarchy
10. **Log Structured Data** - Include context in log messages

### CI/CD Integration

The same quality checks run in CI:

- All formatting and linting checks
- Type checking on core business logic
- Full test suite with isolation
- Security scanning

**CI will fail if:**

- Type checking fails on `dgi/` package
- Tests fail or coverage drops below threshold
- Security vulnerabilities detected
- Code formatting inconsistencies found
- **Test isolation is compromised**
- SOLID principles are violated
- Error handling is inadequate

---

## 🔧 **Technical Debt Management**

### **Current Technical Debt Status**

This project actively manages technical debt through systematic identification and
resolution. See `docs/tech-debt.md` for detailed tracking.

#### **Critical Items (Immediate Action Required)**

- **TD-013**: Pydantic Field Validation Type Safety Violations
- **TD-014**: Mixed Testing Framework Usage Violations

#### **High Priority Items (Next Sprint)**

- **TD-016**: Dependency Inversion Principle Violations
- **TD-017**: Open/Closed Principle Violations in Strategy Patterns
- **TD-018**: Interface Segregation Principle Violations
- **TD-019**: Inadequate Error Handling in Async Operations

### **Technical Debt Resolution Process**

1. **Identify**: Code reviews and automated analysis identify technical debt
2. **Prioritize**: Items are prioritized by impact and effort
3. **Plan**: Technical debt items are planned into development sprints
4. **Implement**: Developers address technical debt systematically
5. **Validate**: Changes are validated through tests and quality checks
6. **Document**: Completed items are moved to `docs/fixed-tech-debt.md`

### **Preventing Technical Debt**

- **Code Reviews**: All changes require peer review
- **Automated Checks**: CI/CD prevents introduction of new debt
- **Refactoring**: Regular refactoring sessions
- **Documentation**: Keep documentation up to date
- **Testing**: Maintain high test coverage

---

## 📚 **Reference Materials**

### **Books & Resources**

- **SOLID Principles**: Clean Architecture by Robert C. Martin
- **Design Patterns**: Gang of Four Design Patterns
- **Clean Code**: Clean Code by Robert C. Martin
- **Enterprise Patterns**: Patterns of Enterprise Application Architecture by Martin
  Fowler
- **Python Best Practices**: Effective Python by Brett Slatkin
- **API Design**: REST API Design Rulebook by Mark Masse
- **Testing**: Growing Object-Oriented Software, Guided by Tests by Freeman & Pryce

### **Online Resources**

- **Python Type Hints**: https://docs.python.org/3/library/typing.html
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pytest Documentation**: https://docs.pytest.org/
- **Ruff Documentation**: https://docs.astral.sh/ruff/

### **Project-Specific Resources**

- **Features Documentation**: `docs/FEATURES.md`
- **Technical Debt Tracking**: `docs/tech-debt.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Architecture Documentation**: `docs/ARCHITECTURE.md`

---

## 🎯 **Definition of Done**

A feature or fix is considered complete when:

- [x] All automated tests pass (507/507 ✅)
- [x] Code coverage maintained or improved (83% ✅)
- [ ] Type checking passes (mypy) - **FAILING: 4 errors**
- [x] Code style checks pass (ruff, black)
- [x] Documentation updated
- [x] Peer review completed
- [x] Manual testing performed for UI/API changes
- [x] SOLID principles followed
- [x] Error handling implemented properly
- [x] Logging includes appropriate context
- [x] Configuration uses environment variables
- [x] No hardcoded values in business logic
- [x] Test isolation verified
- [x] No production data used in tests
- [x] Security scan passes
- [x] Performance considerations addressed
- [x] Technical debt items identified and tracked

---

## 🚨 **Emergency Procedures**

### **Production Issues**

1. **Immediate Response**
   - Check application logs for errors
   - Verify environment configuration
   - Check external dependencies

2. **Rollback Procedure**
   - Revert to last known good deployment
   - Update status in monitoring systems
   - Notify stakeholders

3. **Post-Incident**
   - Document the incident
   - Identify root cause
   - Implement preventive measures
   - Update runbooks

### **Development Environment Issues**

1. **Test Environment Problems**

   ```bash
   make clean
   ./scripts/run-tests.sh --help
   ```

2. **Dependency Issues**

   ```bash
   poetry install --sync
   poetry lock --no-update
   ```

3. **Quality Check Failures**
   ```bash
   make quality
   # Address any remaining issues manually
   ```

### **Contact Information**

- **Technical Lead**: [Contact Information]
- **DevOps Team**: [Contact Information]
- **Emergency Hotline**: [Contact Information]

---

This development guide ensures consistent, high-quality development practices across the
entire team. All developers must follow these guidelines to maintain code quality,
security, and maintainability.
