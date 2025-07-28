"""FastAPI application for DGI Toolkit API service."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from dgi.models.company import CompanyData
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring
from dgi.screener import Screener
from dgi.validation import DgiRowValidator, PydanticRowValidation

# Initialize FastAPI app
app = FastAPI(
    title="DGI Toolkit API",
    description="API for Dividend Growth Investing (DGI) stock screening and analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Pydantic models for API responses
class StockResponse(BaseModel):
    """Response model for stock data."""

    symbol: str
    name: str
    sector: str
    industry: str
    dividend_yield: float
    payout: float
    dividend_cagr: float
    fcf_yield: float
    score: float


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(default="up", description="Service status")


# Initialize screener with default configuration
def get_screener() -> Screener:
    """Get configured screener instance."""
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository("data/fundamentals_small.csv", validator)
    return Screener(repo, scoring_strategy=DefaultScoring())


@app.get("/healthz", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="up")


@app.get(
    "/api/v1/screen",
    response_model=list[StockResponse],
    tags=["Screening"],
    summary="Screen stocks using DGI criteria",
    description="Filter and rank stocks based on dividend yield, payout ratio, and dividend growth rate.",
)
async def screen_stocks(
    min_yield: float = Query(
        default=0.02,
        ge=0.0,
        le=100.0,
        description="Minimum dividend yield (as decimal, e.g., 0.02 for 2%)",
    ),
    max_payout: float = Query(
        default=80.0,
        ge=0.0,
        le=200.0,
        description="Maximum payout ratio (as percentage, e.g., 80.0 for 80%)",
    ),
    min_cagr: float = Query(
        default=0.05,
        ge=-100.0,
        le=100.0,
        description="Minimum 5-year dividend CAGR (as decimal, e.g., 0.05 for 5%)",
    ),
    top_n: int = Query(
        default=10, ge=1, le=100, description="Number of top stocks to return"
    ),
) -> list[StockResponse]:
    """
    Screen stocks using DGI criteria and return top performers.

    This endpoint filters stocks based on dividend yield, payout ratio, and dividend growth rate,
    then ranks them by a composite score and returns the top N stocks.

    Args:
        min_yield: Minimum dividend yield required
        max_payout: Maximum payout ratio allowed
        min_cagr: Minimum dividend growth rate required
        top_n: Number of top stocks to return

    Returns:
        List of stocks sorted by score (descending)
    """
    try:
        # Get screener instance
        screener = get_screener()

        # Load and filter data
        df = screener.load_universe()
        filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
        scored = screener.add_scores(filtered)

        # Sort by score and take top N
        if scored.empty:
            return []

        top_stocks = scored.sort_values("score", ascending=False).head(top_n)

        # Convert to response models
        results = []
        for _, row in top_stocks.iterrows():
            stock = StockResponse(
                symbol=row["symbol"],
                name=row["name"],
                sector=row["sector"],
                industry=row["industry"],
                dividend_yield=float(row["dividend_yield"]),
                payout=float(row["payout"]),
                dividend_cagr=float(row["dividend_cagr"]),
                fcf_yield=float(row["fcf_yield"]),
                score=float(row["score"]),
            )
            results.append(stock)

        return results

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error in screen_stocks: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during stock screening"
        ) from e


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DGI Toolkit API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz",
    }
