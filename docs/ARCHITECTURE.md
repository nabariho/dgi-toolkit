# DGI Toolkit Architecture

This document outlines the architectural decisions, design patterns, and system
organization of the DGI Toolkit.

## Overview

The DGI Toolkit follows a modular, strategy-pattern-based architecture that promotes
extensibility, testability, and separation of concerns. The system is designed to
support dividend growth investing (DGI) analysis through pluggable components.

## Core Architectural Principles

### 1. Strategy Pattern Implementation

The toolkit extensively uses the Strategy pattern to allow runtime behavior
customization:

- **Filtering Strategy**: Different stock filtering approaches
- **Scoring Strategy**: Various scoring algorithms
- **Validation Strategy**: Configurable data validation
- **Repository Pattern**: Abstracted data sources

### 2. Dependency Inversion

High-level modules depend on abstractions, not concretions:

```python
# Screener depends on interfaces, not implementations
class Screener:
    def __init__(
        self,
        repository: CompanyDataRepository,  # Interface
        filter_strategy: FilterStrategy,    # Interface
        scoring_strategy: ScoringStrategy   # Interface
    ):
```

### 3. Single Responsibility Principle

Each class has a focused, single responsibility:

- `Screener`: Orchestrates the screening workflow
- `FilterStrategy`: Implements filtering logic
- `ScoringStrategy`: Implements scoring algorithms
- `CompanyDataRepository`: Handles data access

## System Components

### Data Layer

#### Models (`dgi.models`)

```python
# Pydantic models for type safety and validation
class CompanyData(BaseModel):
    symbol: str
    dividend_yield: float
    payout_ratio: float
    # ... with validation constraints
```

#### Repositories (`dgi.repositories`)

```python
# Abstract base class
class CompanyDataRepository(ABC):
    @abstractmethod
    def get_rows(self) -> List[CompanyData]: ...

# Concrete implementations
class CsvCompanyDataRepository(CompanyDataRepository): ...
# Future: ApiCompanyDataRepository, DatabaseRepository, etc.
```

### Business Logic Layer

#### Filtering (`dgi.filtering`)

Strategy pattern for stock filtering:

```python
class FilterStrategy(ABC):
    @abstractmethod
    def filter(self, df: DataFrame, min_yield: float,
              max_payout: float, min_cagr: float) -> DataFrame: ...

# Implementations:
class DefaultFilter(FilterStrategy): ...          # Basic DGI criteria
class SectorFilter(FilterStrategy): ...           # Sector-specific filtering
class CompositeFilter(FilterStrategy): ...        # Combines multiple filters
class TopNFilter(FilterStrategy): ...             # Limits to top N stocks
```

#### Scoring (`dgi.scoring`)

Strategy pattern for scoring algorithms:

```python
class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, company: CompanyData) -> float: ...

class DefaultScoring(ScoringStrategy): ...        # Standard DGI scoring
# Future: ESGScoring, MomentumScoring, etc.
```

#### Core Engine (`dgi.screener`)

The main orchestrator that coordinates all strategies:

```python
class Screener:
    def __init__(
        self,
        repository: CompanyDataRepository,
        filter_strategy: FilterStrategy = DefaultFilter(),
        scoring_strategy: ScoringStrategy = DefaultScoring()
    ):
        # Uses dependency injection for all strategies

    def load_universe(self) -> DataFrame: ...      # Load data
    def apply_filters(self, ...) -> DataFrame: ... # Filter stocks
    def add_scores(self, ...) -> DataFrame: ...    # Score stocks
```

### Validation Layer (`dgi.validation`)

Type-safe validation using Pydantic:

```python
class DgiRowValidator:
    def __init__(self, strategy: RowValidationStrategy):
        self._strategy = strategy

    def validate_rows(self, rows: List[Dict]) -> List[CompanyData]:
        # Validates and converts raw data to typed models
```

### Application Layer

#### CLI (`dgi.cli`)

Command-line interface using Typer:

```python
@app.command()
def screen(min_yield: float, max_payout: float, min_cagr: float):
    # Configures strategies and runs screening
    screener = Screener(
        repo=CsvCompanyDataRepository(...),
        filter_strategy=DefaultFilter(),
        scoring_strategy=DefaultScoring()
    )
```

#### Portfolio Builder (`dgi.portfolio`)

Portfolio construction with different weighting strategies:

```python
class WeightingStrategy(ABC): ...
class EqualWeighting(WeightingStrategy): ...
class ScoreWeighting(WeightingStrategy): ...
```

## Key Architectural Decisions

### 1. Strategy Pattern Over Inheritance

