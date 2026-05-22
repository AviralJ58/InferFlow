"""
Redis Streams consumer for the monitoring group.

Consumes raw inference events from the same stream as the ingestion
worker, but using an independent consumer group (monitoring-group).
This ensures every event is delivered to both services independently.

Follows the same PEL recovery pattern as the ingestion worker.
Monitoring is best-effort: failed processing does NOT block ACKs.
"""

import asyncio
import json

import redis.asyncio as aioredis

from inferflow_shared.logging import setup_logging
from app.config import get_settings
from app.services.metrics_manager import MetricsManager

settings = get_settings()
logger = setup_logging("monitoring-consumer")


class MonitoringConsumer:
    """
    Redis Streams consumer for the monitoring pipeline.

    Reads events from llm.inference.events using consumer group
    monitoring-group, and feeds them to the MetricsManager.
    """

    def __init__(self, metrics_manager: MetricsManager):
        self._metrics = metrics_manager
        self._redis: aioredis.Redis | None = None

    async def _ensure_group(self) -> None:
        """Create the consumer group if it doesn't already exist."""
        try:
            await self._redis.xgroup_create(
                name=settings.stream_key,
                groupname=settings.consumer_group,
                id="0",
                mkstream=True,
            )
            logger.info(
                f"Created consumer group '{settings.consumer_group}' "
                f"on stream '{settings.stream_key}'"
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug("Consumer group already exists, skipping creation.")
            else:
                raise

    async def _process_messages(self, messages) -> None:
        """Parse and feed messages to the metrics manager."""
        for stream_name, entries in messages:
            for msg_id, fields in entries:
                payload = fields.get("payload")
                if not payload:
                    # Empty payload — ACK and skip
                    await self._redis.xack(
                        settings.stream_key, settings.consumer_group, msg_id
                    )
                    continue

                try:
                    event = json.loads(payload)
                    self._metrics.process_event(event)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in message {msg_id}")
                except Exception:
                    logger.exception(f"Error processing event {msg_id}")

                # Always ACK — monitoring is best-effort, never blocks
                await self._redis.xack(
                    settings.stream_key, settings.consumer_group, msg_id
                )

    async def start(self, shutdown_event: asyncio.Event) -> None:
        """
        Main consumer loop.

        Phase 1: Recover pending messages (PEL).
        Phase 2: Listen for new messages.
        """
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await self._ensure_group()

        logger.info(
            f"Consumer started | group={settings.consumer_group} "
            f"name={settings.consumer_name} stream={settings.stream_key}"
        )

        # Phase 1: PEL recovery
        logger.info("Recovering pending messages from PEL...")
        while not shutdown_event.is_set():
            try:
                messages = await self._redis.xreadgroup(
                    groupname=settings.consumer_group,
                    consumername=settings.consumer_name,
                    streams={settings.stream_key: "0"},
                    count=settings.batch_size,
                )

                if not messages or not messages[0][1]:
                    logger.info("PEL recovery complete.")
                    break

                await self._process_messages(messages)
            except Exception:
                logger.exception("Error in PEL recovery")
                break

        # Phase 2: Live consumption
        logger.info("Listening for new events...")
        while not shutdown_event.is_set():
            try:
                messages = await self._redis.xreadgroup(
                    groupname=settings.consumer_group,
                    consumername=settings.consumer_name,
                    streams={settings.stream_key: ">"},
                    count=settings.batch_size,
                    block=settings.block_ms,
                )

                if not messages:
                    continue

                await self._process_messages(messages)

            except asyncio.CancelledError:
                logger.info("Consumer loop cancelled")
                break
            except Exception:
                logger.exception("Error in consumer loop, retrying in 5s...")
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Clean up resources."""
        logger.info("Consumer stopping...")
        if self._redis:
            await self._redis.aclose()
