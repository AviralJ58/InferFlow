"""
Redis Streams consumer for inference events.

Uses XREADGROUP for consumer group semantics:
  - Horizontal scaling: multiple workers share the workload
  - At-least-once delivery: unACK'd messages are redelivered
  - Independent consumption: each group tracks its own offset

ACK semantics:
  - Events are ACK'd ONLY after successful persistence
  - Failed DB writes leave the message unACK'd for redelivery
  - Invalid events are routed to a dead-letter stream and ACK'd
"""

import asyncio
import json

import redis.asyncio as aioredis

from inferflow_shared.logging import setup_logging
from worker.config import get_settings
from worker.processor import EventProcessor

settings = get_settings()
logger = setup_logging("ingestion-consumer", level=settings.log_level)


class InferenceEventConsumer:
    """
    Redis Streams consumer for inference events.

    Uses XREADGROUP for consumer group semantics.
    """

    def __init__(self):
        self.processor = EventProcessor()
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
        """Helper to process a batch of messages."""
        for stream_name, entries in messages:
            for msg_id, fields in entries:
                payload = fields.get("payload")
                if not payload:
                    logger.warning(f"Empty payload in message {msg_id}, ACK'ing")
                    await self._redis.xack(
                        settings.stream_key, settings.consumer_group, msg_id
                    )
                    continue

                success = await self.processor.process(payload)

                if success:
                    # ACK only on successful persistence
                    await self._redis.xack(
                        settings.stream_key, settings.consumer_group, msg_id
                    )
                elif success is None:
                    # Invalid event — route to dead-letter and ACK
                    await self._redis.xadd(
                        settings.invalid_stream_key,
                        {"payload": payload, "original_id": msg_id},
                    )
                    await self._redis.xack(
                        settings.stream_key, settings.consumer_group, msg_id
                    )
                    logger.warning(
                        f"Invalid event routed to {settings.invalid_stream_key} | id={msg_id}"
                    )
                else:
                    # DB write failed — do NOT ACK, Redis will redeliver
                    logger.error(f"Processing failed, will retry | id={msg_id}")

    async def start(self, shutdown_event: asyncio.Event) -> None:
        """
        Main consumer loop.

        Reads from Redis Streams using consumer group, processes
        events, and acknowledges them.
        """
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await self._ensure_group()

        logger.info(
            f"Consumer started | group={settings.consumer_group} "
            f"name={settings.consumer_name} stream={settings.stream_key}"
        )

        # First, recover any pending messages (PEL) that were read but not ACK'd
        # '0' means read from the beginning of the Pending Entries List for this consumer
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

        logger.info("Listening for new messages...")
        while not shutdown_event.is_set():
            try:
                # XREADGROUP: read new messages for this consumer
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
