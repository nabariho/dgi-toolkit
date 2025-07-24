# Contributing to DGI Toolkit

We welcome contributions to the DGI Toolkit! This guide will help you understand our architecture, development process, and how to contribute effectively.

## Development Setup

### Prerequisites
- **Python 3.12+** (for latest security and features)
- **Poetry** (for dependency management)
- **Git** (for version control)

### Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd dgi-toolkit

# Set up Python 3.12 environment
poetry env use python3.12
poetry install

# Activate virtual environment
poetry shell

# Set up pre-commit hooks
poetry run pre-commit install

# Run tests to verify setup
poetry run pytest
```

## Architecture Guidelines

### Strategy Pattern Implementation
Our codebase extensively uses the Strategy pattern. When adding new features:

1. **Define the Interface First**
   ```python
   class NewStrategy(ABC):
       @abstractmethod
       def process(self, data: Input) -> Output: ...
   ```

2. **Implement Concrete Strategy**
   ```python
   class ConcreteStrategy(NewStrategy):
       def process(self, data: Input) -> Output:
           # Implementation here
   ```

3. **Integrate with Dependency Injection**
   ```python
   class Consumer:
       def __init__(self, strategy: NewStrategy = ConcreteStrategy()):
           self._strategy = strategy
   ```

### Adding New Filtering Strategies
To add a new filter strategy:

```python
# 1. Implement the FilterStrategy interface
class ESGFilter(FilterStrategy):
    def __init__(self, min_esg_score: float):
        self.min_esg_score = min_esg_score
    
    def filter(self, df: DataFrame, min_yield: float, 
              max_payout: float, min_cagr: float) -> DataFrame:
        # Apply base DGI filters first
        base_filtered = df[
            (df["dividend_yield"] >= min_yield)
            & (df["payout"] <= max_payout)
            & (df["dividend_cagr"] >= min_cagr)
        ]
        # Then apply ESG criteria
        return base_filtered[base_filtered["esg_score"] >= self.min_esg_score]

# 2. Add comprehensive tests
def test_esg_filter():
    filter_strategy = ESGFilter(min_esg_score=70)
    # Test implementation...

# 3. Document in filtering.py module docstring
# 4. Add usage example to README
```

## Code Quality Standards

### Testing Requirements
- **Minimum 85% test coverage** (enforced by CI)
- **Unit tests** for all strategies and business logic
- **Integration tests** for end-to-end workflows
- **Architecture tests** to verify strategy injection works

### Code Style
- **Black** for code formatting (`poetry run black dgi/ tests/`)
- **Ruff** for linting (`poetry run ruff check dgi/ tests/`)
- **MyPy** for type checking (`poetry run mypy dgi/`)
- **Pre-commit hooks** run automatically on commit

### Documentation
- **Docstrings** for all public classes and methods
- **Type hints** for all function signatures
- **README updates** for new features
- **Architecture documentation** for design decisions

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Implement Changes
Follow the architecture patterns:
- Use dependency injection
- Implement strategy interfaces
- Add comprehensive tests
- Update documentation

### 3. Run Quality Checks
```bash
# Format code
poetry run black dgi/ tests/

# Check linting
poetry run ruff check dgi/ tests/

# Type checking
poetry run mypy dgi/

# Run tests with coverage
poetry run pytest --cov=dgi --cov-report=term-missing

# Run pre-commit hooks
poetry run pre-commit run --all-files
```

### 4. Submit Pull Request
- Clear description of changes
- Reference any related issues
- Include test results
- Update documentation as needed

## Testing Guidelines

### Unit Testing
```python
def test_strategy_behavior():
    """Test individual strategy in isolation."""
    strategy = MyStrategy()
    result = strategy.process(test_input)
    assert result == expected_output

def test_dependency_injection():
    """Test that strategies can be injected."""
    mock_strategy = Mock(spec=StrategyInterface)
    consumer = Consumer(strategy=mock_strategy)
    assert consumer._strategy is mock_strategy
```

### Integration Testing
```python
def test_end_to_end_workflow():
    """Test complete workflow with real data."""
    screener = Screener(
        repository=CsvCompanyDataRepository(test_data_path, validator),
        filter_strategy=DefaultFilter(),
        scoring_strategy=DefaultScoring()
    )
    
    df = screener.load_universe()
    filtered = screener.apply_filters(df, min_yield=0.02, max_payout=80, min_cagr=0.05)
    scored = screener.add_scores(filtered)
    
    assert len(scored) > 0
    assert "score" in scored.columns
```

## Architectural Decisions

### When to Use Strategy Pattern
Use strategy pattern when:
- Algorithm needs to be swappable at runtime
- Multiple implementations exist for the same interface
- Testing requires mocking behavior
- Future extensions are likely

### When to Use Repository Pattern
Use repository pattern when:
- Data source might change (CSV → API → Database)
- Testing requires mock data sources
- Data access logic is complex
- Multiple data sources need the same interface

### Dependency Management
- **Poetry** for all dependency management
- **Python 3.12+** for security and performance
- **Locked dependencies** for reproducible builds
- **Regular updates** for security patches

## Common Patterns

### Error Handling
```python
def process_data(self, data: List[Dict]) -> List[ValidatedData]:
    valid_items = []
    errors = []
    
    for i, item in enumerate(data):
        try:
            validated = self.validate(item)
            valid_items.append(validated)
        except ValidationError as e:
            error_msg = f"Row {i+1}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    if not valid_items:
        raise DataValidationError(f"No valid items found. Errors:\n{chr(10).join(errors)}")
    
    if errors:
        logger.warning(f"Some items were invalid:\n{chr(10).join(errors)}")
    
    return valid_items
```

### Configuration
```python
# Use environment variables with sensible defaults
class Config:
    def __init__(self):
        self.data_path = os.getenv("DGI_DATA_PATH", "data/fundamentals_small.csv")
        self.min_yield = float(os.getenv("DGI_MIN_YIELD", "0.0"))
```

### Logging
```python
# Use structured logging with context
logger.info(
    "Applied filters: min_yield=%s, max_payout=%s, min_cagr=%s",
    min_yield, max_payout, min_cagr
)
logger.info(f"Filtered to {len(filtered)} rows from {len(df)} rows")
```

## Questions?

If you have questions about:
- **Architecture decisions**: Check `docs/ARCHITECTURE.md`
- **Development setup**: Follow this guide or ask in issues
- **Feature requests**: Create an issue with detailed requirements
- **Bug reports**: Include minimal reproduction case

Thank you for contributing to DGI Toolkit! 