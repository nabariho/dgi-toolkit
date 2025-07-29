"""API versioning functionality for DGI Toolkit API."""

import re
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import get_logger

logger = get_logger(__name__)


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware for handling API versioning and deprecation warnings."""

    def __init__(self, app, default_version: str = "v1"):
        """Initialize the API version middleware.

        Args:
            app: FastAPI application
            default_version: Default API version to use
        """
        super().__init__(app)
        self.default_version = default_version
        self.supported_versions = ["v1"]
        self.deprecated_versions = []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add version information.

        Args:
            request: FastAPI request object
            call_next: Next middleware in the chain

        Returns:
            Response with version headers
        """
        # Extract version from URL path
        version = self._extract_version_from_path(request.url.path)

        # Set version in request state for logging
        request.state.api_version = version

        # Add version headers to response
        response = await call_next(request)

        # Add version information headers
        response.headers["X-API-Version"] = version
        response.headers["X-API-Default-Version"] = self.default_version
        response.headers["X-API-Supported-Versions"] = ", ".join(
            self.supported_versions
        )

        # Add deprecation warning if using deprecated version
        if version in self.deprecated_versions:
            response.headers["X-API-Deprecation-Warning"] = (
                f"Version {version} is deprecated"
            )
            logger.warning(
                f"Deprecated API version {version} used for {request.url.path}"
            )

        return response

    def _extract_version_from_path(self, path: str) -> str:
        """Extract API version from URL path.

        Args:
            path: URL path

        Returns:
            API version string
        """
        # Check for version pattern in path: /api/v1/...
        version_match = re.match(r"/api/(v\d+)/", path)
        if version_match:
            version = version_match.group(1)
            if version in self.supported_versions:
                return version

        # Return default version if no version found or unsupported version
        return self.default_version


def get_api_version_from_request(request: Request) -> str:
    """Get API version from request.

    Args:
        request: FastAPI request object

    Returns:
        API version string
    """
    return getattr(request.state, "api_version", "v1")


def is_version_deprecated(version: str) -> bool:
    """Check if API version is deprecated.

    Args:
        version: API version string

    Returns:
        True if version is deprecated
    """
    deprecated_versions = ["v1"]  # Add versions here when they become deprecated
    return version in deprecated_versions


def get_version_deprecation_message(version: str) -> str | None:
    """Get deprecation message for API version.

    Args:
        version: API version string

    Returns:
        Deprecation message or None if not deprecated
    """
    if is_version_deprecated(version):
        return f"API version {version} is deprecated. Please upgrade to the latest version."
    return None
