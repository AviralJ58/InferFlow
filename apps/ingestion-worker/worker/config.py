"""
Ingestion worker configuration.

Extends the shared BaseConfig with worker-specific settings.
"""

from functools import lru_cache

from inferflow_shared.config import BaseConfig


class WorkerSettings(BaseConfig):
    """Ingestion worker specific configuration."""

    # Consumer group settings
    consumer_group: str = "ingestion-group"
    consumer_name: str = "worker-1"
    stream_key: str = "llm.inference.events"
    invalid_stream_key: str = "llm.inference.invalid"

    # Polling
    block_ms: int = 5000  # Block for 5s when no messages
    batch_size: int = 10  # Read up to 10 messages per poll


@lru_cache
def get_settings() -> WorkerSettings:
    """Return cached settings instance."""
    return WorkerSettings()
