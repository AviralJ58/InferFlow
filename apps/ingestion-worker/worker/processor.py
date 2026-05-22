"""
Event processor — orchestrates the ingestion pipeline.

Pipeline stages:
  1. Validate event schema (Pydantic)
  2. Redact PII (regex)
  3. Persist to PostgreSQL (idempotent)

Returns:
  True  — event persisted successfully
  False — DB write failed (should NOT ACK)
  None  — invalid event (should route to dead-letter)
"""

from inferflow_shared.logging import setup_logging
from worker.config import get_settings
from worker.db.engine import async_session
from worker.db.repositories import InferenceRepository
from worker.pipeline.redactor import PIIRedactor
from worker.pipeline.validator import EventValidator

settings = get_settings()
logger = setup_logging("event-processor", level=settings.log_level)


class EventProcessor:
    """Processes individual inference events through the ingestion pipeline."""

    async def process(self, raw_payload: str) -> bool | None:
        """
        Process a single inference event.

        Args:
            raw_payload: Raw JSON string from Redis Streams.

        Returns:
            True if persisted, False if DB failed, None if invalid.
        """
        # Stage 1: Validate
        event = EventValidator.validate(raw_payload)
        if event is None:
            logger.warning("Invalid event payload, routing to dead-letter")
            return None

        request_id = event.get("request_id", "unknown")
        event_type = event.get("event_type", "unknown")
        conversation_id = event.get("conversation_id", "unknown")

        logger.info(
            f"Processing event | type={event_type} "
            f"request_id={request_id} conversation_id={conversation_id}"
        )

        # Stage 2: Redact PII
        event = PIIRedactor.redact(event)

        # Stage 3: Persist
        try:
            async with async_session() as session:
                repo = InferenceRepository(session)
                inserted = await repo.insert(event)

                if inserted:
                    logger.info(
                        f"Event persisted | type={event_type} request_id={request_id}"
                    )
                else:
                    logger.info(
                        f"Duplicate event skipped | type={event_type} request_id={request_id}"
                    )
                return True

        except Exception:
            logger.exception(
                f"DB write failed | type={event_type} request_id={request_id}"
            )
            return False
