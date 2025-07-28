# DGI Toolkit Features & Business Use Cases

This document provides a comprehensive overview of all implemented features in the DGI
Toolkit, mapping to business requirements and use cases for Dividend Growth Investing
(DGI) portfolio management.

## 📋 Feature Status Overview

### Status Legend

- ✅ **Complete**: Fully implemented, tested, and documented
- 🔄 **In Progress**: Currently being developed
- 📋 **Planned**: Designed and prioritized for development
- 💡 **Proposed**: Ideas under consideration
- 🚫 **Deprecated**: No longer supported

### Priority Levels

- 🔴 **High**: Critical for core functionality
- 🟡 **Medium**: Important for user experience
- 🟢 **Low**: Nice-to-have features

---

## 🎯 Core Features (Complete)

| Feature ID | Component         | Business Value                            | Status      | Priority  |
| ---------- | ----------------- | ----------------------------------------- | ----------- | --------- |
| DGIT-101   | Stock Screener    | Filter universe by DGI criteria           | ✅ Complete | 🔴 High   |
| DGIT-102   | Portfolio Builder | Build weighted portfolios from top stocks | ✅ Complete | 🔴 High   |
| DGIT-103   | CLI Interface     | Command-line access for power users       | ✅ Complete | 🟡 Medium |
| DGIT-104   | Jupyter Demo      | Visual portfolio analysis & reporting     | ✅ Complete | 🟡 Medium |
| DGIT-105   | Testing Suite     | Quality assurance & regression prevention | ✅ Complete | 🔴 High   |
| DGIT-106   | Documentation     | User onboarding & contribution guidelines | ✅ Complete | 🟡 Medium |

---

## 🚀 Planned Features (Next Phase)

| Feature ID | Component                  | Business Value                             | Status         | Priority  | Target Date |
| ---------- | -------------------------- | ------------------------------------------ | -------------- | --------- | ----------- |
| DGIT-301   | FastAPI Service Skeleton   | HTTP endpoints for screener integration    | 🔄 In Progress | 🔴 High   | 2024-12-19  |
| DGIT-302   | Dockerised API             | Containerized service for cloud deployment | 📋 Planned     | 🔴 High   | TBD         |
| DGIT-303   | CI/CD Workflow             | Automated Docker image publishing          | 📋 Planned     | 🟡 Medium | TBD         |
| DGIT-304   | Integration Tests          | Automated API endpoint testing             | 📋 Planned     | 🔴 High   | TBD         |
| DGIT-305   | README & Swagger Link      | API documentation and examples             | 📋 Planned     | 🟡 Medium | TBD         |
| DGIT-401   | FinViz Scraper Tool        | Web scraping for fresh ticker data         | 📋 Planned     | 🔴 High   | TBD         |
| DGIT-402   | IEX Cloud Tool             | API integration for fundamentals data      | 📋 Planned     | 🔴 High   | TBD         |
| DGIT-403   | ResearchAgent Orchestrator | Automated research workflow                | 📋 Planned     | 🔴 High   | TBD         |
| DGIT-404   | Unit + Integration Tests   | Quality assurance for AI tools             | 📋 Planned     | 🟡 Medium | TBD         |
| DGIT-405   | LinkedIn Post Draft        | Marketing content for Sprint 2             | 📋 Planned     | 🟢 Low    | TBD         |

---

### DGIT-301: FastAPI Service Skeleton - 📋 Planned (🔴 High Priority)

**Business Problem**: Research analysts need HTTP endpoints to integrate the DGI
screener into Excel or BI tools without requiring CLI access.

**User Story**: _As a research analyst_ I want an HTTP endpoint that returns the same
results as the CLI so I can integrate the screener into Excel or BI tools.

**Acceptance Criteria**:

- `main.py` boots FastAPI application
- Root `/healthz` endpoint returns `200 OK` with `{"status":"up"}`
- `/api/v1/screen` accepts query parameters: `min_cagr`, `min_yield`, `max_payout`,
  `top_n`
- Returns JSON list of stocks sorted by score
- Swagger/Redoc documentation enabled

**Technical Implementation**:

- **File**: `api/main.py`
- **Dependencies**: Re-use functions from `dgi.screener`
- **Models**: Add Pydantic response models for type safety
- **Validation**: Input parameter validation with meaningful error messages

**Success Criteria**:

- API responds in < 2 seconds for typical screening requests
- JSON response matches CLI output format
- OpenAPI documentation is auto-generated and accessible

