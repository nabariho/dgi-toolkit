# DGI Toolkit API Reference

This document provides detailed technical documentation for developers who want to
extend, integrate with, or contribute to the DGI Toolkit.

## 📚 Module Overview

```
dgi/
├── __init__.py              # Package initialization
├── cli.py                   # CLI commands (Typer)
├── cli_helpers.py           # CLI utility functions
├── config.py                # Configuration management
├── exceptions.py            # Custom exception types
├── filtering.py             # Filter strategy interfaces
├── portfolio.py             # Portfolio construction
├── screener.py              # Stock screening engine
├── scoring.py               # Scoring strategy interfaces
├── validation.py            # Data validation layer
├── models/
│   ├── __init__.py
│   └── company.py           # Pydantic data models
└── repositories/
    ├── __init__.py
    ├── base.py              # Abstract repository interface
    └── csv.py               # CSV repository implementation
```

---

## 🏗️ Core Interfaces

### CompanyDataRepository (Abstract Base)

**Purpose**: Abstract interface for data sources, enabling different data backends.

```python
from abc import ABC, abstractmethod
from typing import List
from dgi.models import CompanyData

class CompanyDataRepository(ABC):
    @abstractmethod
    def get_rows(self) -> List[CompanyData]:
        """
        Return a list of validated CompanyData objects from the data source.

        Returns:
            List[CompanyData]: Validated company financial data

        Raises:
            DataValidationError: If data validation fails
            IOError: If data source is inaccessible
        """
        pass
```

**Implementations:**

- `CsvCompanyDataRepository`: Reads from CSV files

**Future Extensions:**

- `DatabaseRepository`: SQL database integration
- `APIRepository`: Real-time API data feeds
- `ParquetRepository`: High-performance columnar storage

### ScoringStrategy (Abstract Base)

**Purpose**: Pluggable scoring algorithms for ranking stocks.

```python
from abc import ABC, abstractmethod
from dgi.models import CompanyData

class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, company: CompanyData) -> float:
        """
        Calculate a score for a company based on financial metrics.

        Args:
            company: CompanyData object with financial metrics

        Returns:
            float: Score between 0.0 and 1.0 (higher = better)
        """
        pass
```

**Implementations:**

- `DefaultScoring`: Balanced yield/growth/payout algorithm

**Future Extensions:**

- `MomentumScoring`: Price momentum-based scoring
- `ValueScoring`: Traditional value metrics
- `ESGScoring`: Environmental/social/governance factors

### WeightingStrategy (Abstract Base)

**Purpose**: Portfolio allocation algorithms.

```python
from abc import ABC, abstractmethod
from pandas import DataFrame

class WeightingStrategy(ABC):
    @abstractmethod
    def compute_weights(self, df: DataFrame) -> DataFrame:
        """
        Compute portfolio weights for selected stocks.

        Args:
            df: DataFrame with stock data and scores

        Returns:
            DataFrame: Same DataFrame with 'weight' column added
        """
        pass
```

**Implementations:**

- `EqualWeighting`: Equal allocation (1/N)
- `ScoreWeighting`: Score-proportional allocation

---

## 🔍 Data Models

### CompanyData (Pydantic Model)

**Purpose**: Validated financial data representation with type safety.

```python
from typing import Any
from pydantic import BaseModel, validator, Field
from pydantic.types import constr, confloat

class CompanyData(BaseModel):
    """Model for company financial data with validation."""

    # Required fields with constraints
    symbol: constr(min_length=1, max_length=10)           # Stock ticker
    name: constr(min_length=1)                            # Company name
    sector: constr(min_length=1)                          # Business sector
    industry: constr(min_length=1)                        # Industry classification
    dividend_yield: confloat(ge=0.0, le=100.0)           # % dividend yield
    payout_ratio: confloat(ge=0.0, le=200.0) = Field(alias="payout")  # % payout ratio
    dividend_growth_5y: confloat(ge=-50.0, le=100.0) = Field(alias="dividend_cagr")  # % 5-year CAGR
    fcf_yield: confloat(ge=-50.0, le=100.0)              # % free cash flow yield

    class Config:
        allow_population_by_field_name = True  # Support both field names and aliases

    # Backward compatibility properties
    @property
    def payout(self) -> float:
        return float(self.payout_ratio)

    @property
    def dividend_cagr(self) -> float:
        return float(self.dividend_growth_5y)

    @validator("dividend_yield", "payout_ratio", "dividend_growth_5y", "fcf_yield", pre=True)
    def must_be_number(cls, v: Any) -> float:
        """Ensure numeric fields can be converted to float."""
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except Exception:
            raise ValueError(f"Value '{v}' is not a valid number")
```

