"""
SSE monitoring router.

Provides Server-Sent Events (SSE) endpoints for real-time
metric streaming to dashboard clients.

Why SSE over WebSocket:
  - Monitoring is purely server→client (unidirectional).
  - SSE has native browser reconnection (EventSource).
  - Simpler protocol — no upgrade handshake needed.
  - Works through HTTP proxies and CDNs without special config.
"""

import asyncio
import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from inferflow_shared.logging import setup_logging

logger = setup_logging("monitoring-router")
router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/stream")
async def monitoring_stream(request: Request):
    """
    SSE endpoint for real-time metric updates.

    Clients connect and receive periodic MetricSnapshot frames.
    Connection is maintained until client disconnects.
    """
    broadcaster = request.app.state.broadcaster

    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                # Wait for the next snapshot from the broadcaster
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {"event": "metrics", "data": data}
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent connection timeout
                    yield {"comment": "keepalive"}
        except asyncio.CancelledError:
            pass
        finally:
            broadcaster.unsubscribe(queue)

    return EventSourceResponse(event_generator())


@router.get("/snapshot")
async def monitoring_snapshot(request: Request):
    """
    One-shot JSON endpoint returning the current MetricSnapshot.

    Useful for initial dashboard load before SSE takes over.
    """
    metrics_manager = request.app.state.metrics_manager
    snapshot = metrics_manager.snapshot()
    return snapshot.model_dump()


@router.get("/health")
async def monitoring_health(request: Request):
    """Health check with system status."""
    import time

    metrics_manager = request.app.state.metrics_manager
    broadcaster = request.app.state.broadcaster

    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - metrics_manager._start_time, 2),
        "connected_clients": broadcaster.client_count,
        "active_streams": len(metrics_manager._active_streams),
        "window_size": len(metrics_manager._events),
    }
