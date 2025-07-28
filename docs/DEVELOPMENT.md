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
