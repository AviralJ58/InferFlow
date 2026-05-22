"""
Metrics manager — aggregates and tracks system metrics.

Responsibilities:
  - Process incoming inference events
  - Maintain running aggregations (counts, latencies, etc.)
  - Provide metric snapshots for WebSocket streaming
  - Future: expose Prometheus-compatible metrics endpoint

This runs as part of the monitoring service and is fed
events from the Redis Streams consumer background task.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from inferflow_shared.logging import setup_logging

logger = setup_logging("metrics-manager")


@dataclass
class MetricsSnapshot:
    """Point-in-time snapshot of system metrics."""

    total_inferences: int = 0
    total_conversations: int = 0
    avg_latency_ms: float = 0.0
    events_per_minute: float = 0.0
    last_event_at: str | None = None
    error_count: int = 0


class MetricsManager:
    """
    Aggregates inference events into system metrics.

    Thread-safe for use with async background tasks.
    Future: back with Redis for persistence across restarts.
    """

    def __init__(self):
        self._total_inferences: int = 0
        self._total_latency_ms: float = 0.0
        self._error_count: int = 0
        self._conversations: set[str] = set()
        self._last_event_at: datetime | None = None

    async def process_event(self, event: dict) -> None:
        """
        Process an inference event and update metrics.

        Args:
            event: Raw inference event data from Redis Streams.
        """
        self._total_inferences += 1
        self._last_event_at = datetime.now(timezone.utc)

        if conversation_id := event.get("conversation_id"):
            self._conversations.add(conversation_id)

        if latency := event.get("latency_ms"):
            self._total_latency_ms += float(latency)

        logger.debug(f"Metrics updated. Total inferences: {self._total_inferences}")

    def snapshot(self) -> MetricsSnapshot:
        """Return a point-in-time metrics snapshot."""
        avg_latency = (
            self._total_latency_ms / self._total_inferences
            if self._total_inferences > 0
            else 0.0
        )

        return MetricsSnapshot(
            total_inferences=self._total_inferences,
            total_conversations=len(self._conversations),
            avg_latency_ms=round(avg_latency, 2),
            last_event_at=self._last_event_at.isoformat() if self._last_event_at else None,
            error_count=self._error_count,
        )
