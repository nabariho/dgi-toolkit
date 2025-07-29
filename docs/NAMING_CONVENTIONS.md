# Naming Conventions Guide - DGI Toolkit

This document establishes comprehensive naming conventions for the DGI Toolkit project
to ensure consistency, readability, and maintainability across the codebase.

## Table of Contents

- [General Principles](#general-principles)
- [Python Naming Conventions](#python-naming-conventions)
- [File and Directory Naming](#file-and-directory-naming)
- [API and Configuration Naming](#api-and-configuration-naming)
- [Database and Data Naming](#database-and-data-naming)
- [Testing Conventions](#testing-conventions)
- [Documentation Conventions](#documentation-conventions)

## General Principles

### Clarity Over Brevity

- Prefer descriptive names over short abbreviations
- Use full words when possible: `dividend_yield` instead of `div_yield`
- Avoid ambiguous names: use `screening_criteria` instead of `criteria`

### Consistency

- Follow the same naming pattern throughout the codebase
- Use established domain terminology consistently
- Maintain naming conventions across modules and packages

### Convention Adherence

- Follow Python PEP 8 naming conventions strictly
- Use snake_case for variables, functions, and modules
- Use PascalCase for classes and exceptions
- Use UPPER_SNAKE_CASE for constants

## Python Naming Conventions

### Variables and Functions

```python
# ✅ Good: snake_case
min_dividend_yield = 2.0
max_payout_ratio = 80.0
dividend_growth_rate = 5.0

def calculate_dgi_score(company_data: CompanyData) -> float:
    pass

def validate_screening_parameters(min_yield: float, max_payout: float) -> None:
    pass

# ❌ Bad: camelCase, abbreviations
minDividendYield = 2.0
maxPayoutRatio = 80.0
divGrowthRate = 5.0

def calcDgiScore(compData):
    pass
```

### Classes and Exceptions

```python
# ✅ Good: PascalCase with descriptive names
class CompanyDataRepository:
    pass

class ScreeningParameterValidator:
    pass

class DataValidationError(Exception):
    pass

class ConfigurationError(Exception):
    pass

# ❌ Bad: snake_case, unclear names
class company_data_repo:
    pass

class Validator:  # Too generic
    pass
```

### Constants

```python
# ✅ Good: UPPER_SNAKE_CASE
DEFAULT_MIN_DIVIDEND_YIELD = 2.0
MAX_PORTFOLIO_SIZE = 50
API_VERSION = "1.0.0"
DEFAULT_DATA_PATH = "data/fundamentals.csv"

# Configuration keys
CONFIG_DATABASE_URL = "DATABASE_URL"
CONFIG_API_HOST = "API_HOST"
CONFIG_LOG_LEVEL = "LOG_LEVEL"

# ❌ Bad: mixed case, unclear names
default_min_yield = 2.0  # Should be constant
MAX_SIZE = 50  # Too generic
```

### Method and Property Names

```python
# ✅ Good: descriptive method names
def load_company_data(self) -> List[CompanyData]:
    pass

def apply_dividend_growth_filter(self, min_cagr: float) -> DataFrame:
    pass

def calculate_composite_dgi_score(self) -> float:
    pass

@property
def current_portfolio_value(self) -> float:
    pass

# ❌ Bad: unclear or abbreviated names
def load_data(self):  # Too generic
    pass

def apply_filter(self, value):  # Unclear what filter
    pass

def calc_score(self):  # Abbreviated
    pass
```

## File and Directory Naming

### Python Files

```bash
# ✅ Good: snake_case, descriptive
screening_service.py
portfolio_optimizer.py
dividend_calculator.py
data_validation_utils.py

# ❌ Bad: camelCase, unclear
screeningService.py
portfolioOpt.py
utils.py  # Too generic
```

### Directory Structure

```bash
# ✅ Good: organized, clear hierarchy
dgi/
├── models/
│   ├── company.py
│   ├── portfolio.py
│   └── screening_criteria.py
├── services/
│   ├── screening_service.py
│   ├── portfolio_service.py
│   └── validation_service.py
├── repositories/
│   ├── base.py
│   ├── csv.py
│   └── interfaces.py
└── exceptions.py

# ❌ Bad: unclear organization
dgi/
├── stuff/
├── utils/
├── helpers/
└── misc/
```

### Configuration Files

```bash
# ✅ Good: clear purpose
api.yaml
core_settings.json
development.env
production.env

# ❌ Bad: unclear names
config.yaml
settings.json
dev.env
```

## API and Configuration Naming

### API Endpoints

```python
# ✅ Good: RESTful, clear resources
/api/v1/screening/stocks
/api/v1/portfolio/optimize
/api/v1/companies/{symbol}/analysis
/api/v1/health/detailed

# ❌ Bad: unclear actions
/api/screen
/api/get_data
/api/do_analysis
```

### Configuration Keys

```python
# ✅ Good: hierarchical, descriptive
API_HOST = "0.0.0.0"
API_PORT = 8000
API_CORS_ENABLED = True

DATABASE_URL = "sqlite:///dgi.db"
DATABASE_POOL_SIZE = 10

SCREENING_DEFAULT_MIN_YIELD = 2.0
SCREENING_DEFAULT_MAX_PAYOUT = 80.0

LOGGING_LEVEL = "INFO"
LOGGING_FORMAT = "structured"

# ❌ Bad: flat, unclear
HOST = "0.0.0.0"
PORT = 8000
DB = "sqlite:///dgi.db"
MIN_YIELD = 2.0
```

### Environment Variables

```bash
# ✅ Good: prefixed, hierarchical
DGI_API_HOST=0.0.0.0
DGI_API_PORT=8000
DGI_DATABASE_URL=postgresql://...
DGI_CORE_LOG_LEVEL=INFO
DGI_SCREENING_MIN_YIELD=2.0

# ❌ Bad: unprefixed, unclear
HOST=0.0.0.0
PORT=8000
DATABASE=postgresql://...
LEVEL=INFO
```

## Database and Data Naming

### DataFrame Columns

```python
# ✅ Good: snake_case, descriptive
df_columns = [
    "symbol",
    "company_name",
    "sector",
    "industry",
    "dividend_yield",
    "payout_ratio",
    "dividend_cagr_5y",
    "free_cash_flow_yield",
    "market_capitalization"
]

# ❌ Bad: camelCase, abbreviations
df_columns = [
    "Symbol",
    "companyName",
    "divYield",
    "payout",
    "cagr5y",
    "fcfYield",
    "mktCap"
]
```

### Model Field Names

```python
# ✅ Good: consistent with data source
class CompanyData(BaseModel):
    symbol: str
    name: str
    sector: str
    industry: str
    dividend_yield: float
    payout_ratio: float
    dividend_cagr: float
    fcf_yield: float

# ❌ Bad: inconsistent naming
class CompanyData(BaseModel):
    ticker: str  # Inconsistent with 'symbol'
    companyName: str  # camelCase
    div_yield: float  # Abbreviated
    payoutRatio: float  # Mixed case
```

## Testing Conventions

### Test File Names

```python
# ✅ Good: mirrors source structure
test_screening_service.py
test_portfolio_optimizer.py
test_company_data_model.py
test_api_endpoints.py

# ❌ Bad: unclear correspondence
screening_tests.py
portfolio_test.py
test_models.py  # Too generic
```

### Test Function Names

```python
# ✅ Good: descriptive test scenarios
def test_screening_service_filters_by_dividend_yield():
    pass

def test_portfolio_optimizer_handles_empty_universe():
    pass

def test_company_data_validation_rejects_negative_yield():
    pass

def test_api_returns_422_for_invalid_screening_parameters():
    pass

# ❌ Bad: unclear test purpose
def test_service():
    pass

def test_optimizer():
    pass

def test_validation():
    pass
```

### Test Class Names

```python
# ✅ Good: groups related functionality
class TestScreeningService:
    pass

class TestPortfolioOptimizer:
    pass

class TestCompanyDataValidation:
    pass

# ❌ Bad: unclear grouping
class ServiceTests:
    pass

class Tests:
    pass
```

## Documentation Conventions

### README and Documentation Files

```bash
# ✅ Good: clear purpose
README.md
ARCHITECTURE.md
API_REFERENCE.md
DEVELOPMENT.md
NAMING_CONVENTIONS.md
CHANGELOG.md

# ❌ Bad: unclear content
docs.md
info.md
notes.md
```

### Code Comments and Docstrings

```python
# ✅ Good: clear, descriptive
def calculate_dividend_growth_score(
    current_yield: float,
    historical_growth_rate: float,
    time_period_years: int
) -> float:
    """Calculate dividend growth score based on historical performance.

    The score considers both current dividend yield and historical growth
    rate to provide a composite measure of dividend attractiveness.

    Args:
        current_yield: Current annual dividend yield as a percentage
        historical_growth_rate: Average annual dividend growth rate over the period
        time_period_years: Number of years of historical data used

    Returns:
        Composite dividend growth score between 0.0 and 1.0

    Raises:
        ValueError: If yield or growth rate is negative
    """
    pass

# ❌ Bad: unclear or abbreviated
def calc_score(yield_val, growth, period):
    """Calc score."""  # Too brief
    pass
```

## Enforcement and Tools

### Automated Checks

The following tools help enforce naming conventions:

1. **Ruff**: Configured to check naming conventions
2. **MyPy**: Type checking ensures consistent interfaces
3. **Pre-commit hooks**: Automatic checks before commits

### Configuration Examples

#### Ruff Configuration

```toml
[tool.ruff.lint.pep8-naming]
# Enforce class names in PascalCase
classmethod-decorators = ["classmethod"]
staticmethod-decorators = ["staticmethod"]
```

#### Code Review Checklist

- [ ] Variable names use snake_case
- [ ] Class names use PascalCase
- [ ] Constants use UPPER_SNAKE_CASE
- [ ] Function names are descriptive
- [ ] No abbreviations unless domain-standard
- [ ] Consistent terminology throughout
- [ ] Clear distinction between similar concepts

## Domain-Specific Conventions

### Financial Terms

```python
# ✅ Good: consistent financial terminology
dividend_yield          # Not div_yield or dividendYield
payout_ratio            # Not payout or payoutRatio
free_cash_flow_yield    # Not fcf_yield (spell out)
dividend_cagr           # CAGR is standard abbreviation
market_capitalization   # Not market_cap (spell out in models)
price_to_earnings       # Not pe_ratio (spell out)

# Configuration can use abbreviations for brevity
DEFAULT_MIN_FCF_YIELD = 3.0  # OK in config
DEFAULT_PE_RATIO_MAX = 25.0  # OK in config
```

### DGI-Specific Terms

```python
# ✅ Good: established DGI terminology
dgi_score              # Dividend Growth Investing score
screening_criteria     # Not filter_criteria
dividend_aristocrat    # Standard DGI term
yield_on_cost         # Standard DGI calculation
```

## Migration and Refactoring

When updating naming conventions:

1. **Assess Impact**: Check for breaking changes
2. **Update Tests**: Ensure tests reflect new names
3. **Update Documentation**: Keep docs in sync
4. **Gradual Migration**: Use deprecation warnings for public APIs
5. **Communicate Changes**: Document breaking changes in CHANGELOG

## Conclusion

Consistent naming conventions improve code readability, maintainability, and team
collaboration. These guidelines should be followed for all new code and applied when
refactoring existing code.

For questions or exceptions to these conventions, discuss with the team and document any
project-specific decisions.
