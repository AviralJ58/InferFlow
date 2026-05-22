"""
SSE broadcaster — manages connected SSE clients.

Each connected client gets an asyncio.Queue. The broadcaster's
periodic task pushes MetricSnapshot JSON into all queues.
Disconnected clients are automatically cleaned up.

Why asyncio.Queue per client:
  - Each SSE response generator reads from its own queue.
  - The broadcaster pushes to all queues in a non-blocking loop.
  - No shared mutable state between request handlers.
"""

import asyncio
import json

from inferflow_shared.logging import setup_logging
from app.services.metrics_manager import MetricsManager
from app.config import get_settings

settings = get_settings()
logger = setup_logging("sse-broadcaster")


class SSEBroadcaster:
    """
    Manages SSE client subscriptions and periodic metric broadcasting.
    """

    def __init__(self, metrics_manager: MetricsManager):
        self._metrics = metrics_manager
        self._clients: set[asyncio.Queue] = set()
        self._broadcast_task: asyncio.Task | None = None

    def subscribe(self) -> asyncio.Queue:
        """Register a new SSE client. Returns a queue to read from."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._clients.add(queue)
        logger.info(f"SSE client connected. Total: {len(self._clients)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Remove an SSE client."""
        self._clients.discard(queue)
        logger.info(f"SSE client disconnected. Total: {len(self._clients)}")

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def broadcast(self, data: str) -> None:
        """Push data to all connected client queues."""
        disconnected = []
        for queue in self._clients:
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                # Client is too slow — drop the oldest snapshot
                try:
                    queue.get_nowait()
                    queue.put_nowait(data)
                except Exception:
                    disconnected.append(queue)

        for q in disconnected:
            self._clients.discard(q)

    async def start_periodic_broadcast(self, shutdown_event: asyncio.Event) -> None:
        """
        Background task that periodically snapshots metrics
        and broadcasts to all SSE clients.
        """
        logger.info(
            f"Periodic broadcast started (interval={settings.snapshot_interval_seconds}s)"
        )

        while not shutdown_event.is_set():
            try:
                if self._clients:
                    snapshot = self._metrics.snapshot()
                    data = snapshot.model_dump_json()
                    await self.broadcast(data)

                await asyncio.sleep(settings.snapshot_interval_seconds)

            except asyncio.CancelledError:
                logger.info("Broadcast task cancelled")
                break
            except Exception:
                logger.exception("Error in broadcast loop")
                await asyncio.sleep(1)

        logger.info("Periodic broadcast stopped.")