---

### DGIT-302: Dockerised API - 📋 Planned (🔴 High Priority)

**Business Problem**: DevOps teams need the service containerized for deployment in
cloud environments without manual setup.

**User Story**: _As DevOps_ I need the service containerized so we can run it in
ECS/Fargate without manual setup.

**Acceptance Criteria**:

- New multistage `Dockerfile.api` builds `api` target
- Runtime image size ≤ 150 MB
- `ENTRYPOINT ["uvicorn","api.main:app","--host","0.0.0.0","--port","8080"]`
- Exposes port 8080 for HTTP traffic

**Technical Implementation**:

- **File**: `Dockerfile.api`
- **Base Image**: Re-use slim build template from existing Dockerfile
- **Multi-stage**: Separate build and runtime stages for optimization
- **Security**: Non-root user, minimal attack surface

**Success Criteria**:

- Container starts successfully in 30 seconds
- Health check endpoint responds correctly
- Image size stays under 150 MB limit

---

### DGIT-303: CI/CD Workflow - 📋 Planned (🟡 Medium Priority)

**Business Problem**: Tech leads need automated Docker image publishing for seamless
deployment.

**User Story**: _As a tech-lead_ I want the Docker image published to GHCR on every
merge to `main` so deployment is one click.

**Acceptance Criteria**:

- New GitHub Action `.github/workflows/cd.yml`
- Builds `Dockerfile.api` for `linux/amd64` architecture
- Size guard ensures image < 150 MB
- `docker push ghcr.io/<user>/dgi-api:${{ github.sha }}` (only on `main` branch)

**Technical Implementation**:

- **File**: `.github/workflows/cd.yml`
- **Cache**: Re-use CI cache step for efficiency
- **Secrets**: Use GHCR token from repository secrets
- **Triggers**: Only on pushes to `main` branch

**Success Criteria**:

- Automated builds complete in < 10 minutes
- Images are properly tagged and pushed to GHCR
- Failed builds provide clear error messages

---

### DGIT-304: Integration Tests - 📋 Planned (🔴 High Priority)

**Business Problem**: QA teams need automated tests to ensure API endpoints never ship
broken.

**User Story**: _As QA_ I need automated tests that hit `/api/v1/screen` so we never
ship a broken endpoint.

**Acceptance Criteria**:

- `tests/test_api.py` spins up FastAPI with `TestClient`
- Status 200, JSON length ≤ `top_n`, schema validated
- Included in coverage; overall ≥ 85%

**Technical Implementation**:

- **File**: `tests/test_api.py`
- **Dependencies**: Add `fastapi`, `uvicorn[standard]`, `httpx` to dev dependencies
- **Testing**: Use FastAPI TestClient for integration testing
- **Coverage**: Ensure API endpoints are fully covered

**Success Criteria**:

- All API endpoints have integration tests
- Tests run in < 30 seconds
- Coverage remains ≥ 85% overall

---

### DGIT-305: README & Swagger Link - 📋 Planned (🟡 Medium Priority)

**Business Problem**: New users need clear documentation to quickly start using the API.

**User Story**: _As a new user_ I want clear docs so I can curl the API in < 5 min.

**Acceptance Criteria**:

- README "Quick Start (Docker)" section
- Example `curl` call with expected output
- Link to Swagger UI screenshot

**Technical Implementation**:

- **File**: Update `README.md`
- **Content**: Add Docker-based quick start guide
- **Examples**: Provide working curl commands
- **Screenshots**: Include Swagger UI documentation

**Success Criteria**:

- New users can make their first API call in < 5 minutes
- Documentation is clear and accurate
- Examples work out-of-the-box

---

### DGIT-401: FinViz Scraper Tool - 📋 Planned (🔴 High Priority)

**Business Problem**: Research agents need to query FinViz screener pages to pull fresh
ticker lists without licensing costs.

**User Story**: _As the research agent_ I need to query FinViz screener pages so I can
pull fresh ticker lists without licensing costs.

**Acceptance Criteria**:

- `ai_tools/finviz_tool.py` exports `scrape_finviz(criteria:str)->list[str]`
- Uses Playwright or `requests-html` for web scraping
- Returns max 50 tickers with sector & yield where available
- Handles anti-bot delays with retry logic

**Technical Implementation**:

- **File**: `ai_tools/finviz_tool.py`
- **Dependencies**: Playwright or `requests-html`
- **Error Handling**: Retry 3× with exponential backoff
- **Criteria Format**: String parsing for "Dividend% > 4, Payout < 80"

