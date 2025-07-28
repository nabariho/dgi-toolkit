"""FastAPI application for DGI Toolkit API service."""

import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from dgi.screener import Screener

from .config import get_settings, validate_configuration
from .dependencies import get_screener
from .error_handlers import register_exception_handlers
from .exceptions import APIException, ConfigurationError, DataProcessingError
from .logging_config import RequestContextMiddleware, get_logger, setup_logging
from .mappers import PerformanceTracker, ScreenResponseMapper, StockMapper
from .schemas.responses import APIInfoResponse, HealthResponse, ScreenResponse

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting DGI Toolkit API...")

    try:
        # Validate configuration
        validate_configuration()
        logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ConfigurationError(f"Configuration error: {e}") from e

    logger.info("DGI Toolkit API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down DGI Toolkit API...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=get_settings().api_title,
    description=get_settings().api_description,
    version=get_settings().api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=get_settings().cors_allow_credentials,
    allow_methods=get_settings().cors_allow_methods,
    allow_headers=get_settings().cors_allow_headers,
)

# Add request context middleware for logging
app.add_middleware(RequestContextMiddleware)

# Register exception handlers
register_exception_handlers(app)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    if get_settings().enable_security_headers:
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS header (only in production)
        if not get_settings().debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

    return response


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/healthz", response_model=HealthResponse, tags=["Health"])
@limiter.limit(
    f"{get_settings().rate_limit_requests}/{get_settings().rate_limit_period}s"
)
async def health_check(request: Request) -> HealthResponse:
    """Health check endpoint."""
    logger.debug("Health check requested")

    return HealthResponse(
        status="up",
        version=get_settings().api_version,
        environment="development" if get_settings().debug else "production",
    )


@app.get(
    "/api/v1/screen",
    response_model=ScreenResponse,
    tags=["Screening"],
    summary="Screen stocks using DGI criteria",
    description="Filter and rank stocks based on dividend yield, payout ratio, and dividend growth rate.",
)
@limiter.limit(
    f"{get_settings().rate_limit_requests}/{get_settings().rate_limit_period}s"
)
async def screen_stocks(
    request: Request,
    min_yield: float = Query(
        default=0.02,
        ge=get_settings().min_yield_range[0],
        le=get_settings().min_yield_range[1],
        description="Minimum dividend yield (as decimal, e.g., 0.02 for 2%)",
    ),
    max_payout: float = Query(
        default=80.0,
        ge=get_settings().max_payout_range[0],
        le=get_settings().max_payout_range[1],
        description="Maximum payout ratio (as percentage, e.g., 80.0 for 80%)",
    ),
    min_cagr: float = Query(
        default=0.05,
        ge=get_settings().cagr_range[0],
        le=get_settings().cagr_range[1],
        description="Minimum 5-year dividend CAGR (as decimal, e.g., 0.05 for 5%)",
    ),
    top_n: int = Query(
        default=10,
        ge=1,
        le=get_settings().max_top_n,
        description="Number of top stocks to return",
    ),
    screener: Screener = Depends(get_screener),
) -> ScreenResponse:
    """
    Screen stocks using DGI criteria and return top performers.

    This endpoint filters stocks based on dividend yield, payout ratio, and dividend growth rate,
    then ranks them by a composite score and returns the top N stocks.

    Args:
        request: FastAPI request object
        min_yield: Minimum dividend yield required
        max_payout: Maximum payout ratio allowed
        min_cagr: Minimum dividend growth rate required
        top_n: Number of top stocks to return
        screener: Injected screener dependency

    Returns:
        ScreenResponse with filtered and ranked stocks

    Raises:
        DataProcessingError: If data processing fails
        ValidationError: If input parameters are invalid
    """
    # Start performance tracking
    tracker = PerformanceTracker()
    tracker.start()

    # Get correlation ID for logging
    correlation_id = getattr(request.state, "correlation_id", None)

    logger.info(
        f"Screening stocks with parameters: min_yield={min_yield}, max_payout={max_payout}, "
        f"min_cagr={min_cagr}, top_n={top_n}",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Load and filter data
        df = screener.load_universe()

        if df.empty:
            logger.warning(
                "No data loaded from repository",
                extra={"correlation_id": correlation_id},
            )
            return ScreenResponseMapper.create_screen_response(
                stocks=[],
                filters_applied=ScreenResponseMapper.create_filters_dict(
                    min_yield, max_payout, min_cagr, top_n
                ),
                processing_time_ms=tracker.end(),
            )

        # Apply filters
        filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)

        if filtered.empty:
            logger.info(
                "No stocks match the filtering criteria",
                extra={"correlation_id": correlation_id},
            )
            return ScreenResponseMapper.create_screen_response(
                stocks=[],
                filters_applied=ScreenResponseMapper.create_filters_dict(
                    min_yield, max_payout, min_cagr, top_n
                ),
                processing_time_ms=tracker.end(),
            )

        # Add scores
        scored = screener.add_scores(filtered)

        # Validate DataFrame structure
        if not StockMapper.validate_dataframe_structure(scored):
            raise DataProcessingError(
                "Invalid data structure returned from screener",
                operation="data_validation",
            )

        # Sort by score and take top N
        top_stocks = scored.sort_values("score", ascending=False).head(top_n)

        # Convert to response models
        stocks = StockMapper.dataframe_to_stock_responses(top_stocks)

        # Create filters dictionary
        filters_applied = ScreenResponseMapper.create_filters_dict(
            min_yield, max_payout, min_cagr, top_n
        )

        # Calculate processing time
        processing_time_ms = tracker.end()

        logger.info(
            f"Screening completed: {len(stocks)} stocks returned in {processing_time_ms:.2f}ms",
            extra={
                "correlation_id": correlation_id,
                "stocks_returned": len(stocks),
                "processing_time_ms": processing_time_ms,
            },
        )

        return ScreenResponseMapper.create_screen_response(
            stocks=stocks,
            filters_applied=filters_applied,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        logger.error(
            f"Error in screen_stocks: {e!s}",
            exc_info=True,
            extra={"correlation_id": correlation_id},
        )
        raise DataProcessingError(
            f"Error during stock screening: {e!s}", operation="stock_screening"
        ) from e


@app.get("/", response_model=APIInfoResponse, tags=["Root"])
async def root() -> APIInfoResponse:
    """Root endpoint with API information."""
    return APIInfoResponse(
        message="DGI Toolkit API",
        version=get_settings().api_version,
        docs_url="/docs",
        health_url="/healthz",
        endpoints=["/api/v1/screen", "/healthz", "/docs", "/redoc"],
    )


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    correlation_id = getattr(request.state, "correlation_id", None)

    logger.error(
        f"API Exception: {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers={"X-Correlation-ID": correlation_id} if correlation_id else None,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=get_settings().host,
        port=get_settings().port,
        reload=get_settings().reload,
        log_level=get_settings().log_level.lower(),
    )
