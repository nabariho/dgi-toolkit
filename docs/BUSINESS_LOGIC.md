# Business Logic Documentation - DGI Toolkit

This document provides comprehensive documentation for the complex business logic,
scoring algorithms, and domain-specific rules implemented in the DGI (Dividend Growth
Investing) Toolkit.

## Table of Contents

- [Overview](#overview)
- [DGI Scoring Algorithm](#dgi-scoring-algorithm)
- [Screening Criteria](#screening-criteria)
- [Business Rules and Constraints](#business-rules-and-constraints)
- [Portfolio Optimization](#portfolio-optimization)
- [Data Validation Logic](#data-validation-logic)
- [Performance Calculations](#performance-calculations)
- [Extension Points](#extension-points)

## Overview

### Dividend Growth Investing (DGI) Philosophy

DGI is an investment strategy focused on companies that consistently grow their dividend
payments over time. The strategy emphasizes:

1. **Dividend Yield**: Current income generation
2. **Dividend Growth**: Historical and projected growth rates
3. **Sustainability**: Company's ability to maintain and grow dividends
4. **Quality**: Financial strength and business moat

### Core Metrics

The toolkit evaluates companies using these key financial metrics:

- **Dividend Yield**: Annual dividends per share / Stock price
- **Payout Ratio**: Dividends per share / Earnings per share
- **Dividend CAGR**: Compound Annual Growth Rate of dividends
- **Free Cash Flow Yield**: Free cash flow per share / Stock price

## DGI Scoring Algorithm

### Overview

The DGI scoring algorithm combines multiple financial metrics to produce a composite
score between 0.0 and 1.0, where higher scores indicate more attractive DGI
opportunities.

### Default Scoring Strategy

The `DefaultScoring` class implements the core scoring logic:

```python
def score(self, company: CompanyData) -> float:
    """Calculate composite DGI score for a company.

    The score combines four components:
    1. Dividend yield score (40% weight)
    2. Payout ratio score (20% weight)
    3. Dividend growth score (30% weight)
    4. Free cash flow yield score (10% weight)
    """
```

### Component Calculations

#### 1. Dividend Yield Score (40% weight)

```python
def _calculate_yield_score(self, dividend_yield: float) -> float:
    """Calculate yield score with target optimization.

    Algorithm:
    - Target yield: 4% (optimal balance of income and growth)
    - Below 2%: Linear scaling from 0.0 to 0.5
    - 2% to 4%: Linear scaling from 0.5 to 1.0
    - 4% to 8%: Linear scaling from 1.0 to 0.8
    - Above 8%: Penalty for potentially unsustainable yields

    Business Logic:
    - Very low yields (<2%) may indicate poor income generation
    - Moderate yields (2-4%) balance income and growth potential
    - High yields (>8%) may signal financial distress
    """
```

**Mathematical Formula:**

```
if yield < 0.02:
    score = yield / 0.04  # 0.0 to 0.5
elif yield <= 0.04:
    score = 0.5 + (yield - 0.02) / 0.04  # 0.5 to 1.0
elif yield <= 0.08:
    score = 1.0 - (yield - 0.04) * 0.05  # 1.0 to 0.8
else:
    score = 0.8 - (yield - 0.08) * 0.02  # Decreasing penalty
```

#### 2. Payout Ratio Score (20% weight)

```python
def _calculate_payout_score(self, payout_ratio: float) -> float:
    """Calculate payout ratio score for sustainability.

    Algorithm:
    - Target range: 40-60% (sustainable and growing)
    - Below 40%: Room for growth but may indicate low commitment
    - 40-60%: Optimal range for balance
    - Above 80%: Sustainability concerns

    Business Logic:
    - Low payout ratios may indicate management reluctance to share profits
    - Moderate ratios suggest sustainable dividend policy
    - High ratios may limit future growth or force dividend cuts
    """
```

#### 3. Dividend Growth Score (30% weight)

```python
def _calculate_growth_score(self, dividend_cagr: float) -> float:
    """Calculate dividend growth score.

    Algorithm:
    - Target: 5-15% annual growth (sustainable long-term growth)
    - Negative growth: 0.0 score (dividend cuts are poor signals)
    - 0-5%: Linear scaling for inflation protection
    - 5-15%: Optimal range for sustainable growth
    - Above 15%: May be unsustainable long-term

    Business Logic:
    - Negative growth indicates potential financial difficulties
    - Low growth may not keep pace with inflation
    - Moderate growth suggests healthy, sustainable business
    - Very high growth may be unsustainable
    """
```

#### 4. Free Cash Flow Yield Score (10% weight)

```python
def _calculate_fcf_score(self, fcf_yield: float) -> float:
    """Calculate free cash flow yield score.

    Algorithm:
    - Target: Above 5% (indicates strong cash generation)
    - Linear scaling from 0% to 10%
    - Capped at 1.0 for yields above 10%

    Business Logic:
    - FCF yield indicates company's ability to generate cash
    - Higher yields suggest stronger financial position
    - Essential for dividend sustainability assessment
    """
```

### Composite Score Calculation

```python
final_score = (
    yield_score * 0.40 +      # Dividend yield (40%)
    payout_score * 0.20 +     # Payout ratio (20%)
    growth_score * 0.30 +     # Dividend growth (30%)
    fcf_score * 0.10          # FCF yield (10%)
)
```

### Score Interpretation

| Score Range | Interpretation          | Investment Consideration |
| ----------- | ----------------------- | ------------------------ |
| 0.8 - 1.0   | Excellent DGI candidate | Strong buy consideration |
| 0.6 - 0.8   | Good DGI candidate      | Buy consideration        |
| 0.4 - 0.6   | Fair DGI candidate      | Hold or further analysis |
| 0.2 - 0.4   | Poor DGI candidate      | Avoid or sell            |
| 0.0 - 0.2   | Very poor DGI candidate | Strong avoid             |

## Screening Criteria

### Parameter Validation

The `ScreeningParameterValidator` enforces business rules:

```python
class ScreeningParameterValidator:
    """Validates screening parameters against business rules."""

    BUSINESS_RULES = {
        "min_yield": {
            "range": (0.0, 1.0),  # 0% to 100%
            "format": "decimal",   # 0.02 for 2%
            "business_logic": "Minimum acceptable dividend yield"
        },
        "max_payout": {
            "range": (0.0, 5.0),  # 0% to 500%
            "format": "decimal",   # 0.80 for 80%
            "business_logic": "Maximum payout ratio for sustainability"
        },
        "min_cagr": {
            "range": (-1.0, 1.0), # -100% to 100%
            "format": "decimal",   # 0.05 for 5%
            "business_logic": "Minimum dividend growth rate"
        }
    }
```

### DGI Criteria Application

The `DGICriteriaService` applies investment criteria:

```python
def apply_dgi_criteria(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """Apply DGI investment criteria to filter companies.

    Business Logic:
    1. Dividend Yield Filter: Remove companies below minimum yield
    2. Payout Ratio Filter: Remove companies above maximum payout
    3. Growth Filter: Remove companies below minimum growth rate
    4. Quality Filter: Remove companies with negative FCF yields

    The filtering is cumulative - companies must pass ALL criteria.
    """
```

### Default Screening Parameters

```python
DEFAULT_SCREENING_PARAMETERS = {
    "min_yield": 0.02,        # 2% minimum yield
    "max_payout": 0.80,       # 80% maximum payout ratio
    "min_cagr": 0.03,         # 3% minimum growth rate
    "min_fcf_yield": 0.01,    # 1% minimum FCF yield
}
```

### Business Rationale

- **Minimum Yield (2%)**: Ensures meaningful income generation above inflation
- **Maximum Payout (80%)**: Maintains dividend sustainability buffer
- **Minimum Growth (3%)**: Requires real (inflation-adjusted) dividend growth
- **Minimum FCF Yield (1%)**: Ensures basic cash flow generation capability

## Business Rules and Constraints

### Data Quality Rules

```python
class DataQualityRules:
    """Business rules for data quality validation."""

    REQUIRED_FIELDS = [
        "symbol", "name", "sector", "industry",
        "dividend_yield", "payout", "dividend_cagr", "fcf_yield"
    ]

    FIELD_CONSTRAINTS = {
        "dividend_yield": {"min": 0.0, "max": 0.50},  # 0% to 50%
        "payout": {"min": 0.0, "max": 5.0},           # 0% to 500%
        "dividend_cagr": {"min": -1.0, "max": 1.0},   # -100% to 100%
        "fcf_yield": {"min": -1.0, "max": 1.0},       # -100% to 100%
    }
```

### Sector-Specific Rules

Different sectors have different DGI characteristics:

```python
SECTOR_ADJUSTMENTS = {
    "Utilities": {
        "yield_weight": 0.50,     # Higher yield emphasis
        "growth_weight": 0.20,    # Lower growth expectations
        "typical_yield": 0.04,    # 4% typical yield
        "typical_growth": 0.02,   # 2% typical growth
    },
    "Technology": {
        "yield_weight": 0.30,     # Lower yield emphasis
        "growth_weight": 0.40,    # Higher growth potential
        "typical_yield": 0.015,   # 1.5% typical yield
        "typical_growth": 0.08,   # 8% typical growth
    },
    "Consumer Staples": {
        "yield_weight": 0.40,     # Balanced approach
        "growth_weight": 0.30,    # Moderate growth
        "typical_yield": 0.025,   # 2.5% typical yield
        "typical_growth": 0.04,   # 4% typical growth
    }
}
```

### Risk Management Rules

```python
class RiskManagementRules:
    """Risk management constraints for DGI investing."""

    PORTFOLIO_CONSTRAINTS = {
        "max_position_size": 0.10,        # 10% maximum per position
        "max_sector_concentration": 0.30, # 30% maximum per sector
        "min_diversification": 15,        # Minimum 15 holdings
        "max_correlation": 0.80,          # Maximum position correlation
    }

    DIVIDEND_SAFETY_RULES = {
        "max_payout_ratio": 0.90,         # 90% maximum (warning level)
        "min_interest_coverage": 2.5,     # 2.5x minimum coverage
        "max_debt_to_equity": 2.0,        # 200% maximum leverage
        "min_free_cash_flow": 0.01,       # 1% minimum FCF yield
    }
```

## Portfolio Optimization

### Modern Portfolio Theory Integration

```python
class DGIPortfolioOptimizer:
    """Optimize DGI portfolio using modern portfolio theory."""

    def optimize_weights(self, returns: pd.DataFrame, scores: pd.Series) -> pd.Series:
        """Optimize portfolio weights considering DGI scores and returns.

        Objective Function:
        maximize: w^T * μ - λ * w^T * Σ * w + α * w^T * scores

        Where:
        - w: portfolio weights
        - μ: expected returns
        - Σ: covariance matrix
        - λ: risk aversion parameter
        - α: DGI score weight
        - scores: normalized DGI scores

        Business Logic:
        - Higher DGI scores get preference in allocation
        - Risk is managed through diversification
        - Return expectations are balanced with dividend quality
        """
```

### Rebalancing Logic

```python
def calculate_rebalancing_trades(
    current_weights: pd.Series,
    target_weights: pd.Series,
    transaction_costs: float = 0.001
) -> pd.DataFrame:
    """Calculate optimal rebalancing trades.

    Business Rules:
    1. Only rebalance if benefit exceeds transaction costs
    2. Maintain tax efficiency (minimize short-term gains)
    3. Consider dividend payment dates
    4. Respect position size constraints
    """
```

## Data Validation Logic

### Multi-Layer Validation

```python
class CompanyDataValidator:
    """Multi-layer validation for company financial data."""

    def validate_financial_consistency(self, company: CompanyData) -> List[str]:
        """Validate financial metric consistency.

        Business Logic Checks:
        1. Payout ratio vs. dividend yield consistency
        2. FCF yield vs. dividend sustainability
        3. Growth rate vs. business maturity
        4. Sector benchmark comparisons
        """
```

### Outlier Detection

```python
def detect_data_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Detect and flag potential data outliers.

    Statistical Methods:
    1. Interquartile Range (IQR) method
    2. Z-score analysis (> 3 standard deviations)
    3. Sector-relative analysis
    4. Time-series consistency checks

    Business Application:
    - Flag extreme values for manual review
    - Protect scoring algorithm from bad data
    - Ensure data quality for decision making
    """
```

## Performance Calculations

### Risk-Adjusted Returns

```python
def calculate_risk_adjusted_returns(
    returns: pd.Series,
    benchmark_returns: pd.Series
) -> Dict[str, float]:
    """Calculate comprehensive risk-adjusted performance metrics.

    Metrics Calculated:
    1. Sharpe Ratio: (Return - Risk-free rate) / Volatility
    2. Sortino Ratio: (Return - Risk-free rate) / Downside deviation
    3. Alpha: Excess return vs. benchmark
    4. Beta: Sensitivity to market movements
    5. Information Ratio: Active return / Tracking error
    6. Maximum Drawdown: Largest peak-to-trough decline

    Business Interpretation:
    - Sharpe > 1.0: Good risk-adjusted performance
    - Sortino > 1.5: Good downside risk management
    - Alpha > 0: Outperforming benchmark
    - Beta < 1.0: Lower volatility than market
    """
```

### Dividend-Specific Metrics

```python
def calculate_dividend_metrics(
    prices: pd.Series,
    dividends: pd.Series
) -> Dict[str, float]:
    """Calculate dividend-specific performance metrics.

    DGI-Specific Calculations:
    1. Dividend Yield on Cost: Annual dividend / Original cost basis
    2. Dividend Growth Rate: CAGR of dividend payments
    3. Dividend Coverage Ratio: Earnings / Dividends
    4. Yield on Cost Progression: Multi-year yield development
    5. Dividend Reliability Score: Consistency measure

    Business Value:
    - Track income generation over time
    - Measure dividend sustainability
    - Evaluate long-term income growth
    """
```

## Extension Points

### Custom Scoring Strategies

```python
class CustomScoringStrategy(ScoringStrategy):
    """Example custom scoring strategy implementation."""

    def score(self, company: CompanyData) -> float:
        """Custom scoring algorithm.

        Extension Guidelines:
        1. Inherit from ScoringStrategy base class
        2. Implement score() method returning 0.0-1.0
        3. Document scoring logic and business rationale
        4. Add unit tests for edge cases
        5. Register with StrategyRegistry for dynamic loading
        """

        # Custom algorithm implementation
        custom_score = self._calculate_custom_metrics(company)
        return min(max(custom_score, 0.0), 1.0)  # Clamp to valid range
```

### Custom Filters

```python
class SectorSpecificFilter(BaseFilter):
    """Example sector-specific filter implementation."""

    def apply(self, df: pd.DataFrame, **criteria) -> pd.DataFrame:
        """Custom filtering logic.

        Extension Guidelines:
        1. Inherit from BaseFilter base class
        2. Implement apply() method returning filtered DataFrame
        3. Document filtering criteria and business logic
        4. Handle edge cases (empty DataFrames, missing columns)
        5. Add comprehensive logging for debugging
        """

        # Custom filtering implementation
        return df[self._sector_specific_criteria(df, criteria)]
```

### Plugin Architecture

```python
class DGIPlugin(ABC):
    """Base class for DGI Toolkit plugins."""

    @abstractmethod
    def get_name(self) -> str:
        """Return plugin name."""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Return plugin version."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        pass

    @abstractmethod
    def get_strategies(self) -> Dict[str, Any]:
        """Return available strategies provided by plugin."""
        pass
```

## Conclusion

This documentation provides the foundation for understanding and extending the DGI
Toolkit's business logic. The modular design allows for customization while maintaining
the core DGI investment philosophy.

### Key Principles

1. **Transparency**: All scoring logic is documented and explainable
2. **Flexibility**: Strategy pattern allows for custom implementations
3. **Consistency**: Business rules are enforced throughout the system
4. **Quality**: Multi-layer validation ensures data integrity
5. **Performance**: Risk-adjusted metrics provide comprehensive evaluation

### Continuous Improvement

The business logic should evolve based on:

- Market condition changes
- Academic research updates
- User feedback and requirements
- Performance analysis results
- Regulatory or compliance updates

For questions about specific algorithms or business rules, refer to the source code
documentation or contact the development team.