**Success Criteria**:

- Successfully scrapes FinViz without being blocked
- Returns structured data with ticker symbols and metadata
- Handles rate limiting gracefully

---

### DGIT-402: IEX Cloud Tool - 📋 Planned (🔴 High Priority)

**Business Problem**: AI agents need API access to fetch fundamentals for ticker
validation and analysis.

**User Story**: _As the agent_ I need an API call that fetches fundamentals for a list
of tickers for validation.

**Acceptance Criteria**:

- `ai_tools/iex_tool.py` with function
  `fetch_fundamentals(tickers:list[str])->pd.DataFrame`
- Reads `IEX_TOKEN` from environment variables
- Raises clear error if token is absent
- Unit test uses `pytest-vcr` cassette for reliable testing

**Technical Implementation**:

- **File**: `ai_tools/iex_tool.py`
- **API**: IEX Cloud fundamentals endpoint
- **Rate Limiting**: Free sandbox key covers 50 calls/min
- **Testing**: VCR cassettes for reproducible tests

**Success Criteria**:

- Successfully fetches fundamentals for provided tickers
- Returns structured DataFrame with financial metrics
- Handles API rate limits and errors gracefully

---

### DGIT-403: ResearchAgent Orchestrator - 📋 Planned (🔴 High Priority)

**Business Problem**: AI power-users need a one-command agent that automates the entire
research workflow.

**User Story**: _As an AI power-user_ I want a one-command agent that merges FinViz +
IEX data, de-dupes, runs the screener filter, and outputs a ranked CSV.

**Acceptance Criteria**:

- `ai_chat/agent_demo.py` initialises `crewAI.Agent` with 2 tools +
  `dgi.screener.apply_filters`
- Agent prints thought/action logs for transparency
- Final CSV stored to `output/candidates_<date>.csv`
- Works headless via `python -m ai_chat.agent_demo`

**Technical Implementation**:

- **File**: `ai_chat/agent_demo.py`
- **Framework**: Use `crewAI` "CrewWorker" if available; fallback to LangChain agent
- **Workflow**: FinViz scraping → IEX validation → DGI screening → CSV output
- **Logging**: Detailed thought process and action logs

**Success Criteria**:

- Complete end-to-end workflow execution
- Generates ranked CSV with candidate stocks
- Provides transparent logging of decision process

---

### DGIT-404: Unit + Integration Tests - 📋 Planned (🟡 Medium Priority)

**Business Problem**: Quality assurance teams need comprehensive testing for scraper and
API tools.

**User Story**: Ensures scraper & API tool behave with mocks and recorded cassettes.

**Acceptance Criteria**:

- `tests/test_finviz.py`, `test_iex.py` reach ≥ 85% coverage for `ai_tools` package
- Mock external dependencies for reliable testing
- VCR cassettes for API response recording

**Technical Implementation**:

- **Files**: `tests/test_finviz.py`, `tests/test_iex.py`
- **Coverage**: Target ≥ 85% for `ai_tools` package
- **Mocking**: External API and web scraping dependencies
- **VCR**: Record and replay API responses

**Success Criteria**:

- Comprehensive test coverage for all AI tools
- Reliable test execution without external dependencies
- Fast test execution with mocked responses

---

### DGIT-405: LinkedIn Post Draft - 📋 Planned (🟢 Low Priority)

**Business Problem**: Marketing team needs publishable content to showcase Sprint 2
achievements.

**User Story**: Publishable content for Sprint 2.

**Acceptance Criteria**:

- `/docs/linkedin_post_week6.md` with hook, bullet features, GIF placeholder
- Professional marketing content highlighting new capabilities
- Ready for social media publication

**Technical Implementation**:

- **File**: `/docs/linkedin_post_week6.md`
- **Content**: Hook, feature bullets, visual placeholders
- **Format**: Markdown with LinkedIn-optimized structure

**Success Criteria**:

- Engaging content that highlights technical achievements
- Professional presentation suitable for LinkedIn
- Clear call-to-action for engagement

---

## 💡 Proposed Features (Future Consideration)

| Feature ID | Component | Business Value | Status | Priority | Notes |
| ---------- | --------- | -------------- | ------ | -------- | ----- |
|            |           |                |        |          |       |

---

## 🔍 DGIT-101: Stock Screener (`dgi.screener`)

### Business Problem Solved