**Field Aliases:**

- `payout_ratio` ↔ `payout` (for CSV compatibility)
- `dividend_growth_5y` ↔ `dividend_cagr` (for CSV compatibility)

**Validation Rules:**

- Dividend yield: 0-100% (allows high-yield scenarios)
- Payout ratio: 0-200% (allows unsustainable payouts)
- Dividend growth: -50% to 100% (allows dividend cuts)
- FCF yield: -50% to 100% (allows negative FCF)

---

## 🔧 Core Components

### Screener Class

**Purpose**: Main screening engine with dependency injection.

```python
class Screener:
    """Screen companies based on DGI criteria."""

    def __init__(
        self,
        repository: CompanyDataRepository,
        filters: Optional[list[CompanyFilter]] = None,
        scoring_strategy: Optional[ScoringStrategy] = None,
    ) -> None:
        """
        Initialize screener with dependencies.

        Args:
            repository: Data source implementation
            filters: Optional list of filter strategies (future)
            scoring_strategy: Optional custom scoring algorithm
        """
        self._repository = repository
        self._filters = filters or []
        self._scoring_strategy = scoring_strategy

    def load_universe(self) -> DataFrame:
        """
        Load and validate the raw fundamentals universe.

        Returns:
            DataFrame: Validated data ready for screening

        Raises:
            DataValidationError: If validation fails
        """

    def apply_filters(
        self,
        df: DataFrame,
        min_yield: float = 0.0,
        max_payout: float = 100.0,
        min_cagr: float = 0.0,
    ) -> DataFrame:
        """
        Filter stocks by DGI criteria.

        Args:
            df: Universe DataFrame
            min_yield: Minimum dividend yield (decimal, e.g., 0.02 = 2%)
            max_payout: Maximum payout ratio (percentage, e.g., 80.0 = 80%)
            min_cagr: Minimum dividend CAGR (decimal, e.g., 0.05 = 5%)

        Returns:
            DataFrame: Filtered stocks meeting criteria
        """

    def add_scores(self, df: DataFrame) -> DataFrame:
        """
        Add composite scores for ranking.

        Args:
            df: Filtered DataFrame

        Returns:
            DataFrame: Same DataFrame with 'score' column added
        """

    def default_score(self, company: CompanyData) -> float:
        """
        Default scoring algorithm (if no strategy provided).

        Algorithm:
        - Yield Score: dividend_yield * 1.0
        - Growth Score: dividend_growth_5y * 0.5
        - Payout Penalty: max(0, payout_ratio - 60.0) * -0.1

        Args:
            company: CompanyData object

        Returns:
            float: Composite score
        """
```

### Portfolio Module

**Purpose**: Portfolio construction and analysis functions.

```python
def build(
    df: DataFrame,
    top_n: int,
    weighting: str = "equal",
    ticker_col: Optional[str] = None,
) -> DataFrame:
    """
    Build a portfolio by selecting top-N stocks and applying weighting.

    Args:
        df: DataFrame with at least 'score' column and ticker column
        top_n: Number of top stocks to select
        weighting: 'equal' or 'score'
        ticker_col: Optional override for ticker column name

    Returns:
        DataFrame: Portfolio with columns ['ticker', 'weight', 'score']

    Raises:
        ValueError: If top_n > len(df), missing columns, or invalid weighting
    """

def summary_stats(portfolio_df: DataFrame, universe_df: DataFrame) -> Dict[str, float]:
    """
    Calculate portfolio summary statistics.

    Args:
        portfolio_df: Portfolio DataFrame with weights
        universe_df: Full universe DataFrame for comparison

    Returns:
        Dict with keys: 'avg_yield', 'median_cagr', 'mean_payout'
    """
```

### Validation Layer

**Purpose**: Robust data validation with detailed error reporting.

