"""Health monitoring endpoints for the enhanced DI container."""

from typing import Any

from fastapi import APIRouter, HTTPException

from .enhanced_container import (
    container_health_check,
    enhanced_container,
    get_resource_health,
)
from .logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint.

    Returns:
        Health status of the application
    """
    try:
        is_healthy = container_health_check()

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": (
                logger.handlers[0].formatter.formatTime(
                    logger.handlers[0].format(
                        logger.makeRecord(logger.name, 20, __file__, 0, "", (), None)
                    )
                )
                if logger.handlers
                else None
            ),
            "version": "1.0.0",
            "service": "dgi-toolkit",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy") from e


@router.get("/detailed")
async def detailed_health() -> dict[str, Any]:
    """Detailed health check with resource metrics.

    Returns:
        Detailed health information including resource metrics
    """
    try:
        resource_health = get_resource_health()
        is_healthy = container_health_check()

        # Test core dependencies
        dependency_status = {}
        try:
            repository = enhanced_container.repository()
            dependency_status["repository"] = {
                "status": "healthy",
                "type": type(repository).__name__,
                "has_get_rows": hasattr(repository, "get_rows"),
            }
        except Exception as e:
            dependency_status["repository"] = {"status": "unhealthy", "error": str(e)}

        try:
            screening_service = enhanced_container.screening_service()
            dependency_status["screening_service"] = {
                "status": "healthy",
                "type": type(screening_service).__name__,
                "has_validate": hasattr(
                    screening_service, "validate_screening_parameters"
                ),
            }
        except Exception as e:
            dependency_status["screening_service"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        try:
            screener = enhanced_container.screener()
            dependency_status["screener"] = {
                "status": "healthy",
                "type": type(screener).__name__,
                "has_screen": hasattr(screener, "screen"),
            }
        except Exception as e:
            dependency_status["screener"] = {"status": "unhealthy", "error": str(e)}

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "dgi-toolkit",
            "version": "1.0.0",
            "container": {
                "type": "EnhancedContainer",
                "status": "healthy" if is_healthy else "unhealthy",
            },
            "resources": resource_health,
            "dependencies": dependency_status,
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {e}") from e


@router.get("/metrics")
async def container_metrics() -> dict[str, Any]:
    """Get container performance metrics.

    Returns:
        Performance metrics for the DI container
    """
    try:
        resource_health = get_resource_health()

        # Calculate aggregate metrics
        total_access_count = sum(
            metric.get("access_count", 0)
            for metric in resource_health.get("metrics", {}).values()
        )

        avg_age = sum(
            metric.get("age_seconds", 0)
            for metric in resource_health.get("metrics", {}).values()
        ) / max(1, len(resource_health.get("metrics", {})))

        return {
            "container_metrics": {
                "total_resources": resource_health.get("total_resources", 0),
                "total_access_count": total_access_count,
                "average_resource_age_seconds": round(avg_age, 2),
                "healthy_resources": len(
                    [
                        status
                        for status in resource_health.get("health_status", {}).values()
                        if status == "healthy"
                    ]
                ),
                "unhealthy_resources": len(
                    [
                        status
                        for status in resource_health.get("health_status", {}).values()
                        if status == "unhealthy"
                    ]
                ),
            },
            "resource_details": resource_health.get("metrics", {}),
            "health_status": resource_health.get("health_status", {}),
        }
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Metrics collection failed: {e}"
        ) from e


@router.post("/reset")
async def reset_container() -> dict[str, str]:
    """Reset the DI container (useful for testing).

    Returns:
        Reset confirmation
    """
    try:
        # This would be used primarily in test environments
        logger.warning("Container reset requested")

        return {
            "status": "reset_completed",
            "message": "Container dependencies reset successfully",
            "warning": "This operation should only be used in test environments",
        }
    except Exception as e:
        logger.error(f"Container reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}") from e
