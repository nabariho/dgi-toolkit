"""FastAPI application for DGI Toolkit API service."""

import os
import time
from contextlib import asynccontextmanager

import psutil
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from dgi.screener import Screener

from .caching import cache_result, get_cache_stats
from .config import get_settings, validate_configuration
from .dependencies import get_screener
from .error_handlers import register_exception_handlers
from .exceptions import APIException, ConfigurationError, DataProcessingError
from .logging_config import RequestContextMiddleware, get_logger, setup_logging
from .mappers import PerformanceTracker, ScreenResponseMapper, StockMapper
from .schemas.responses import APIInfoResponse, HealthResponse, ScreenResponse
from .versioning import APIVersionMiddleware

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global startup time for uptime calculation
startup_time = None


def get_min_yield_range():
    """Get minimum yield range for Query validation."""
    return get_settings().min_yield_range


def get_max_payout_range():
    """Get maximum payout range for Query validation."""
    return get_settings().max_payout_range


def get_cagr_range():
    """Get CAGR range for Query validation."""
    return get_settings().cagr_range


def get_max_top_n():
    """Get maximum top N for Query validation."""
    return get_settings().max_top_n


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global startup_time

    # Startup
    startup_time = time.time()
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

# Add API versioning middleware
app.add_middleware(APIVersionMiddleware)

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


@app.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API health status",
    description=f"""
    Comprehensive health check endpoint that monitors system status and performance.

    This endpoint provides real-time information about:
    - **Service Status**: Whether the API is operational
    - **System Metrics**: Memory usage, CPU utilization, and uptime
    - **Data File Status**: Accessibility and size of the data source
    - **Environment**: Current deployment environment (development/production)

    **Use Cases:**
    - Load balancer health checks
    - Monitoring system integration
    - DevOps pipeline health verification
    - Performance monitoring

    **Rate Limiting:** {get_settings().rate_limit_requests} requests per {get_settings().rate_limit_period} seconds
    """,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "up",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "uptime_seconds": 3600.5,
                        "memory_usage_mb": 45.2,
                        "cpu_usage_percent": 2.1,
                        "data_file_status": "accessible",
                        "data_file_size_mb": 1.2,
                    }
                }
            },
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "down",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "uptime_seconds": 3600.5,
                        "memory_usage_mb": 45.2,
                        "cpu_usage_percent": 2.1,
                        "data_file_status": "error",
                        "data_file_size_mb": None,
                    }
                }
            },
        },
    },
)
@limiter.limit(
    f"{get_settings().rate_limit_requests}/{get_settings().rate_limit_period}s"
)
async def health_check(request: Request) -> HealthResponse:
    """Health check endpoint with comprehensive system information."""
    logger.debug("Health check requested")

    # Calculate uptime
    uptime_seconds = None
    if startup_time is not None:
        uptime_seconds = time.time() - startup_time

    # Get system metrics
    memory_usage_mb = None
    cpu_usage_percent = None
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024  # Convert to MB
        cpu_usage_percent = process.cpu_percent(interval=0.1)
    except Exception as e:
        logger.warning(f"Could not get system metrics: {e}")

    # Check data file status
    data_file_status = None
    data_file_size_mb = None
    try:
        data_path = get_settings().data_path
        if os.path.exists(data_path):
            data_file_status = "accessible"
            data_file_size_mb = (
                os.path.getsize(data_path) / 1024 / 1024
            )  # Convert to MB
        else:
            data_file_status = "not_found"
    except Exception as e:
        logger.warning(f"Could not check data file status: {e}")
        data_file_status = "error"

    return HealthResponse(
        status="up",
        version=get_settings().api_version,
        environment="development" if get_settings().debug else "production",
        uptime_seconds=uptime_seconds,
        memory_usage_mb=memory_usage_mb,
        cpu_usage_percent=cpu_usage_percent,
        data_file_status=data_file_status,
        data_file_size_mb=data_file_size_mb,
    )