```python
class DgiRowValidator:
    """Validates CSV rows for DGI analysis."""

    def __init__(self, strategy: RowValidationStrategy) -> None:
        """
        Initialize with validation strategy.

        Args:
            strategy: Implementation of RowValidationStrategy protocol
        """

    def validate_rows(self, rows: list[dict[str, Any]]) -> list[CompanyData]:
        """
        Validate a list of raw data rows.

        Args:
            rows: List of dictionaries from CSV/database

        Returns:
            List[CompanyData]: Successfully validated rows

        Raises:
            DataValidationError: If no valid rows found

        Behavior:
        - Logs validation errors for each invalid row
        - Continues processing after individual row failures
        - Raises exception only if ALL rows fail validation
        """

class PydanticRowValidation:
    """Pydantic-based validation strategy."""

    def __init__(self, model_class: type[CompanyData]) -> None:
        """
        Initialize with Pydantic model class.

        Args:
            model_class: CompanyData or subclass
        """

    def validate(self, row: dict[str, Any]) -> CompanyData:
        """
        Validate a single row using Pydantic.

        Args:
            row: Dictionary of field values

        Returns:
            CompanyData: Validated model instance

        Raises:
            ValidationError: If validation fails
        """
```

---

## 🖥️ CLI Interface

### Command Structure

**Framework**: Typer with Rich output formatting

```python
import typer
from typing import Optional

app = typer.Typer(help="DGI Toolkit CLI: screen stocks and build portfolios.")

@app.command()
def screen(
    min_yield: float = typer.Option(0.02, help="Minimum dividend yield"),
    max_payout: float = typer.Option(80.0, help="Maximum payout ratio (percentage)"),
    min_cagr: float = typer.Option(0.05, help="Minimum dividend CAGR"),
    csv_path: Optional[str] = typer.Option(None, help="Path to CSV file"),
) -> None:
    """Screen companies using DGI criteria and display in rich table."""

@app.command()
def build_portfolio(
    csv_path: str = typer.Option("data/fundamentals_small.csv", help="Path to CSV"),
    top_n: int = typer.Option(10, help="Number of stocks in portfolio"),
    weighting: str = typer.Option("equal", help="Weighting: 'equal' or 'score'"),
    min_yield: float = typer.Option(0.0, help="Minimum dividend yield"),
    max_payout: float = typer.Option(100.0, help="Maximum payout ratio"),
    min_cagr: float = typer.Option(0.0, help="Minimum dividend CAGR"),
) -> None:
    """Build portfolio from screened stocks."""
```

### CLI Helper Functions

```python
def render_screen_table(df: DataFrame) -> None:
    """
    Render screening results as a Rich table.

    Args:
        df: DataFrame with screening results and scores

    Features:
    - Color-coded columns (green for good metrics)
    - Sorted by score (descending)
    - Formatted percentages and decimals
    - Professional table styling
    """
```

---

## ⚙️ Configuration Management

### Environment Variables

```python
class Config:
    """Configuration with environment variable support."""

    def __init__(self) -> None:
        self.DATA_PATH = os.getenv("DGI_DATA_PATH", "data/fundamentals_small.csv")
        self.LOG_LEVEL = os.getenv("DGI_LOG_LEVEL", "INFO")
        self.DEFAULT_MIN_YIELD = float(os.getenv("DGI_MIN_YIELD", "0.0"))
        self.DEFAULT_MAX_PAYOUT = float(os.getenv("DGI_MAX_PAYOUT", "100.0"))
        self.DEFAULT_MIN_CAGR = float(os.getenv("DGI_MIN_CAGR", "0.0"))

def get_config() -> Config:
    """Get configuration instance (singleton pattern)."""
    return Config()
```

### Logging Configuration

```python
class JsonFormatter(logging.Formatter):
    """Structured JSON logging formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)
```

---

## 🚨 Exception Handling

### Custom Exceptions

```python
class DataValidationError(ValueError):
    """
    Raised when data validation fails in the DGI toolkit.

    Use Cases:
    - Invalid CSV data format
    - Missing required columns
    - All rows fail validation
    """
    pass
```

### Error Handling Patterns

**Graceful Degradation:**

```python
# Skip invalid rows, continue processing
try:
    validated = self._strategy.validate(row_str_keys)
    valid_rows.append(validated)
except ValidationError as e:
    logger.error(f"Row {i+2}: {e}")
    errors.append(error_msg)  # Collect but don't fail
```

**Fail Fast:**

```python
# Validate critical parameters immediately
if top_n > len(df):
    raise ValueError("top_n cannot be greater than number of stocks")
```

**User-Friendly CLI Errors:**

```python
try:
    # Business logic
except Exception as e:
    typer.echo(f"[ERROR] {e}", err=True)
    raise typer.Exit(code=1)
```

---

## 🧪 Testing Utilities

### Test Data Creation

