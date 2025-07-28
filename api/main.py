"""FastAPI application for DGI Toolkit API service."""

import os
import time
from contextlib import asynccontextmanager

import psutil
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Query,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from dgi.screener import Screener
from dgi.services import ScreeningService, ValidationService

from .async_processing import (
    JobPriority,
    JobStatus,
    ScreeningJob,
    get_job_queue,
    submit_background_screening,
)
from .caching import cache_result, get_cache_stats
from .config import get_settings, validate_configuration
from .dependencies import get_screener
from .error_handlers import register_exception_handlers
from .exceptions import APIException, ConfigurationError
from .logging_config import RequestContextMiddleware, get_logger, setup_logging
from .observability import get_metrics, get_observability_manager, instrument_fastapi
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
    try:
        return get_settings().min_yield_range
    except Exception:
        return (0.0, 100.0)


def get_max_payout_range():
    """Get maximum payout range for Query validation."""
    try:
        return get_settings().max_payout_range
    except Exception:
        return (0.0, 200.0)


def get_cagr_range():
    """Get CAGR range for Query validation."""
    try:
        return get_settings().cagr_range
    except Exception:
        return (-100.0, 100.0)


def get_max_top_n():
    """Get maximum top N for Query validation."""
    try:
        return get_settings().max_top_n
    except Exception:
        return 100


def validate_uuid_format(job_id: str) -> str:
    """Validate that job_id is a valid UUID format using service layer."""
    return ValidationService.validate_uuid_format(job_id, "job_id")


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

# Instrument FastAPI with OpenTelemetry
instrument_fastapi(app)


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
@limiter.limit("100/minute")
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
@limiter.limit("50/minute")
async def screen_stocks(
    request: Request,
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
        default=10,
        ge=1,
        le=1000,
        description="Number of top stocks to return",
    ),
    screener: Screener = Depends(get_screener),
) -> ScreenResponse:
    """Screen stocks using DGI criteria with observability."""
    start_time = time.time()
    observability_manager = get_observability_manager()

    try:
        # Log business event
        observability_manager.log_business_event(
            "stock_screening_started",
            {
                "min_yield": min_yield,
                "max_payout": max_payout,
                "min_cagr": min_cagr,
                "top_n": top_n,
            },
        )

        # Trace the operation
        async with observability_manager.trace_operation(
            "screen_stocks",
            {
                "min_yield": min_yield,
                "max_payout": max_payout,
                "min_cagr": min_cagr,
                "top_n": top_n,
            },
        ):
            # Log screening parameters
            logger.info(
                f"Screening stocks with parameters: min_yield={min_yield}, "
                f"max_payout={max_payout}, min_cagr={min_cagr}, top_n={top_n}"
            )

            # Load universe data with caching
            universe_df = _load_universe_cached(screener)

            # Apply screening criteria using service layer
            filtered_df = ScreeningService.apply_screening_criteria(
                universe_df, min_yield, max_payout, min_cagr
            )

            # Add scores using service layer
            scored_df = ScreeningService.score_dataframe(filtered_df)

            # Get top stocks using service layer
            top_stocks_df = ScreeningService.get_top_stocks(scored_df, top_n)

            # Convert to response format using service layer
            stocks = ScreeningService.convert_to_response_format(top_stocks_df)

            # Calculate processing time
            processing_time = (
                time.time() - start_time
            ) * 1000  # Convert to milliseconds

            # Record screening metrics
            observability_manager.record_screening_operation(
                len(stocks),
                time.time() - start_time,
                {
                    "min_yield": min_yield,
                    "max_payout": max_payout,
                    "min_cagr": min_cagr,
                    "top_n": top_n,
                },
            )

            # Log completion
            logger.info(
                f"Screening completed: {len(stocks)} stocks returned in {processing_time:.2f}ms"
            )

            # Log business event
            observability_manager.log_business_event(
                "stock_screening_completed",
                {
                    "stocks_returned": len(stocks),
                    "processing_time_ms": processing_time,
                    "filters_applied": {
                        "min_yield": min_yield,
                        "max_payout": max_payout,
                        "min_cagr": min_cagr,
                        "top_n": top_n,
                    },
                },
            )

            return ScreenResponse(
                stocks=stocks,
                total_count=len(stocks),
                filters_applied={
                    "min_yield": min_yield,
                    "max_payout": max_payout,
                    "min_cagr": min_cagr,
                    "top_n": top_n,
                },
                processing_time_ms=processing_time,
            )

    except Exception as e:
        # Record error metrics
        observability_manager.record_error("screening_error", str(e), "/api/v1/screen")

        # Log business event
        observability_manager.log_business_event(
            "stock_screening_error",
            {
                "error": str(e),
                "parameters": {
                    "min_yield": min_yield,
                    "max_payout": max_payout,
                    "min_cagr": min_cagr,
                    "top_n": top_n,
                },
            },
        )

        logger.error(f"Screening error: {e}")
        raise


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
@limiter.limit("100/minute")
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


