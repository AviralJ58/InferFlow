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
    consumer_group: str = "monitoring-consumers"
    consumer_name: str = "monitor-1"
    stream_key: str = "inferflow:inference_events"

    # Metrics
    metrics_flush_interval_seconds: int = 30


@lru_cache
def get_settings() -> MonitoringSettings:
    """Return cached settings instance."""
    return MonitoringSettings()
