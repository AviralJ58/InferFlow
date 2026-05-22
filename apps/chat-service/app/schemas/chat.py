"""
Chat API schemas.
"""

from pydantic import BaseModel, Field


class StreamChatRequest(BaseModel):
    """Incoming chat message request for streaming."""
    conversation_id: str = Field(..., description="The conversation ID to append to")
    message: str = Field(..., min_length=1, max_length=10000, description="User message content")
    model: str | None = Field(None, description="Model override")

class StreamEventData(BaseModel):
    """Schema for the data payload inside an SSE event."""
    message_id: str
    conversation_id: str
    content: str = ""
    is_done: bool = False

class InferenceEvent(BaseModel):
    """
    Normalized inference event published to Redis Streams.
    (Preserved from scaffolding)
    """
    conversation_id: str
    message_id: str
    user_message: str
    assistant_message: str
    model: str
    latency_ms: float | None = None
    token_usage: dict[str, int] | None = None
    metadata: dict | None = None
