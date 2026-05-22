"""
Normalized telemetry events for LLM inference.
"""

from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class BaseInferenceEvent(BaseModel):
    """Base schema for all inference events."""
    event_type: str
    request_id: str
    conversation_id: str
    provider: str
    model: str
    timestamp: str = Field(default_factory=utc_now)

class InferenceStartedEvent(BaseInferenceEvent):
    """Emitted when a stream request begins."""
    event_type: Literal["inference_started"] = "inference_started"

class InferenceCompletedEvent(BaseInferenceEvent):
    """Emitted when a stream request completes successfully."""
    event_type: Literal["inference_completed"] = "inference_completed"
    ttft_ms: int
    total_latency_ms: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    status: Literal["success"] = "success"

class InferenceFailedEvent(BaseInferenceEvent):
    """Emitted when a stream request fails due to an exception."""
    event_type: Literal["inference_failed"] = "inference_failed"
    ttft_ms: Optional[int] = None
    total_latency_ms: int
    error: str
    status: Literal["failed"] = "failed"

class InferenceCancelledEvent(BaseInferenceEvent):
    """Emitted when a stream request is cancelled (e.g. by the user or client disconnect)."""
    event_type: Literal["inference_cancelled"] = "inference_cancelled"
    ttft_ms: Optional[int] = None
    total_latency_ms: int
    status: Literal["cancelled"] = "cancelled"
