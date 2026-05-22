"""
PII redaction layer.

Applies regex-based redaction to event fields before persistence.
Targets error messages which are the most likely source of
accidentally leaked PII in LLM error payloads.
"""

import re

from inferflow_shared.logging import setup_logging

logger = setup_logging("pii-redactor")

# Patterns
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

REDACTED = "[REDACTED]"


class PIIRedactor:
    """Redacts PII from event payloads before persistence."""

    @staticmethod
    def redact(event: dict) -> dict:
        """
        Redact PII from string fields in the event dict.
        Currently targets the 'error', 'input_preview', and 'output_preview' fields.
        """
        for field in ["error", "input_preview", "output_preview"]:
            if field in event and event[field]:
                event[field] = PIIRedactor._redact_string(event[field])
        return event

    @staticmethod
    def _redact_string(value: str) -> str:
        """Apply all PII patterns to a string."""
        value = EMAIL_PATTERN.sub(REDACTED, value)
        value = PHONE_PATTERN.sub(REDACTED, value)
        value = CREDIT_CARD_PATTERN.sub(REDACTED, value)
        return value