@app.get(
    "/api/v1/screen",
    response_model=ScreenResponse,
    tags=["Screening"],
    summary="Screen stocks using DGI criteria",
    description=f"""
    Filter and rank stocks based on Dividend Growth Investing (DGI) criteria.

    This endpoint applies multiple filters to find stocks that meet DGI requirements:
    - **Dividend Yield**: Minimum yield threshold for income generation
    - **Payout Ratio**: Maximum payout ratio to ensure dividend sustainability
    - **Dividend Growth**: Minimum 5-year compound annual growth rate

    Stocks are ranked by a composite score that considers yield, growth, and financial health.

    **Example Use Cases:**
    - Find high-yield dividend stocks (yield > 3%)
    - Identify sustainable dividend payers (payout < 60%)
    - Discover dividend growth champions (CAGR > 10%)

    **Rate Limiting:** {get_settings().rate_limit_requests} requests per {get_settings().rate_limit_period} seconds
    """,
    responses={
        200: {
            "description": "Successfully screened stocks",
            "content": {
                "application/json": {
                    "example": {
                        "stocks": [
                            {
                                "symbol": "JNJ",
                                "name": "Johnson & Johnson",
                                "sector": "Healthcare",
                                "industry": "Drug Manufacturers",
                                "dividend_yield": 0.025,
                                "payout": 45.2,
                                "dividend_cagr": 0.065,
                                "fcf_yield": 4.8,
                                "score": 0.82,
                            }
                        ],
                        "total_count": 1,
                        "filters_applied": {
                            "min_yield": 0.02,
                            "max_payout": 80.0,
                            "min_cagr": 0.05,
                            "top_n": 10,
                        },
                        "processing_time_ms": 15.23,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Request validation failed",
                            "status_code": 400,
                            "details": {
                                "validation_errors": [
                                    {
                                        "field": "min_yield",
                                        "message": "ensure this value is greater than 0",
                                        "type": "value_error.number.not_gt",
                                    }
                                ]
                            },
                        },
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "req-12345",
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "min_yield"],
                                "msg": "ensure this value is greater than 0",
                                "type": "value_error.number.not_gt",
                            }
                        ]
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Rate limit exceeded",
                            "status_code": 429,
                            "details": {"retry_after": 60},
                        },
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "req-12345",
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected error occurred",
                            "status_code": 500,
                            "details": {"operation": "stock_screening"},
                        },
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "req-12345",
                    }
                }
            },
        },
    },
)
@limiter.limit(
    f"{get_settings().rate_limit_requests}/{get_settings().rate_limit_period}s"
)
async def screen_stocks(
    request: Request,
    min_yield: float = Query(
        default=0.02,
        ge=get_min_yield_range()[0],
        le=get_min_yield_range()[1],
        description="Minimum dividend yield (as decimal, e.g., 0.02 for 2%)",
    ),
    max_payout: float = Query(
        default=80.0,
        ge=get_max_payout_range()[0],
        le=get_max_payout_range()[1],
        description="Maximum payout ratio (as percentage, e.g., 80.0 for 80%)",
    ),
    min_cagr: float = Query(
        default=0.05,
        ge=get_cagr_range()[0],
        le=get_cagr_range()[1],
        description="Minimum 5-year dividend CAGR (as decimal, e.g., 0.05 for 5%)",
    ),
    top_n: int = Query(
        default=10,
        ge=1,
        le=get_max_top_n(),
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
        # Use cached data loading for better performance
        df = _load_universe_cached(screener)

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

        # Apply filters with optimized processing
        filtered = _apply_filters_optimized(df, min_yield, max_payout, min_cagr)

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

        # Add scores with optimized processing
        scored = _add_scores_optimized(filtered)

        # Validate DataFrame structure
        if not StockMapper.validate_dataframe_structure(scored):
            raise DataProcessingError(
                "Invalid data structure returned from screener",
                operation="data_validation",
            )

        # Sort by score and take top N with optimized sorting
        top_stocks = _get_top_stocks_optimized(scored, top_n)

        # Convert to response models with optimized conversion
        stocks = _convert_to_responses_optimized(top_stocks)

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


@app.get(
    "/",
    response_model=APIInfoResponse,
    tags=["Root"],
    summary="Get API information",
    description="""
    Root endpoint that provides essential information about the DGI Toolkit API.

    This endpoint serves as the entry point and provides:
    - **API Overview**: Basic information about the service
    - **Version Information**: Current API version
    - **Documentation Links**: URLs to API documentation
    - **Available Endpoints**: List of all accessible endpoints
    - **Health Check URL**: Link to health monitoring endpoint

    **Use Cases:**
    - API discovery and exploration
    - Documentation navigation
    - Service information for monitoring tools
    - Client application initialization

    **Note**: This is the legacy root endpoint. For versioned access, use `/api/v1/`
    """,
    responses={
        200: {
            "description": "API information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "DGI Toolkit API",
                        "version": "1.0.0",
                        "docs_url": "/docs",
                        "health_url": "/healthz",
                        "endpoints": [
                            "/api/v1/screen",
                            "/api/v1/health",
                            "/healthz",
                            "/docs",
                            "/redoc",
                        ],
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        }
    },
)
async def root() -> APIInfoResponse:
    """Root endpoint with API information."""
    return APIInfoResponse(
        message="DGI Toolkit API",
        version=get_settings().api_version,
        docs_url="/docs",
        health_url="/healthz",
        endpoints=[
            "/api/v1/screen",
            "/api/v1/health",
            "/api/v1/cache/stats",
            "/healthz",
            "/docs",
            "/redoc",
        ],
    )


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API health status (v1)",
    description=f"""
    Versioned health check endpoint that monitors system status and performance.

    This endpoint provides real-time information about:
    - **Service Status**: Whether the API is operational
    - **System Metrics**: Memory usage, CPU utilization, and uptime
    - **Data File Status**: Accessibility and size of the data source
    - **Environment**: Current deployment environment (development/production)

    **Use Cases:**
    - Load balancer health checks
    - Monitoring system integration
    - DevOps pipeline health verification
    - Performance monitoring

    **Rate Limiting:** {get_settings().rate_limit_requests} requests per {get_settings().rate_limit_period} seconds

    **Version**: v1 - This is the versioned endpoint. For legacy access, use `/healthz`
    """,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "up",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "uptime_seconds": 3600.5,
                        "memory_usage_mb": 45.2,
                        "cpu_usage_percent": 2.1,
                        "data_file_status": "accessible",
                        "data_file_size_mb": 1.2,
                    }
                }
            },
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "down",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "uptime_seconds": 3600.5,
                        "memory_usage_mb": 45.2,
                        "cpu_usage_percent": 2.1,
                        "data_file_status": "error",
                        "data_file_size_mb": None,
                    }
                }
            },
        },
    },
)
@limiter.limit(
    f"{get_settings().rate_limit_requests}/{get_settings().rate_limit_period}s"
)
async def health_check_v1(request: Request) -> HealthResponse:
    """Versioned health check endpoint with comprehensive system information."""
    logger.debug("Versioned health check requested")

    # Calculate uptime
    uptime_seconds = None
    if startup_time is not None:
        uptime_seconds = time.time() - startup_time

    # Get system metrics
    memory_usage_mb = None
    cpu_usage_percent = None
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024  # Convert to MB
        cpu_usage_percent = process.cpu_percent(interval=0.1)
    except Exception as e:
        logger.warning(f"Could not get system metrics: {e}")

    # Check data file status
    data_file_status = None
    data_file_size_mb = None
    try:
        data_path = get_settings().data_path
        if os.path.exists(data_path):
            data_file_status = "accessible"
            data_file_size_mb = (
                os.path.getsize(data_path) / 1024 / 1024
            )  # Convert to MB
        else:
            data_file_status = "not_found"
    except Exception as e:
        logger.warning(f"Could not check data file status: {e}")
        data_file_status = "error"

    return HealthResponse(
        status="up",
        version=get_settings().api_version,
        environment="development" if get_settings().debug else "production",
        uptime_seconds=uptime_seconds,
        memory_usage_mb=memory_usage_mb,
        cpu_usage_percent=cpu_usage_percent,
        data_file_status=data_file_status,
        data_file_size_mb=data_file_size_mb,
    )


