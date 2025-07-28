"""Global exception handlers for DGI Toolkit API."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import APIException, DataProcessingError
from .exceptions import ValidationError as APIValidationError
from .logging_config import get_logger

logger = get_logger(__name__)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions.

    Args:
        request: FastAPI request object
        exc: API exception instance

    Returns:
        JSONResponse with error details
    """
    # Get correlation ID from request state if available
    correlation_id = getattr(request.state, "correlation_id", None)

    # Log the error with context
    logger.error(
        f"API Exception: {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Return structured error response
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers={"X-Correlation-ID": correlation_id} if correlation_id else None,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError | ValidationError
) -> JSONResponse:
    """Handle validation exceptions.

    Args:
        request: FastAPI request object
        exc: Validation exception instance

    Returns:
        JSONResponse with validation error details
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    # Extract validation errors
    errors = exc.errors() if isinstance(exc, RequestValidationError) else exc.errors()

    # Format validation errors
    formatted_errors = []
    for error in errors:
        formatted_errors.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    # Create API validation error
    api_error = APIValidationError(
        message="Request validation failed",
        details={"validation_errors": formatted_errors},
    )

    logger.warning(
        f"Validation Error: {len(formatted_errors)} validation errors",
        extra={
            "correlation_id": correlation_id,
            "validation_errors": formatted_errors,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return await api_exception_handler(request, api_error)


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Handle rate limit exceptions.

    Args:
        request: FastAPI request object
        exc: Rate limit exception instance

    Returns:
        JSONResponse with rate limit error details
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    # Extract retry after information
    retry_after = getattr(exc, "retry_after", None)

    from .exceptions import RateLimitExceededError

    api_error = RateLimitExceededError(
        message="Rate limit exceeded", retry_after=retry_after
    )

    logger.warning(
        f"Rate Limit Exceeded: {request.client.host}",
        extra={
            "correlation_id": correlation_id,
            "client_ip": request.client.host,
            "retry_after": retry_after,
            "path": request.url.path,
            "method": request.method,
        },
    )

    response = await api_exception_handler(request, api_error)

    # Add retry-after header if available
    if retry_after:
        response.headers["Retry-After"] = str(retry_after)

    return response


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions.

    Args:
        request: FastAPI request object
        exc: HTTP exception instance

    Returns:
        JSONResponse with error details
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    # Map to appropriate API exception
    if exc.status_code == 404:
        from .exceptions import DataNotFoundError

        api_error = DataNotFoundError("Resource not found")
    elif exc.status_code == 400:
        from .exceptions import BadRequestError

        api_error = BadRequestError(exc.detail or "Bad request")
    elif exc.status_code == 401:
        from .exceptions import UnauthorizedError

        api_error = UnauthorizedError(exc.detail or "Authentication required")
    elif exc.status_code == 403:
        from .exceptions import ForbiddenError

        api_error = ForbiddenError(exc.detail or "Access forbidden")
    else:
        # Create generic API exception
        api_error = APIException(
            message=exc.detail or "HTTP error occurred", status_code=exc.status_code
        )

    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return await api_exception_handler(request, api_error)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions.

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSONResponse with error details
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    # Log the full exception with traceback
    logger.error(
        f"Unhandled Exception: {exc!s}",
        exc_info=True,
        extra={
            "correlation_id": correlation_id,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Create generic error response
    api_error = DataProcessingError(
        message="An unexpected error occurred",
        operation="request_processing",
        details={"exception_type": type(exc).__name__},
    )

    return await api_exception_handler(request, api_error)


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Register custom API exception handler
    app.add_exception_handler(APIException, api_exception_handler)

    # Register validation exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Register rate limit exception handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

    # Register HTTP exception handler
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Register general exception handler (should be last)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered successfully")
