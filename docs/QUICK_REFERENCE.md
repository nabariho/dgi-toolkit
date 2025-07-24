# DGI Toolkit Quick Reference

## Development Commands

### Environment Setup
```bash
# Set up development environment
poetry env use python3.12
poetry install
poetry shell

# Run tests
poetry run pytest                    # All tests
poetry run pytest tests/test_filtering.py -v  # Specific module
poetry run pytest --cov=dgi --cov-report=html # With coverage

# Code quality
poetry run black dgi/ tests/        # Format code
poetry run ruff check dgi/ tests/   # Lint code  
poetry run mypy dgi/                 # Type checking
poetry run pre-commit run --all-files # All hooks
```

### Docker
```bash
# Build and run
docker build --platform=linux/amd64 -t dgi-toolkit .
docker run --rm dgi-toolkit python -m dgi.cli screen
```

## Architecture Patterns

### Strategy Pattern Implementation

#### 1. Define Interface
```python
from abc import ABC, abstractmethod

class MyStrategy(ABC):
    @abstractmethod
    def process(self, data: Input) -> Output:
        """Process data according to strategy."""
        pass
```

#### 2. Implement Concrete Strategy
```python
class ConcreteStrategy(MyStrategy):
    def __init__(self, param: float):
        self.param = param
    
    def process(self, data: Input) -> Output:
        # Implementation here
        return result
```

#### 3. Inject into Consumer
```python
class Consumer:
    def __init__(self, strategy: MyStrategy = ConcreteStrategy()):
        self._strategy = strategy
    
    def execute(self, data: Input) -> Output:
        return self._strategy.process(data)
```

### Repository Pattern
```python
# Abstract interface
class DataRepository(ABC):
    @abstractmethod
    def get_data(self) -> List[Model]: ...

# Concrete implementation
class CsvDataRepository(DataRepository):
    def __init__(self, file_path: str, validator: Validator):
        self.file_path = file_path
        self.validator = validator
    
    def get_data(self) -> List[Model]:
        # Load and validate data
        return validated_data
```

## Common Workflows

### Adding New Filter Strategy

#### 1. Implement FilterStrategy
```python
# In dgi/filtering.py
class CustomFilter(FilterStrategy):
    def __init__(self, custom_param: float):
        self.custom_param = custom_param
    
    def filter(self, df: DataFrame, min_yield: float, 
              max_payout: float, min_cagr: float) -> DataFrame:
        # Apply base DGI filters
        base_filtered = df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]
        
        # Apply custom logic
        return base_filtered[base_filtered["custom_metric"] >= self.custom_param]
```

#### 2. Add Tests
```python
# In tests/test_filtering.py
class TestCustomFilter(unittest.TestCase):
    def test_custom_filter_behavior(self):
        filter_strategy = CustomFilter(custom_param=5.0)
        
        test_df = pd.DataFrame({
            "dividend_yield": [2.5, 3.0],
            "payout": [30.0, 40.0],
            "dividend_cagr": [6.0, 7.0],
            "custom_metric": [4.0, 6.0]
        })
        
        result = filter_strategy.filter(test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0)
        
        # Only second row should pass (custom_metric >= 5.0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["custom_metric"], 6.0)
```

#### 3. Usage Example
```python
# Usage in application
screener = Screener(
    repository=CsvCompanyDataRepository(data_path, validator),
    filter_strategy=CustomFilter(custom_param=5.0),
    scoring_strategy=DefaultScoring()
)
```

### Adding New Scoring Strategy

```python
# 1. Implement ScoringStrategy
class MomentumScoring(ScoringStrategy):
    def score(self, company: CompanyData) -> float:
        # Momentum-based scoring logic
        momentum = company.dividend_growth_5y * 0.4
        yield_score = company.dividend_yield * 0.3
        quality = (100 - company.payout_ratio) * 0.3
        return (momentum + yield_score + quality) / 100.0

# 2. Add tests
def test_momentum_scoring():
    scoring = MomentumScoring()
    company = CompanyData(...)
    score = scoring.score(company)
    assert 0.0 <= score <= 1.0

# 3. Use in screener
screener = Screener(repo, scoring_strategy=MomentumScoring())
```

### Adding New Data Repository

```python
# 1. Implement CompanyDataRepository
class ApiDataRepository(CompanyDataRepository):
    def __init__(self, api_client: ApiClient, validator: DgiRowValidator):
        self.api_client = api_client
        self.validator = validator
    
    def get_rows(self) -> List[CompanyData]:
        raw_data = self.api_client.fetch_companies()
        return self.validator.validate_rows(raw_data)

# 2. Add integration tests
def test_api_repository_integration():
    api_client = Mock(spec=ApiClient)
    api_client.fetch_companies.return_value = [...]
    
    repo = ApiDataRepository(api_client, validator)
    data = repo.get_rows()
    
    assert len(data) > 0
    assert all(isinstance(item, CompanyData) for item in data)

# 3. Use in screener
repo = ApiDataRepository(api_client, validator)
screener = Screener(repo)
```