@app.get(
    "/metrics",
    tags=["Monitoring"],
    summary="Get Prometheus metrics",
    description="""
    Get Prometheus-formatted metrics for monitoring and alerting.

    This endpoint provides comprehensive metrics including:
    - **Request Metrics**: Total requests, duration, status codes
    - **Business Metrics**: Screening operations, cache performance
    - **Error Metrics**: Error counts by type and endpoint
    - **System Metrics**: Service information and health

    **Use Cases:**
    - Prometheus monitoring integration
    - Grafana dashboard creation
    - Alerting rule configuration
    - Performance analysis

    **Format**: Prometheus text format
    """,
    responses={
        200: {
            "description": "Prometheus metrics in text format",
            "content": {
                "text/plain": {
                    "example": """
# HELP dgi_requests_total Total number of API requests
# TYPE dgi_requests_total counter
dgi_requests_total{method="GET",path="/healthz",status_code="200"} 150

# HELP dgi_request_duration_seconds Request duration in seconds
# TYPE dgi_request_duration_seconds histogram
dgi_request_duration_seconds_bucket{method="GET",path="/healthz",status_code="200",le="0.1"} 120
dgi_request_duration_seconds_bucket{method="GET",path="/healthz",status_code="200",le="0.5"} 150

# HELP dgi_screening_operations_total Total number of stock screening operations
# TYPE dgi_screening_operations_total counter
dgi_screening_operations_total{stocks_returned="5",filters_applied="4"} 25
                    """
                }
            },
        }
    },
)
async def get_metrics_endpoint() -> str:
    """Get Prometheus metrics endpoint."""
    return get_metrics()


@app.post(
    "/api/v1/screen/async",
    tags=["Async Screening"],
    summary="Submit async stock screening job",
    description="""
    Submit a stock screening job for background processing.

    This endpoint allows you to submit screening jobs that will be processed asynchronously.
    The job will be queued and processed in the background, and you can check its status
    using the job ID returned in the response.

    **Features:**
    - Background processing for large datasets
    - Job queue management with priority levels
    - Progress tracking and status monitoring
    - Result caching for expensive operations

    **Use Cases:**
    - Processing large stock universes
    - Batch screening operations
    - Long-running analysis tasks
    - Resource-intensive calculations

    **Job Priorities:**
    - **LOW**: Background processing, no urgency
    - **NORMAL**: Standard processing (default)
    - **HIGH**: Priority processing
    - **URGENT**: Immediate processing
    """,
    responses={
        202: {
            "description": "Job submitted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "pending",
                        "message": "Job submitted successfully",
                        "estimated_completion": "2024-01-15T10:35:00Z",
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
                        }
                    }
                }
            },
        },
    },
)
async def submit_async_screening(
    request: Request,
    background_tasks: BackgroundTasks,
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
        default=10,
        ge=1,
        le=1000,
        description="Number of top stocks to return",
    ),
    priority: JobPriority = Query(
        default=JobPriority.NORMAL, description="Job priority level"
    ),
    user_id: str | None = Query(
        default=None,
        description="User ID for job tracking",
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    ),
) -> dict:
    """Submit an async screening job."""
    correlation_id = getattr(request.state, "correlation_id", None)

    job_id = await submit_background_screening(
        background_tasks=background_tasks,
        min_yield=min_yield,
        max_payout=max_payout,
        min_cagr=min_cagr,
        top_n=top_n,
        priority=priority,
        user_id=user_id,
        correlation_id=correlation_id,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Job submitted successfully",
        "estimated_completion": None,  # Could be calculated based on queue length
    }