**Data analysts** need to quickly filter thousands of stocks to identify dividend growth
candidates that meet specific financial criteria, reducing manual analysis time from
hours to seconds.

### Core Functionality

#### 1. Universe Loading

```python
from dgi.screener import load_universe

# Load and validate fundamentals data
df = load_universe("data/fundamentals_small.csv")
```

**Business Value:**

- Automatically validates data quality (removes corrupted/invalid rows)
- Ensures consistent data types for downstream analysis
- Handles missing values gracefully

#### 2. Multi-Criteria Filtering

```python
from dgi.screener import Screener
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.validation import DgiRowValidator, PydanticRowValidation
from dgi.models.company import CompanyData

# Set up screener with dependency injection
validator = DgiRowValidator(PydanticRowValidation(CompanyData))
repo = CsvCompanyDataRepository("data/fundamentals_small.csv", validator)
screener = Screener(repo)

# Apply DGI filters
df = screener.load_universe()
filtered = screener.apply_filters(
    df,
    min_yield=0.02,      # Minimum 2% dividend yield
    max_payout=0.80,     # Maximum 80% payout ratio
    min_cagr=0.05        # Minimum 5% dividend CAGR
)
```

**Business Value:**

- **Time Savings**: Reduce screening time from manual Excel analysis (hours) to
  automated filtering (seconds)
- **Consistency**: Standardized criteria application across all analyses
- **Scalability**: Process thousands of stocks with identical logic

#### 3. Composite Scoring

```python
# Add composite scores for ranking
scored = screener.add_scores(filtered)
top_stocks = scored.sort_values("score", ascending=False).head(20)
```

**Scoring Algorithm:**

- **⅓ Dividend Yield**: Higher yield increases score
- **⅓ Dividend Growth**: Higher 5-year CAGR increases score
- **⅓ Payout Safety**: Lower payout ratio increases score (penalty for >60%)

**Business Value:**

- **Objective Ranking**: Removes emotion and bias from stock selection
- **Multi-Factor Analysis**: Balances yield, growth, and sustainability
- **Customizable**: Easy to modify scoring weights for different strategies

### Architecture Features

- **Repository Pattern**: Abstract data sources (CSV, future database support)
- **Strategy Pattern**: Pluggable scoring algorithms
- **Type Safety**: 100% mypy compliance with Pydantic validation
- **Error Handling**: Graceful handling of invalid data with detailed logging

---

## 💼 DGIT-102: Portfolio Builder (`dgi.portfolio`)

### Business Problem Solved

**Portfolio managers** need to quickly convert a screened stock list into actionable
portfolio weights, supporting different allocation strategies and risk management.

### Core Functionality

#### 1. Top-N Selection with Weighting

```python
from dgi.portfolio import build

# Equal-weighted portfolio (risk parity approach)
equal_portfolio = build(scored_df, top_n=10, weighting="equal")

# Score-weighted portfolio (conviction-based)
score_portfolio = build(scored_df, top_n=10, weighting="score")
```

**Business Value:**

- **Speed**: Instant portfolio construction from screening results
- **Flexibility**: Multiple weighting strategies for different risk profiles
- **Consistency**: Standardized output format for execution systems

#### 2. Portfolio Summary Statistics

```python
from dgi.portfolio import summary_stats

stats = summary_stats(portfolio_df, universe_df)
print(f"Portfolio Yield: {stats['avg_yield']:.2%}")
print(f"Median CAGR: {stats['median_cagr']:.2%}")
print(f"Mean Payout: {stats['mean_payout']:.1%}")
```

**Business Value:**

- **Risk Assessment**: Quick portfolio-level metrics for risk management
- **Client Reporting**: Professional statistics for investment committees
- **Benchmarking**: Compare portfolio characteristics vs. universe

#### 3. Weighting Strategies

**Equal Weighting** (Risk Parity):

```python
# Each position gets 1/N allocation
# Reduces single-stock risk, diversification-focused
```

**Score Weighting** (Conviction-Based):

```python
# Higher-scored stocks get larger allocations
# Concentrates in highest-conviction names
```

### Architecture Features

- **Strategy Pattern**: `WeightingStrategy` ABC enables custom allocation algorithms
- **Input Validation**: Comprehensive parameter checking with meaningful error messages
- **Flexible Output**: Standard DataFrame format compatible with execution systems

---

## 🖥️ DGIT-103: CLI Interface (`dgi.cli`)

### Business Problem Solved

**Power users** need command-line access for automation, scripting, and integration with
existing workflows without requiring Python programming knowledge.

