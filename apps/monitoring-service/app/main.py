"""
InferFlow Monitoring Service — FastAPI application entry point.

This service provides:
  - Real-time event fanout via WebSocket connections
  - Metrics aggregation and exposure (future: Prometheus-compatible)
  - Dashboard data APIs (future)

Architecture:
  Redis Streams → Consumer → MetricsManager → WebSocket fanout
                                    ↓
                            Metrics aggregation (future)

Why WebSocket (not SSE) for monitoring:
  - Monitoring dashboards need bidirectional communication
    (e.g., subscribing to specific event types, requesting historical data)
  - WebSocket provides lower overhead for high-frequency updates
  - SSE is better suited for unidirectional chat streaming
"""

from contextlib import asynccontextmanager
from logging import Logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, websocket

settings = get_settings()

# -- Logging ------------------------------------------------------------------

from inferflow_shared.logging import setup_logging

logger: Logger = setup_logging("monitoring-service", level=settings.log_level)


# -- Lifespan -----------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Future: start Redis Streams consumer task, initialize metrics manager.
    """
    logger.info("Monitoring service starting up...")
    # TODO: Start background Redis Streams consumer
    # TODO: Initialize MetricsManager
    yield
    logger.info("Monitoring service shutting down...")
    # TODO: Stop background consumer
    # TODO: Flush metrics


# -- App ----------------------------------------------------------------------

app = FastAPI(
    title="InferFlow Monitoring Service",
    description="Real-time monitoring, metrics, and event fanout",
    version="0.1.0",
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
app.include_router(websocket.router)
