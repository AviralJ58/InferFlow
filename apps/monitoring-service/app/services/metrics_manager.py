"""
Metrics manager — rolling-window in-memory aggregation.

Uses a bounded deque of timestamped events to compute
real-time metrics without hitting the database.

Design:
  - Each event is appended as a lightweight dict to a deque.
  - On every snapshot() call, stale entries (older than window_seconds)
    are pruned, and metrics are computed from the remaining entries.
  - Active streams are tracked via a set of request_ids that have
    started but not yet completed/failed/cancelled.
  - Recent failures are kept in a separate bounded deque (last 20).
"""

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from inferflow_shared.logging import setup_logging
from app.config import get_settings
from app.models import (
    LatencyMetrics,
    MetricSnapshot,
    ModelStats,
    ProviderStats,
    RecentFailure,
)

settings = get_settings()
logger = setup_logging("metrics-manager")

# Terminal event types that close an active stream
_TERMINAL_EVENTS = {"inference_completed", "inference_failed", "inference_cancelled"}


@dataclass
class _EventRecord:
    """Lightweight record stored in the rolling window."""
    timestamp: float  # time.time()
    event_type: str
    request_id: str
    conversation_id: str
    provider: str
    model: str
    total_latency_ms: int | None = None
    ttft_ms: int | None = None
    total_tokens: int | None = None
    error: str | None = None


