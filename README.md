# DGI Toolkit

A comprehensive toolkit for Dividend Growth Investing (DGI) analysis, providing tools for screening stocks, building portfolios, and analyzing dividend-focused investment strategies.

## Quick Start

### Prerequisites

- **Python 3.12+** (latest version for security and features)
- **Poetry** (for dependency management)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dgi-toolkit
   ```

2. **Install dependencies using Poetry:**
   ```bash
   # Install Poetry if you haven't already
   curl -sSL https://install.python-poetry.org | python3 -

   # Install project dependencies
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

4. **Set up environment variables (optional):**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your API keys and preferences
   # Note: .env is gitignored for security
   ```

### Usage

#### Command Line Interface

Screen stocks using DGI criteria:
```bash
# Basic screening
dgi screen

# Custom parameters
dgi screen --min-yield 0.03 --max-payout 70 --min-cagr 0.08

# Build a portfolio
dgi build-portfolio --top-n 15 --weighting score
```

#### Python API

```python
from dgi.screener import Screener
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.validation import DgiRowValidator, PydanticRowValidation
from dgi.filtering import DefaultFilter, SectorFilter
from dgi.scoring import DefaultScoring
from dgi.models.company import CompanyData

# Set up screener with custom filtering
validator = DgiRowValidator(PydanticRowValidation(CompanyData))
repo = CsvCompanyDataRepository("data/fundamentals_small.csv", validator)

# Use sector-specific filtering
tech_filter = SectorFilter(["Technology", "Software"])
screener = Screener(
    repo, 
    filter_strategy=tech_filter,
    scoring_strategy=DefaultScoring()
)

# Load and filter data
df = screener.load_universe()
filtered = screener.apply_filters(df, min_yield=0.02, max_payout=80, min_cagr=0.05)
scored = screener.add_scores(filtered)
```

## Development

### Development Environment Setup

1. **Install development dependencies:**
   ```bash
   poetry install --with dev
   ```

2. **Install pre-commit hooks:**
   ```bash
   poetry run pre-commit install
   ```

3. **Run tests:**
   ```bash
   # All tests with coverage
   poetry run pytest

   # Specific test files
   poetry run pytest tests/test_filtering.py -v

   # With coverage report
   poetry run pytest --cov=dgi --cov-report=html
   ```

4. **Code formatting and linting:**
   ```bash
   # Format code
   poetry run black dgi/ tests/

   # Lint code
   poetry run ruff check dgi/ tests/

   # Type checking
   poetry run mypy dgi/
   ```

### Dependency Management

This project uses **Poetry** for dependency management. Key dependencies include:

**Core Dependencies:**
- `pandas ^2.3.1` - Data manipulation and analysis
- `pydantic ^2.0` - Data validation using type hints  
- `typer` - CLI framework
- `rich ^14.0.0` - Rich text and beautiful formatting

**AI/LLM Dependencies:**
- `langchain ^0.3.26` - LLM framework
- `openai ^1.97.1` - OpenAI API client
- `langchain-openai ^0.3.28` - LangChain OpenAI integration
- `langchain-anthropic ^0.3.17` - LangChain Anthropic integration

**Development Dependencies:**
- `pytest ^8.4.1` - Testing framework
- `pytest-cov ^6.2.1` - Coverage reporting
- `black ^25.1.0` - Code formatting
- `ruff ^0.12.4` - Fast Python linter
- `mypy ^1.17.0` - Static type checking

### Adding New Dependencies

```bash
# Add runtime dependency
poetry add package-name

# Add development dependency  
poetry add --group dev package-name

# Update dependencies
poetry update
```

### Docker Support

Build and run using Docker:

```bash
# Build image (uses Python 3.12 and amd64 architecture for CI/CD compatibility)
docker build --platform=linux/amd64 -t dgi-toolkit .

# Run container
docker run --rm dgi-toolkit python -m dgi.cli screen
```

### Architecture

The toolkit follows a modular architecture with strategy patterns:

- **Filtering Strategy**: Extensible filtering system (`dgi.filtering`)
  - `DefaultFilter`: Standard DGI criteria (yield, payout, growth)
  - `SectorFilter`: Sector-specific filtering with DGI criteria
  - `CompositeFilter`: Combines multiple filter strategies
  - `TopNFilter`: Limits results to top N stocks
- **Scoring Strategy**: Pluggable scoring algorithms (`dgi.scoring`) 
  - `DefaultScoring`: Balanced scoring across multiple metrics
  - Extensible for ESG, momentum, or custom scoring
- **Repository Pattern**: Data source abstraction (`dgi.repositories`)
  - `CsvCompanyDataRepository`: CSV file data source
  - Extensible for APIs, databases, or real-time data
- **Validation Strategy**: Configurable data validation (`dgi.validation`)
  - Pydantic-based type-safe validation
  - Graceful error handling and reporting

**Key Design Principles:**
- **Strategy Pattern**: Runtime behavior customization
- **Dependency Injection**: Improved testability and flexibility
- **Single Responsibility**: Each class has one focused purpose
- **Open/Closed**: Open for extension, closed for modification

**Example of Strategy Composition:**
```python
# Technology sector focus with custom filtering
tech_filter = CompositeFilter(
    SectorFilter(['Technology', 'Software']),
    TopNFilter(20, DefaultFilter())
)

screener = Screener(
    repository=CsvCompanyDataRepository(data_path, validator),
    filter_strategy=tech_filter,
    scoring_strategy=DefaultScoring()
)
```

### Testing

- **Unit Tests**: Comprehensive test coverage for all modules
- **Integration Tests**: End-to-end workflow testing
- **Coverage Target**: 85% minimum coverage enforced by CI

## Project Pitch

**dgi-toolkit** is a Python toolkit for building, analyzing, and managing Dividend Growth Investing portfolios. It aims to provide robust, extensible tools for research, automation, and reporting for DGI investors.

## Example CLI Output

```
  DGI Screen Results
  ┏━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━┳━━━━━━━━━━━┳━━━━━━━┓
  ┃Symbol┃Name              ┃Yield ┃Payout  ┃CAGR ┃FCF Yield ┃Score ┃
  ┡━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━╇━━━━━━━━━━━╇━━━━━━━┩
  ┃AAPL  ┃Apple Inc.        ┃0.60  ┃15.00   ┃8.50 ┃5.20      ┃0.178 ┃
  ┃MSFT  ┃Microsoft Corp.   ┃0.80  ┃35.00   ┃10.0 ┃7.00      ┃0.253 ┃
  ┃GOOG  ┃Alphabet Inc.     ┃0.70  ┃25.00   ┃12.0 ┃6.50      ┃0.276 ┃
  ┃JNJ   ┃Johnson & Johnson ┃2.50  ┃50.00   ┃6.00 ┃4.00      ┃0.120 ┃
  ┃PG    ┃Procter & Gamble  ┃1.20  ┃55.00   ┃5.50 ┃3.80      ┃0.089 ┃
  └───────┴──────────────────┴───────┴────────┴──────┴───────────┴───────┘
```

## Notebook Demo

You can try the full pipeline in your browser (no install needed):

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nabariho/dgi-toolkit/main?filepath=notebooks%2Fdgi_portfolio_builder.ipynb)

---

## License
MIT
