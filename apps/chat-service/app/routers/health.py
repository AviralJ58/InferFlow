"""
Health check router.

Provides liveness and readiness probes for Docker healthchecks
and orchestrator monitoring.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Liveness probe.

    Future: check Redis connectivity, DB connectivity, LLM provider health.
    """
    return {
        "status": "healthy",
        "service": "chat-service",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe.

    Future: verify all downstream dependencies are reachable.
    """
    # TODO: Check Redis connection
    # TODO: Check database connection
    return {"status": "ready"}