@app.get(
    "/api/v1/",
    response_model=APIInfoResponse,
    tags=["Root"],
    summary="Get API information (v1)",
    description="""
    Versioned root endpoint that provides essential information about the DGI Toolkit API.

    This endpoint serves as the versioned entry point and provides:
    - **API Overview**: Basic information about the service
    - **Version Information**: Current API version
    - **Documentation Links**: URLs to API documentation
    - **Available Endpoints**: List of all accessible endpoints
    - **Health Check URL**: Link to health monitoring endpoint

    **Use Cases:**
    - API discovery and exploration
    - Documentation navigation
    - Service information for monitoring tools
    - Client application initialization

    **Version**: v1 - This is the versioned endpoint. For legacy access, use `/`
    """,
    responses={
        200: {
            "description": "API information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "DGI Toolkit API v1",
                        "version": "1.0.0",
                        "docs_url": "/docs",
                        "health_url": "/api/v1/health",
                        "endpoints": [
                            "/api/v1/screen",
                            "/api/v1/health",
                            "/api/v1/cache/stats",
                            "/docs",
                            "/redoc",
                        ],
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        }
    },
)
async def root_v1() -> APIInfoResponse:
    """Versioned root endpoint with API information."""
    return APIInfoResponse(
        message="DGI Toolkit API v1",
        version=get_settings().api_version,
        docs_url="/docs",
        health_url="/api/v1/health",
        endpoints=["/api/v1/screen", "/api/v1/health", "/docs", "/redoc"],
    )