**Decision**: Use composition with strategy interfaces rather than inheritance
hierarchies.

**Rationale**:

- Runtime strategy swapping
- Easier testing with mocks
- Better separation of concerns
- Avoids deep inheritance chains

**Example**:

```python
# Good: Composition with strategies
screener = Screener(repo, filter_strategy=SectorFilter(['Tech']))

# Avoided: Inheritance
class TechScreener(Screener): ...
```

### 2. Pydantic for Data Validation

**Decision**: Use Pydantic models for all data structures.

**Rationale**:

- Type safety at runtime
- Automatic validation
- JSON serialization
- IDE support and autocomplete

### 3. Repository Pattern for Data Access

**Decision**: Abstract data sources behind repository interfaces.

**Rationale**:

- Easy to swap data sources (CSV → API → Database)
- Simplified testing with mock repositories
- Clean separation of data access from business logic

### 4. Dependency Injection

**Decision**: Inject all dependencies through constructors.

**Rationale**:

- Improved testability
- Loose coupling
- Runtime configuration flexibility

## Extension Points

### Adding New Filter Strategies

```python
class ESGFilter(FilterStrategy):
    def __init__(self, min_esg_score: float):
        self.min_esg_score = min_esg_score

    def filter(self, df: DataFrame, ...) -> DataFrame:
        # Apply ESG criteria
        return df[df['esg_score'] >= self.min_esg_score]

# Usage
screener = Screener(repo, filter_strategy=ESGFilter(70))
```

### Adding New Data Sources

```python
class ApiCompanyDataRepository(CompanyDataRepository):
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    def get_rows(self) -> List[CompanyData]:
        # Fetch from API and validate
```

### Adding New Scoring Algorithms

```python
class MomentumScoring(ScoringStrategy):
    def score(self, company: CompanyData) -> float:
        # Implement momentum-based scoring
```

## Testing Strategy

### Unit Testing

- Each strategy tested in isolation
- Mock dependencies for fast, reliable tests
- 85% minimum coverage requirement

### Integration Testing

- End-to-end workflow testing
- Real data validation
- CLI interface testing

### Architecture Testing

```python
def test_screener_accepts_custom_strategies():
    # Verify strategy injection works
    custom_filter = Mock(spec=FilterStrategy)
    screener = Screener(repo, filter_strategy=custom_filter)
    assert screener._filter_strategy is custom_filter
```

## Performance Considerations

### DataFrame Operations

- Use vectorized pandas operations
- Avoid row-by-row iteration
- Leverage pandas' optimized filtering

### Memory Management

- Process data in chunks for large datasets
- Use lazy evaluation where possible
- Clean up intermediate DataFrames

### Caching Strategy

```python
# Future: Add caching layer
class CachedRepository(CompanyDataRepository):
    def __init__(self, underlying: CompanyDataRepository):
        self.underlying = underlying
        self._cache = {}
```

## Development Guidelines

### Adding New Features

1. Define interface/strategy first
2. Implement concrete strategy
3. Add comprehensive tests
4. Update documentation
5. Provide usage examples

### Code Organization

```
dgi/
├── models/          # Data models (Pydantic)
├── repositories/    # Data access layer
├── filtering.py     # Filtering strategies
├── scoring.py       # Scoring strategies
├── screener.py      # Main orchestrator
├── validation.py    # Data validation
├── cli.py          # Command-line interface
└── portfolio.py    # Portfolio construction
```

### Dependency Management

- Python 3.12+ for latest security updates
- Poetry for dependency management
- Locked versions for reproducibility
- Regular security updates

## Future Enhancements

### Planned Features

- **Database Support**: PostgreSQL repository implementation
- **API Integration**: Real-time data from financial APIs
- **Machine Learning**: ML-based scoring strategies
- **Web Interface**: React/FastAPI web application
- **Backtesting**: Historical performance analysis

### Architectural Evolution

- **Event-Driven Architecture**: For real-time updates
- **Microservices**: Split into focused services
- **GraphQL API**: Flexible data querying
- **Plugin System**: Runtime strategy loading

## Dependencies and Technology Stack

### Core Dependencies

- **pandas**: Data manipulation and analysis
- **pydantic**: Data validation and serialization
- **typer**: Command-line interface framework
- **rich**: Terminal output formatting

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking

### Infrastructure

- **Poetry**: Dependency management
- **Docker**: Containerization (Python 3.12, amd64)
- **GitHub Actions**: CI/CD pipeline
- **Pre-commit**: Git hooks for quality

This architecture provides a solid foundation for the DGI Toolkit while maintaining
flexibility for future enhancements and extensions.
