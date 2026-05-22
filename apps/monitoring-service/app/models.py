"""
Structured monitoring models/contracts.

Defines the data shapes for all monitoring metrics,
serialized to JSON for SSE broadcasting to dashboard clients.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LatencyMetrics(BaseModel):
    """Latency distribution metrics."""
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0


class ProviderStats(BaseModel):
    """Per-provider aggregated stats within the rolling window."""
    provider: str
    request_count: int = 0
    avg_latency_ms: float = 0.0
    error_count: int = 0
    error_rate: float = 0.0


class ModelStats(BaseModel):
    """Per-model aggregated stats within the rolling window."""
    model: str
    provider: str
    request_count: int = 0
    avg_latency_ms: float = 0.0


class RecentFailure(BaseModel):
    """A recent inference failure for the live feed."""
    timestamp: str
    request_id: str
    conversation_id: str
    provider: str
    model: str
    error: str


class MetricSnapshot(BaseModel):
    """
    Point-in-time snapshot of all system metrics.

    Computed from the rolling window and broadcast via SSE.
    """
    # Timing
    timestamp: str = Field(default_factory=utc_now)
    window_seconds: int = 300

    # Throughput
    requests_per_sec: float = 0.0
    total_requests: int = 0

    # Active streams
    active_streams: int = 0

    # Latency
    latency: LatencyMetrics = Field(default_factory=LatencyMetrics)
    ttft: LatencyMetrics = Field(default_factory=LatencyMetrics)

    # Tokens
    token_throughput_per_sec: float = 0.0
    total_tokens_in_window: int = 0

    # Error rate
    error_rate: float = 0.0
    error_count: int = 0

    # Distributions
    provider_stats: list[ProviderStats] = Field(default_factory=list)
    model_stats: list[ModelStats] = Field(default_factory=list)

    # Recent failures
    recent_failures: list[RecentFailure] = Field(default_factory=list)


class SystemHealth(BaseModel):
    """System health status for the dashboard header."""
    status: str = "healthy"  # healthy | degraded | unhealthy
    uptime_seconds: float = 0.0
    connected_clients: int = 0
    consumer_group: str = ""
    stream_key: str = ""