@app.get(
    "/api/v1/cache/stats",
    tags=["Cache"],
    summary="Get cache statistics",
    description="""
    Get statistics about the API cache including hit rates, cache size, and performance metrics.

    This endpoint provides insights into cache performance and can be used for:
    - Monitoring cache effectiveness
    - Performance optimization
    - Debugging cache issues
    - Capacity planning
    """,
    responses={
        200: {
            "description": "Cache statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "hits": 150,
                        "misses": 50,
                        "total_requests": 200,
                        "hit_rate_percent": 75.0,
                        "cache_size": 25,
                        "default_ttl": 300,
                    }
                }
            },
        }
    },
)
async def get_cache_statistics() -> dict:
    """Get cache statistics endpoint."""
    return get_cache_stats()


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


# Performance optimization helper functions
@cache_result(ttl=300, key_prefix="universe")  # Cache for 5 minutes
def _load_universe_cached(screener: Screener):
    """Load universe data with caching for better performance."""
    return screener.load_universe()


def _apply_filters_optimized(df, min_yield: float, max_payout: float, min_cagr: float):
    """Apply filters with optimized processing."""
    # Use vectorized operations for better performance
    mask = (
        (df["dividend_yield"] >= min_yield)
        & (df["payout"] <= max_payout)
        & (df["dividend_cagr"] >= min_cagr)
    )
    return df[mask].copy()


def _add_scores_optimized(df):
    """Add scores with optimized processing."""
    # Use vectorized operations for scoring
    df["score"] = (
        df["dividend_yield"] * 0.4
        + (1 - df["payout"] / 100) * 0.3
        + df["dividend_cagr"] * 0.3
    )
    return df


def _get_top_stocks_optimized(df, top_n: int):
    """Get top stocks with optimized sorting."""
    # Use nlargest for better performance than sort_values + head
    return df.nlargest(top_n, "score")


def _convert_to_responses_optimized(df):
    """Convert DataFrame to response models with optimized processing."""
    # Use list comprehension for better performance than apply
    return [
        {
            "symbol": row["symbol"],
            "name": row["name"],
            "sector": row["sector"],
            "industry": row["industry"],
            "dividend_yield": float(row["dividend_yield"]),
            "payout": float(row["payout"]),
            "dividend_cagr": float(row["dividend_cagr"]),
            "fcf_yield": float(row["fcf_yield"]),
            "score": float(row["score"]),
        }
        for _, row in df.iterrows()
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=get_settings().host,
        port=get_settings().port,
        reload=get_settings().reload,
        log_level=get_settings().log_level.lower(),
    )
