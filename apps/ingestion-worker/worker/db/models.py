"""
SQLAlchemy ORM models for the ingestion worker.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class InferenceLog(Base):
    """Maps to the inference_logs table."""

    __tablename__ = "inference_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    status = Column(String)
    ttft_ms = Column(Integer)
    total_latency_ms = Column(Integer)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    input_preview = Column(Text)
    output_preview = Column(Text)
    error = Column(Text)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    metadata_ = Column("metadata", JSONB, default=dict)
