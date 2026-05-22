"""
Normalized models and contracts for the LLM SDK.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class StreamChunk(BaseModel):
    """A single yielded chunk from an LLM stream."""
    content: str
    is_done: bool = False
    finish_reason: str | None = None
    token_usage: dict[str, int] | None = None

class ChatCompletionResult(BaseModel):
    """Final accumulated result from a chat completion."""
    content: str
    finish_reason: str | None = None
    token_usage: dict[str, int] | None = None
    latency_ms: float | None = None

class ProviderConfig(BaseModel):
    """Configuration required to initialize a provider."""
    api_key: str
    default_model: str
    timeout_ms: int = 30000
    additional_kwargs: dict[str, Any] = Field(default_factory=dict)
