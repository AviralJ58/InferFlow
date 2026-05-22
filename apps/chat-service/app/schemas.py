"""
Request/response schemas for the chat service.

Uses Pydantic v2 models for validation and serialization.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message content")
    conversation_id: str | None = Field(
        None, description="Existing conversation ID. None to start a new conversation."
    )
    model: str | None = Field(None, description="LLM model override (future)")


class ChatResponse(BaseModel):
    """Chat response returned to the frontend."""

    message: str = Field(..., description="Assistant response content")
    conversation_id: str = Field(..., description="Conversation ID")
    model: str | None = Field(None, description="Model used for inference")


class InferenceEvent(BaseModel):
    """
    Normalized inference event published to Redis Streams.

    This is the canonical event shape that downstream consumers
    (ingestion-worker, monitoring-service) will process.

    Future: add token counts, latency metrics, cost estimation.
    """

    conversation_id: str
    message_id: str
    user_message: str
    assistant_message: str
    model: str
    latency_ms: float | None = None
    token_usage: dict[str, int] | None = None
    metadata: dict | None = None
