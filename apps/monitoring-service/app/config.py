"""
Monitoring service configuration.

Extends the shared BaseConfig with monitoring-specific settings.
"""

from functools import lru_cache

from inferflow_shared.config import BaseConfig


class MonitoringSettings(BaseConfig):
    """Monitoring service specific configuration."""

    # Service
    monitoring_service_host: str = "0.0.0.0"
    monitoring_service_port: int = 8001

    # Redis Streams consumer
    consumer_group: str = "monitoring-group"
    consumer_name: str = "monitor-1"
    stream_key: str = "llm.inference.events"

    # Polling
    block_ms: int = 2000  # Block for 2s when no messages
    batch_size: int = 50  # Read up to 50 messages per poll

    # Rolling window
    window_seconds: int = 300  # 5-minute rolling window

    # SSE push frequency
    snapshot_interval_seconds: int = 2  # Push metrics every 2 seconds


@lru_cache
def get_settings() -> MonitoringSettings:
    """Return cached settings instance."""
    return MonitoringSettings()
