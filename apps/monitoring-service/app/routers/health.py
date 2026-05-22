"""
Health check router for the monitoring service.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Liveness probe."""
    return {
        "status": "healthy",
        "service": "monitoring-service",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check():
    """Readiness probe."""
    # TODO: Check Redis connection
    return {"status": "ready"}