## Testing Patterns

### Unit Test Template
```python
import unittest
from unittest.mock import Mock
import pandas as pd

class TestMyComponent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_dependency = Mock()
        self.component = MyComponent(self.mock_dependency)
    
    def test_happy_path(self):
        """Test normal operation."""
        # Arrange
        input_data = ...
        expected_output = ...
        
        # Act
        result = self.component.process(input_data)
        
        # Assert
        self.assertEqual(result, expected_output)
    
    def test_edge_case(self):
        """Test edge case handling."""
        # Test empty input, invalid data, etc.
    
    def test_error_handling(self):
        """Test error conditions."""
        with self.assertRaises(ExpectedError):
            self.component.process(invalid_input)
```

### Integration Test Template
```python
def test_end_to_end_workflow():
    """Test complete workflow with real components."""
    # Use real implementations, not mocks
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository(test_data_path, validator)
    screener = Screener(
        repository=repo,
        filter_strategy=DefaultFilter(),
        scoring_strategy=DefaultScoring()
    )
    
    # Test complete workflow
    df = screener.load_universe()
    filtered = screener.apply_filters(df, min_yield=0.02, max_payout=80, min_cagr=0.05)
    scored = screener.add_scores(filtered)
    
    # Verify results
    assert len(scored) > 0
    assert "score" in scored.columns
    assert all(scored["score"] >= 0.0)
```

## Configuration Patterns

### Environment Variables
```python
# dgi/config.py
class Config:
    def __init__(self):
        self.data_path = os.getenv("DGI_DATA_PATH", "data/fundamentals_small.csv")
        self.log_level = os.getenv("DGI_LOG_LEVEL", "INFO")
        self.min_yield = float(os.getenv("DGI_MIN_YIELD", "0.0"))

# Usage
config = get_config()
repo = CsvCompanyDataRepository(config.data_path, validator)
```

### Strategy Configuration
```python
# Runtime strategy selection
def create_screener(filter_type: str = "default", scoring_type: str = "default"):
    filters = {
        "default": DefaultFilter(),
        "sector": SectorFilter(["Technology"]),
        "esg": ESGFilter(min_esg_score=70),
    }
    
    scorers = {
        "default": DefaultScoring(),
        "momentum": MomentumScoring(),
    }
    
    return Screener(
        repository=repo,
        filter_strategy=filters[filter_type],
        scoring_strategy=scorers[scoring_type]
    )
```

## Error Handling Patterns

### Validation Errors
```python
def validate_and_process(self, data: List[Dict]) -> List[ValidatedModel]:
    valid_items = []
    errors = []
    
    for i, item in enumerate(data):
        try:
            validated = self.validator.validate(item)
            valid_items.append(validated)
        except ValidationError as e:
            error_msg = f"Row {i+1}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    if not valid_items:
        raise DataValidationError(f"No valid items. Errors:\n{chr(10).join(errors)}")
    
    return valid_items
```

### CLI Error Handling
```python
@app.command()
def command():
    try:
        # Business logic
        result = process_data()
        display_results(result)
    except ValidationError as e:
        typer.echo(f"[ERROR] Data validation failed: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"[ERROR] Unexpected error: {e}", err=True)
        raise typer.Exit(code=1)
```

## Quick Commands Reference

| Task | Command |
|------|---------|
| Run all tests | `poetry run pytest` |
| Test with coverage | `poetry run pytest --cov=dgi` |
| Format code | `poetry run black dgi/ tests/` |
| Lint code | `poetry run ruff check dgi/` |
| Type check | `poetry run mypy dgi/` |
| Pre-commit hooks | `poetry run pre-commit run --all-files` |
| CLI help | `poetry run dgi --help` |
| Screen stocks | `poetry run dgi screen --min-yield 0.03` |
| Build portfolio | `poetry run dgi build-portfolio --top-n 15` |
| Jupyter notebook | `poetry run jupyter notebook` |
| Docker build | `docker build --platform=linux/amd64 -t dgi-toolkit .` |

## File Structure Reference

```
dgi-toolkit/
├── dgi/                     # Main package
│   ├── models/             # Pydantic data models
│   ├── repositories/       # Data access layer
│   ├── providers/          # LLM integrations
│   ├── filtering.py        # Filtering strategies
│   ├── scoring.py          # Scoring strategies  
│   ├── screener.py         # Main orchestrator
│   ├── validation.py       # Data validation
│   ├── cli.py             # Command-line interface
│   ├── cli_helpers.py     # CLI utilities
│   ├── portfolio.py       # Portfolio construction
│   ├── config.py          # Configuration
│   └── exceptions.py      # Custom exceptions
├── tests/                  # Test suite
├── docs/                   # Documentation
├── data/                   # Sample data
├── notebooks/             # Jupyter notebooks
├── pyproject.toml         # Poetry configuration
├── Dockerfile            # Container definition
└── README.md             # Project overview
``` 