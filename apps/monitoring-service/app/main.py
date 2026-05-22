"""
InferFlow Monitoring Service — FastAPI application entry point.

This service provides:
  - Real-time metrics aggregation from Redis Streams events
  - SSE-based metric broadcasting to dashboard clients
  - Rolling-window in-memory aggregation (no DB polling)

Architecture:
  Redis Streams → Consumer (monitoring-group) → MetricsManager → SSE broadcast
                                                      ↓
                                              Rolling-window deque

Why SSE (not WebSocket) for monitoring:
  - Monitoring is server→client only (unidirectional push).
  - SSE has native browser reconnection via EventSource.
  - Simpler protocol — works through proxies without upgrade.
  - WebSocket's bidirectional capability is unnecessary here.
"""

import asyncio
from contextlib import asynccontextmanager
from logging import Logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, monitoring
from app.services.consumer import MonitoringConsumer
from app.services.metrics_manager import MetricsManager
from app.services.sse_broadcaster import SSEBroadcaster

settings = get_settings()

# -- Logging ------------------------------------------------------------------

from inferflow_shared.logging import setup_logging

logger: Logger = setup_logging("monitoring-service", level=settings.log_level)


# -- Lifespan -----------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Starts the Redis consumer and SSE broadcaster as background tasks.
    Gracefully shuts them down on exit.
    """
    logger.info("Monitoring service starting up...")

    # Initialize core components
    shutdown_event = asyncio.Event()
    metrics_manager = MetricsManager()
    consumer = MonitoringConsumer(metrics_manager)
    broadcaster = SSEBroadcaster(metrics_manager)

    # Store on app.state so routers can access them
    app.state.metrics_manager = metrics_manager
    app.state.broadcaster = broadcaster
    app.state.shutdown_event = shutdown_event

    # Start background tasks
    consumer_task = asyncio.create_task(consumer.start(shutdown_event))
    broadcast_task = asyncio.create_task(broadcaster.start_periodic_broadcast(shutdown_event))

    logger.info("Background tasks started (consumer + broadcaster)")

    yield

    # Graceful shutdown
    logger.info("Monitoring service shutting down...")
    shutdown_event.set()

    consumer_task.cancel()
    broadcast_task.cancel()

    try:
        await asyncio.gather(consumer_task, broadcast_task, return_exceptions=True)
    except Exception:
        pass

    await consumer.stop()
    logger.info("Monitoring service stopped.")


# -- App ----------------------------------------------------------------------

app = FastAPI(
    title="InferFlow Monitoring Service",
    description="Real-time monitoring, metrics aggregation, and SSE broadcasting",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers ------------------------------------------------------------------

app.include_router(health.router)
app.include_router(monitoring.router)
