"""
WebSocket router for real-time monitoring.

Provides a WebSocket endpoint that:
  1. Accepts dashboard client connections
  2. Streams inference events and metrics in real-time
  3. Supports subscription filtering (future)

Architecture:
  - A background task consumes from Redis Streams
  - The MetricsManager processes events and updates aggregations
  - Connected WebSocket clients receive event fanout
  - Each client can subscribe to specific event types (future)

Why WebSocket over SSE for monitoring:
  - Bidirectional: clients can send subscription filters
  - Lower overhead for high-frequency metric updates
  - Native browser support for reconnection
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from inferflow_shared.logging import setup_logging
from app.services.connection_manager import ConnectionManager

logger = setup_logging("ws-router")
router = APIRouter(tags=["websocket"])

manager = ConnectionManager()


@router.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.

    Connected clients receive inference events as they flow
    through the system. Future: support subscription filters.
    """
    await manager.connect(websocket)
    logger.info(f"WebSocket client connected. Total: {manager.active_count}")

    try:
        while True:
            # Keep connection alive, handle incoming messages (future: filters)
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")

            # TODO: Parse subscription filter messages
            # TODO: Update client's subscription preferences

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected. Total: {manager.active_count}")


@router.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for aggregated metrics streaming.

    Sends periodic metric snapshots to connected dashboard clients.
    Future: configurable update interval.
    """
    await manager.connect(websocket)

    try:
        while True:
            # TODO: Get metrics snapshot from MetricsManager
            metrics = {
                "total_inferences": 0,
                "avg_latency_ms": 0,
                "active_conversations": 0,
                "events_per_minute": 0,
            }
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(5)  # Send metrics every 5 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket)
