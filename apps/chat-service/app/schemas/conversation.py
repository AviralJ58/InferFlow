"""
Conversation API schemas.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CreateConversationRequest(BaseModel):
    title: str | None = Field(default=None)