### Core Functionality

#### 1. Interactive Screening

```bash
# Basic screening with rich table output
poetry run dgi screen --min-yield 0.03

# Custom parameters
poetry run dgi screen \
  --min-yield 0.025 \
  --max-payout 75.0 \
  --min-cagr 0.07 \
  --csv-path custom_data.csv
```

**Business Value:**

- **Accessibility**: Non-programmers can access full functionality
- **Automation**: Easy integration into shell scripts and cron jobs
- **Speed**: Instant results with professional table formatting

#### 2. Portfolio Construction

```bash
# Build equal-weighted portfolio
poetry run dgi build-portfolio \
  --top-n 15 \
  --weighting equal \
  --min-yield 0.02

# Score-weighted portfolio with custom filters
poetry run dgi build-portfolio \
  --top-n 10 \
  --weighting score \
  --max-payout 60.0
```

**Business Value:**

- **Workflow Integration**: Fits into existing trading/research workflows
- **Reproducibility**: Consistent results with version-controlled parameters
- **Batch Processing**: Process multiple universes with different criteria

#### 3. Rich Output Formatting

- **Color-coded tables**: Visual highlighting of key metrics
- **Sortable columns**: Data organized by relevance (score, yield, growth)
- **Error handling**: Clear error messages with exit codes for scripting

### Architecture Features

- **Typer Framework**: Modern CLI with automatic help generation
- **Rich Integration**: Professional terminal output with colors and formatting
- **Configuration Management**: Environment variable support for defaults
- **Structured Logging**: JSON logging for production monitoring

---

## 📊 DGIT-104: Jupyter Demo (`notebooks/dgi_portfolio_builder.ipynb`)

### Business Problem Solved

**Content creators** and **analysts** need visual portfolio analysis capabilities for
presentations, blog posts, and research reports.

### Core Functionality

#### 1. Complete Pipeline Demonstration

```python
# Full end-to-end workflow
df = screener.load_universe()
filtered = screener.apply_filters(df, min_yield=0.5, max_payout=60, min_cagr=5.0)
scored = screener.add_scores(filtered)
portfolio = build(scored, top_n=10, weighting="equal")
```

#### 2. Visual Analysis

- **Portfolio Weight Distribution**: Bar charts showing allocation percentages
- **Sector Analysis**: Pie charts of sector diversification
- **Metric Histograms**: Distribution of yield, growth, and payout ratios

#### 3. Summary Statistics

- Portfolio-level metrics with formatting
- Comparison tables vs. broader universe
- Risk/return characteristics

**Business Value:**

- **Professional Reporting**: Publication-ready charts and tables
- **Educational Content**: Step-by-step learning resource
- **Prototype Development**: Sandbox for testing new features

---

## 🧪 DGIT-105: Testing Suite (`tests/`)

### Business Problem Solved

**QA teams** and **developers** need confidence that code changes don't break existing
functionality, especially in financial calculations where accuracy is critical.

### Core Functionality

#### 1. Comprehensive Test Coverage (87%)

```python
# Edge case testing
def test_screener_empty_dataframe():
    """Ensure empty results don't crash the system"""

def test_portfolio_build_invalid_top_n():
    """Validate input parameter boundaries"""

def test_validation_invalid_data():
    """Handle corrupted data gracefully"""
```

#### 2. Parametrized Testing

```python
@pytest.mark.parametrize("weighting,expected", [
    ("equal", [0.1, 0.1, 0.1]),  # Equal weights
    ("score", [0.4, 0.3, 0.3]),   # Score-based weights
])
def test_portfolio_weighting_strategies(weighting, expected):
    """Test multiple weighting algorithms"""
```

#### 3. Integration Testing

- Full pipeline tests (CSV → portfolio)
- CLI testing with subprocess
- Error handling validation

**Business Value:**

- **Risk Reduction**: Catch financial calculation errors before production
- **Refactoring Safety**: Confidence to improve code without breaking functionality
- **Documentation**: Tests serve as executable specifications

---

## 📚 DGIT-106: Documentation & Developer Experience

### Business Problem Solved

**Open source users** and **team members** need clear onboarding, contribution
guidelines, and usage examples to quickly become productive.

### Core Functionality

#### 1. Professional README

- Quick start guide with copy-paste examples
- CI/CD status badges for transparency
- Feature overview with business context

#### 2. Contribution Guidelines

- Pre-commit hook setup for code quality
- Conventional commit message standards
- Code review requirements and quality gates

