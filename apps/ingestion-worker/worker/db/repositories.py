"""
Database repository for inference logs.

Uses ON CONFLICT (request_id) DO NOTHING for idempotent inserts,
safely handling Redis Streams replays.
"""

import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from inferflow_shared.logging import setup_logging
from worker.db.models import InferenceLog

logger = setup_logging("inference-repository")


class InferenceRepository:
    """Persists inference telemetry events to PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def insert(self, event: dict) -> bool:
        """
        Insert an inference log idempotently.

        Returns True if the row was inserted, False if it was a duplicate.
        """
        stmt = pg_insert(InferenceLog).values(
            request_id=uuid.UUID(event["request_id"]),
            conversation_id=uuid.UUID(event["conversation_id"]),
            event_type=event["event_type"],
            provider=event["provider"],
            model=event["model"],
            status=event.get("status"),
            ttft_ms=event.get("ttft_ms"),
            total_latency_ms=event.get("total_latency_ms"),
            prompt_tokens=event.get("prompt_tokens"),
            completion_tokens=event.get("completion_tokens"),
            total_tokens=event.get("total_tokens"),
            input_preview=event.get("input_preview"),
            output_preview=event.get("output_preview"),
            error=event.get("error"),
            event_timestamp=datetime.fromisoformat(event["timestamp"]),
            metadata_=event.get("metadata", {}),
        ).on_conflict_do_nothing(index_elements=["request_id", "event_type"])

        result = await self._session.execute(stmt)
        await self._session.commit()

        inserted = result.rowcount > 0
        if not inserted:
            logger.info(f"Duplicate event skipped | request_id={event['request_id']}")
        return inserted
