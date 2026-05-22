"""
Core domain models for the chat service.

These represent the internal business entities, decoupled from
API schemas (Pydantic) and database models (SQLAlchemy/SQLModel).
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal


@dataclass
class Message:
    """A single message in a conversation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"] = "user"
    content: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Conversation:
    """A conversation containing a list of messages."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StreamEvent:
    """An event yielded during an SSE streaming response."""
    event_type: Literal["token", "error", "done"]
    data: str