```python
def create_test_company(**overrides) -> CompanyData:
    """
    Create a test CompanyData instance with sensible defaults.

    Args:
        **overrides: Field values to override defaults

    Returns:
        CompanyData: Test instance
    """
    defaults = {
        "symbol": "TEST",
        "name": "Test Company",
        "sector": "Technology",
        "industry": "Software",
        "dividend_yield": 3.0,
        "payout": 60.0,
        "dividend_cagr": 8.0,
        "fcf_yield": 5.0,
    }
    defaults.update(overrides)
    return CompanyData(**defaults)

def create_test_csv(tmp_path: Path, companies: List[dict]) -> Path:
    """
    Create a temporary CSV file for testing.

    Args:
        tmp_path: pytest temporary directory
        companies: List of company data dictionaries

    Returns:
        Path: Path to created CSV file
    """
```

### Mock Implementations

```python
class MockRepository(CompanyDataRepository):
    """Mock repository for testing."""

    def __init__(self, companies: List[CompanyData]):
        self.companies = companies

    def get_rows(self) -> List[CompanyData]:
        return self.companies

class MockScoringStrategy(ScoringStrategy):
    """Mock scoring strategy for testing."""

    def __init__(self, score_value: float = 0.5):
        self.score_value = score_value

    def score(self, company: CompanyData) -> float:
        return self.score_value
```

---

## 🔌 Extension Points

### Adding New Data Sources

1. **Implement Repository Interface:**

```python
class DatabaseRepository(CompanyDataRepository):
    def __init__(self, connection_string: str):
        self.connection = create_connection(connection_string)

    def get_rows(self) -> List[CompanyData]:
        # SQL query logic
        # Return List[CompanyData]
```

2. **Register with Dependency Injection:**

```python
repo = DatabaseRepository("postgresql://...")
screener = Screener(repo)
```

### Adding New Scoring Algorithms

1. **Implement Strategy Interface:**

```python
class MomentumScoring(ScoringStrategy):
    def score(self, company: CompanyData) -> float:
        # Custom scoring logic
        return calculated_score
```

2. **Use in Screener:**

```python
screener = Screener(repo, scoring_strategy=MomentumScoring())
```

### Adding New Weighting Methods

1. **Implement Strategy Interface:**

```python
class VolatilityWeighting(WeightingStrategy):
    def compute_weights(self, df: DataFrame) -> DataFrame:
        # Inverse volatility weighting
        df['weight'] = 1.0 / df['volatility']
        df['weight'] = df['weight'] / df['weight'].sum()
        return df
```

2. **Register in Portfolio Builder:**

```python
# Add to strategies dictionary in portfolio.py
strategies = {
    "equal": EqualWeighting(),
    "score": ScoreWeighting(),
    "volatility": VolatilityWeighting(),  # New strategy
}
```

---

## 📊 Performance Considerations

### Data Loading Optimization

```python
# Use efficient pandas operations
df_raw = pd.read_csv(csv_path, dtype=str)  # Read as strings initially
df_raw = df_raw.dropna()  # Remove NaN rows early

# Batch validation instead of row-by-row
records = df_raw.to_dict(orient="records")
validated = validator.validate_rows(records)
```

### Memory Management

```python
# Use copy() for DataFrame operations to avoid SettingWithCopyWarning
filtered = df.copy()
filtered = filtered[conditions]

# Clean up large DataFrames
del large_df
gc.collect()  # Force garbage collection if needed
```

### Scoring Performance

```python
# Vectorized operations when possible
df['score'] = (
    df['dividend_yield'] * 1.0 +
    df['dividend_cagr'] * 0.5 -
    (df['payout'] - 60.0).clip(lower=0) * 0.1
)

# Fallback to apply() for complex logic
df['score'] = df.apply(lambda row: complex_scoring_function(row), axis=1)
```

---

## 🔒 Security Considerations

### Input Validation

```python
# Validate file paths
if not Path(csv_path).exists():
    raise FileNotFoundError(f"CSV file not found: {csv_path}")

# Sanitize user inputs
min_yield = max(0.0, min_yield)  # Prevent negative values
max_payout = min(200.0, max_payout)  # Reasonable upper bound
```

### SQL Injection Prevention

```python
# Use parameterized queries for database repositories
cursor.execute(
    "SELECT * FROM companies WHERE sector = %s",
    (sector_filter,)  # Parameterized
)
```

### File System Security

```python
# Restrict file access to allowed directories
allowed_dir = Path("data").resolve()
requested_path = Path(csv_path).resolve()
if not str(requested_path).startswith(str(allowed_dir)):
    raise SecurityError("File access outside allowed directory")
```

---

This API reference provides the technical foundation for extending and integrating with
the DGI Toolkit. For business use cases and examples, see `FEATURES.md`.
