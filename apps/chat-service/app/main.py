"""
InferFlow Chat Service — FastAPI application entry point.

This service handles:
- Conversation management (future)
- LLM inference orchestration (future)
- SSE streaming responses to the frontend
- Publishing inference events to Redis Streams (future)

Architecture:
  Request → Router → Service → LLM SDK → Response (SSE stream)
                                  ↓
                          Redis Streams (fire-and-forget event publish)
"""

from contextlib import asynccontextmanager
from logging import Logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()


# -- Logging ------------------------------------------------------------------

from inferflow_shared.logging import setup_logging

logger: Logger = setup_logging("chat-service", level=settings.log_level)


# -- Lifespan -----------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Future: initialize Redis connection pool, DB engine, LLM client here.
    """
    logger.info("Chat service starting up...")
    # TODO: Initialize Redis connection pool
    # TODO: Initialize database engine
    # TODO: Initialize LLM provider client
    yield
    logger.info("Chat service shutting down...")
    # TODO: Close Redis connection pool
    # TODO: Dispose database engine


# -- App ----------------------------------------------------------------------

app = FastAPI(
    title="InferFlow Chat Service",
    description="Handles conversation management and LLM inference streaming",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers ------------------------------------------------------------------

from app.api import chat, conversations, health, models

app.include_router(health.router)
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
