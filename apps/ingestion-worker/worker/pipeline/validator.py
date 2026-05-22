"""
Event validation using the shared telemetry event contracts.

Invalid payloads are routed to a dead-letter stream instead of crashing the worker.
"""

import json
from typing import Optional

from pydantic import ValidationError

from inferflow_shared.logging import setup_logging
from inferflow_shared.telemetry.events import (
    BaseInferenceEvent,
    InferenceCancelledEvent,
    InferenceCompletedEvent,
    InferenceFailedEvent,
    InferenceStartedEvent,
)

logger = setup_logging("event-validator")

EVENT_TYPE_MAP = {
    "inference_started": InferenceStartedEvent,
    "inference_completed": InferenceCompletedEvent,
    "inference_failed": InferenceFailedEvent,
    "inference_cancelled": InferenceCancelledEvent,
}


class EventValidator:
    """Validates raw event payloads against the telemetry contracts."""

    @staticmethod
    def validate(raw_payload: str) -> Optional[dict]:
        """
        Parse and validate a raw JSON payload.

        Returns the validated event dict if valid, None otherwise.
        """
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return None

        event_type = data.get("event_type")
        model_class = EVENT_TYPE_MAP.get(event_type)

        if not model_class:
            logger.warning(f"Unknown event_type: {event_type}")
            return None

        try:
            validated = model_class.model_validate(data)
            return validated.model_dump()
        except ValidationError as e:
            logger.error(f"Validation failed for {event_type}: {e}")
            return None