#### 3. Developer Tooling

- **Black**: Automated code formatting
- **Ruff**: Fast linting with modern rules
- **MyPy**: Static type checking in strict mode
- **Pre-commit**: Quality gates before commit

**Business Value:**

- **Faster Onboarding**: New team members productive in minutes
- **Code Quality**: Consistent style and standards across team
- **Professional Image**: Enterprise-grade documentation and processes

---

## 🏗️ Technical Architecture

### Design Patterns Used

#### 1. Repository Pattern

```python
class CompanyDataRepository(ABC):
    @abstractmethod
    def get_rows(self) -> List[CompanyData]:
        """Abstract data access for testability and flexibility"""
```

**Benefits:**

- Easy unit testing with mock repositories
- Future database support without changing business logic
- Clean separation of data access and business logic

#### 2. Strategy Pattern

```python
class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, company: CompanyData) -> float:
        """Pluggable scoring algorithms"""
```

**Benefits:**

- Runtime algorithm selection
- Easy A/B testing of different scoring methods
- Extensible without modifying existing code

#### 3. Dependency Injection

```python
def __init__(self, repository: CompanyDataRepository,
             scoring_strategy: Optional[ScoringStrategy] = None):
    """Dependencies injected via constructor"""
```

**Benefits:**

- Loose coupling between components
- Easy testing with mock dependencies
- Configurable behavior without code changes

### Quality Assurance

#### 1. Type Safety

- 100% mypy compliance in strict mode
- Pydantic models with runtime validation
- Generic types properly constrained

#### 2. Error Handling

- Custom exception types for domain errors
- Structured logging with context
- Graceful degradation for invalid data

#### 3. Testing Strategy

- Unit tests for individual components
- Integration tests for full workflows
- Property-based testing for edge cases
- CLI testing with subprocess

---

## 🚀 Future Extension Points

### Planned Enhancements

#### 1. Additional Data Sources

```python
# Future implementations
class DatabaseRepository(CompanyDataRepository):
    """SQL database data source"""

class APIRepository(CompanyDataRepository):
    """Real-time API data source"""
```

#### 2. Advanced Scoring Models

```python
class MLScoringStrategy(ScoringStrategy):
    """Machine learning-based scoring"""

class ESGScoringStrategy(ScoringStrategy):
    """Environmental/Social/Governance scoring"""
```

#### 3. Portfolio Optimization

```python
class ModernPortfolioWeighting(WeightingStrategy):
    """Mean-variance optimization"""

class RiskParityWeighting(WeightingStrategy):
    """Risk-based allocation"""
```

---

## 📈 Business Impact Summary

| Stakeholder           | Before DGI Toolkit                  | After DGI Toolkit                        | Time Savings |
| --------------------- | ----------------------------------- | ---------------------------------------- | ------------ |
| **Data Analyst**      | Manual Excel screening (2-4 hours)  | Automated filtering (30 seconds)         | **95%**      |
| **Portfolio Manager** | Manual weight calculations (1 hour) | Instant portfolio generation (5 seconds) | **99%**      |
| **Power User**        | Python scripting required           | Simple CLI commands                      | **80%**      |
| **Content Creator**   | Custom visualization code           | Ready-made notebook templates            | **70%**      |
| **QA Team**           | Manual testing of calculations      | Automated test suite                     | **90%**      |

### ROI Calculation

- **Development Time**: 40 hours initial investment
- **Weekly Time Savings**: 15 hours across team (3 analysts × 5 hours)
- **Break-even Point**: 2.7 weeks
- **Annual Value**: $156,000 (assuming $200/hour fully-loaded cost)

---

## 📞 Support & Getting Started

### Quick Start

```bash
# Install dependencies
poetry install

# Run screening
poetry run dgi screen --min-yield 0.03

# Build portfolio
poetry run dgi build-portfolio --top-n 10

# Run tests
poetry run pytest

# View notebook
jupyter notebook notebooks/dgi_portfolio_builder.ipynb
```

### Common Use Cases

1. **Daily Screening**: Automated morning screening for new opportunities
2. **Portfolio Rebalancing**: Monthly portfolio reconstruction with updated data
3. **Research Analysis**: Ad-hoc filtering and analysis for specific sectors
4. **Client Reporting**: Professional visualizations for investment committees

This toolkit transforms dividend growth investing from a manual, time-intensive process
into an automated, repeatable, and scalable workflow suitable for professional
investment management.