class MetricsManager:
    """
    In-memory rolling-window metrics aggregator.

    Thread-safe for use with async background tasks (single event loop).
    """

    def __init__(self, window_seconds: int | None = None):
        self._window = window_seconds or settings.window_seconds
        self._events: deque[_EventRecord] = deque()
        self._active_streams: set[str] = set()
        self._recent_failures: deque[RecentFailure] = deque(maxlen=20)
        self._start_time = time.time()

    def process_event(self, event: dict) -> None:
        """
        Ingest a raw inference event from Redis Streams.

        Classifies the event, updates active streams, and appends
        to the rolling window.
        """
        event_type = event.get("event_type", "unknown")
        request_id = event.get("request_id", "")

        record = _EventRecord(
            timestamp=time.time(),
            event_type=event_type,
            request_id=request_id,
            conversation_id=event.get("conversation_id", ""),
            provider=event.get("provider", "unknown"),
            model=event.get("model", "unknown"),
            total_latency_ms=_safe_int(event.get("total_latency_ms")),
            ttft_ms=_safe_int(event.get("ttft_ms")),
            total_tokens=_safe_int(event.get("total_tokens")),
            error=event.get("error"),
        )

        self._events.append(record)

        # Track active streams
        if event_type == "inference_started":
            self._active_streams.add(request_id)
        elif event_type in _TERMINAL_EVENTS:
            self._active_streams.discard(request_id)

        # Track recent failures
        if event_type == "inference_failed":
            self._recent_failures.append(
                RecentFailure(
                    timestamp=event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    request_id=request_id,
                    conversation_id=event.get("conversation_id", ""),
                    provider=event.get("provider", "unknown"),
                    model=event.get("model", "unknown"),
                    error=event.get("error", "Unknown error"),
                )
            )

        logger.debug(
            f"Event processed | type={event_type} request={request_id[:8]}... "
            f"window_size={len(self._events)} active_streams={len(self._active_streams)}"
        )

    def snapshot(self) -> MetricSnapshot:
        """
        Compute a point-in-time metrics snapshot from the rolling window.

        Prunes stale events first, then aggregates.
        """
        self._prune()

        now = time.time()
        events = list(self._events)

        if not events:
            return MetricSnapshot(
                window_seconds=self._window,
                active_streams=len(self._active_streams),
                recent_failures=list(self._recent_failures),
            )

        # --- Throughput ---
        window_duration = min(now - events[0].timestamp, self._window) if events else self._window
        window_duration = max(window_duration, 1.0)  # avoid division by zero
        total_requests = len(events)
        requests_per_sec = round(total_requests / window_duration, 2)

        # --- Latency ---
        latencies = [e.total_latency_ms for e in events if e.total_latency_ms is not None]
        latency_metrics = _compute_latency(latencies)

        ttfts = [e.ttft_ms for e in events if e.ttft_ms is not None]
        ttft_metrics = _compute_latency(ttfts)

        # --- Tokens ---
        total_tokens = sum(e.total_tokens for e in events if e.total_tokens)
        token_throughput = round(total_tokens / window_duration, 2)

        # --- Error rate ---
        error_count = sum(1 for e in events if e.event_type == "inference_failed")
        # Compute error rate against completed + failed (terminal events)
        terminal_count = sum(1 for e in events if e.event_type in _TERMINAL_EVENTS)
        error_rate = round(error_count / terminal_count, 4) if terminal_count > 0 else 0.0

        # --- Provider distribution ---
        provider_stats = self._compute_provider_stats(events)

        # --- Model distribution ---
        model_stats = self._compute_model_stats(events)

        return MetricSnapshot(
            window_seconds=self._window,
            requests_per_sec=requests_per_sec,
            total_requests=total_requests,
            active_streams=len(self._active_streams),
            latency=latency_metrics,
            ttft=ttft_metrics,
            token_throughput_per_sec=token_throughput,
            total_tokens_in_window=total_tokens,
            error_rate=error_rate,
            error_count=error_count,
            provider_stats=provider_stats,
            model_stats=model_stats,
            recent_failures=list(self._recent_failures),
        )

    def _prune(self) -> None:
        """Remove events older than the rolling window."""
        cutoff = time.time() - self._window
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()

    def _compute_provider_stats(self, events: list[_EventRecord]) -> list[ProviderStats]:
        """Aggregate stats per provider."""
        providers: dict[str, dict] = {}
        for e in events:
            if e.provider not in providers:
                providers[e.provider] = {"count": 0, "latencies": [], "errors": 0}
            providers[e.provider]["count"] += 1
            if e.total_latency_ms is not None:
                providers[e.provider]["latencies"].append(e.total_latency_ms)
            if e.event_type == "inference_failed":
                providers[e.provider]["errors"] += 1

        result = []
        for name, data in providers.items():
            avg_lat = sum(data["latencies"]) / len(data["latencies"]) if data["latencies"] else 0.0
            err_rate = data["errors"] / data["count"] if data["count"] > 0 else 0.0
            result.append(
                ProviderStats(
                    provider=name,
                    request_count=data["count"],
                    avg_latency_ms=round(avg_lat, 2),
                    error_count=data["errors"],
                    error_rate=round(err_rate, 4),
                )
            )
        return sorted(result, key=lambda s: s.request_count, reverse=True)

    def _compute_model_stats(self, events: list[_EventRecord]) -> list[ModelStats]:
        """Aggregate stats per model."""
        models: dict[str, dict] = {}
        for e in events:
            key = e.model
            if key not in models:
                models[key] = {"provider": e.provider, "count": 0, "latencies": []}
            models[key]["count"] += 1
            if e.total_latency_ms is not None:
                models[key]["latencies"].append(e.total_latency_ms)

        result = []
        for name, data in models.items():
            avg_lat = sum(data["latencies"]) / len(data["latencies"]) if data["latencies"] else 0.0
            result.append(
                ModelStats(
                    model=name,
                    provider=data["provider"],
                    request_count=data["count"],
                    avg_latency_ms=round(avg_lat, 2),
                )
            )
        return sorted(result, key=lambda s: s.request_count, reverse=True)


def _compute_latency(values: list[int]) -> LatencyMetrics:
    """Compute latency percentiles from a list of millisecond values."""
    if not values:
        return LatencyMetrics()

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def percentile(p: float) -> float:
        idx = int(p * n)
        idx = min(idx, n - 1)
        return float(sorted_vals[idx])

    return LatencyMetrics(
        avg_ms=round(sum(sorted_vals) / n, 2),
        p50_ms=percentile(0.5),
        p95_ms=percentile(0.95),
        p99_ms=percentile(0.99),
        min_ms=float(sorted_vals[0]),
        max_ms=float(sorted_vals[-1]),
    )


def _safe_int(val) -> int | None:
    """Safely convert a value to int, returning None on failure."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