@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=ScreeningJob,
    tags=["Async Screening"],
    summary="Get job status",
    description="""
    Get the current status and progress of an async screening job.

    This endpoint provides detailed information about a background job including:
    - Current status (pending, running, completed, failed, cancelled)
    - Progress percentage and current step
    - Job parameters and results (when completed)
    - Error information (if failed)
    - Timing information (created, started, completed)

    **Use Cases:**
    - Monitor job progress
    - Retrieve completed results
    - Debug failed jobs
    - Track job timing
    """,
    responses={
        200: {
            "description": "Job status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "running",
                        "priority": "normal",
                        "created_at": "2024-01-15T10:30:00Z",
                        "started_at": "2024-01-15T10:30:05Z",
                        "completed_at": None,
                        "progress": 0.5,
                        "total_steps": 5,
                        "current_step": 3,
                        "step_description": "Calculating scores",
                        "min_yield": 0.02,
                        "max_payout": 80.0,
                        "min_cagr": 0.05,
                        "top_n": 10,
                        "result": None,
                        "error_message": None,
                        "user_id": "user123",
                        "correlation_id": "req-12345",
                    }
                }
            },
        },
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "JOB_NOT_FOUND",
                            "message": "Job not found",
                            "status_code": 404,
                        }
                    }
                }
            },
        },
    },
)
async def get_job_status(
    job_id: str = Path(..., description="Job ID (UUID format)"),
) -> ScreeningJob:
    """Get the status of an async screening job."""
    # Validate UUID format
    try:
        validate_uuid_format(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid job ID format: {e}")

    queue = await get_job_queue()
    job = await queue.get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "status_code": 404,
                }
            },
        )

    return job


@app.delete(
    "/api/v1/jobs/{job_id}",
    tags=["Async Screening"],
    summary="Cancel job",
    description="""
    Cancel a pending or running async screening job.

    This endpoint allows you to cancel a job that is still pending or currently running.
    Completed, failed, or already cancelled jobs cannot be cancelled.

    **Use Cases:**
    - Cancel unnecessary jobs
    - Free up queue capacity
    - Stop long-running operations
    - Resource management
    """,
    responses={
        200: {
            "description": "Job cancelled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "cancelled",
                        "message": "Job cancelled successfully",
                    }
                }
            },
        },
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "JOB_NOT_FOUND",
                            "message": "Job not found",
                            "status_code": 404,
                        }
                    }
                }
            },
        },
        400: {
            "description": "Job cannot be cancelled",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "JOB_CANNOT_CANCEL",
                            "message": "Job is already completed and cannot be cancelled",
                            "status_code": 400,
                        }
                    }
                }
            },
        },
    },
)
async def cancel_job(
    job_id: str = Path(..., description="Job ID (UUID format)"),
) -> dict:
    """Cancel an async screening job."""
    # Validate UUID format
    try:
        validate_uuid_format(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid job ID format: {e}")

    queue = await get_job_queue()
    cancelled = await queue.cancel_job(job_id)

    if not cancelled:
        # Check if job exists
        job = await queue.get_job_status(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "JOB_NOT_FOUND",
                        "message": f"Job {job_id} not found",
                        "status_code": 404,
                    }
                },
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "JOB_CANNOT_CANCEL",
                        "message": f"Job {job_id} is already {job.status.value} and cannot be cancelled",
                        "status_code": 400,
                    }
                },
            )

    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancelled successfully",
    }


@app.get(
    "/api/v1/jobs",
    tags=["Async Screening"],
    summary="List jobs",
    description="""
    List async screening jobs with optional filtering.

    This endpoint provides a list of jobs with optional filtering by status and user.
    Jobs are sorted by creation time (newest first).

    **Use Cases:**
    - Monitor all jobs
    - Filter by status
    - User-specific job tracking
    - Queue management
    """,
    responses={
        200: {
            "description": "Jobs retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "jobs": [
                            {
                                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "completed",
                                "priority": "normal",
                                "created_at": "2024-01-15T10:30:00Z",
                                "progress": 1.0,
                                "total_steps": 5,
                                "current_step": 5,
                                "step_description": "Completed",
                            }
                        ],
                        "total_count": 1,
                        "filters_applied": {
                            "status": "completed",
                            "user_id": "user123",
                        },
                    }
                }
            },
        }
    },
)
async def list_jobs(
    status: JobStatus | None = Query(default=None, description="Filter by job status"),
    user_id: str | None = Query(
        default=None,
        description="Filter by user ID",
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    ),
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of jobs to return"
    ),
) -> dict:
    """List async screening jobs."""
    queue = await get_job_queue()
    jobs = await queue.list_jobs(status=status, user_id=user_id, limit=limit)

    return {
        "jobs": jobs,
        "total_count": len(jobs),
        "filters_applied": {
            "status": status.value if status else None,
            "user_id": user_id,
        },
    }


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


# Caching helper function
@cache_result(ttl=300, key_prefix="universe")  # Cache for 5 minutes
def _load_universe_cached(screener: Screener):
    """Load universe data with caching for better performance."""
    return screener.load_universe()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=get_settings().host,
        port=get_settings().port,
        reload=get_settings().reload,
        log_level=get_settings().log_level.lower(),
    )
