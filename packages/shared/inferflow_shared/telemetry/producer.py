"""
Fire-and-forget Redis Streams telemetry producer.
"""

import json
import logging
import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger("inferflow.telemetry")

class TelemetryProducer:
    """
    Asynchronous telemetry producer leveraging Redis Streams.
    Designed for fire-and-forget logging. Telemetry failures MUST NEVER break inference.
    """
    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def emit(self, event: BaseModel, stream_name: str = "llm.inference.events"):
        """
        Emit a normalized event to a Redis Stream asynchronously.
        Catches any exception to ensure inference continues unaffected.
        """
        try:
            # We convert the event to a dict of strings for Redis Streams (XADD format)
            # Alternatively, we could store it under a single key 'payload'
            payload = {"payload": event.model_dump_json()}
            
            await self._redis.xadd(
                name=stream_name,
                fields=payload,
                maxlen=100000,
                approximate=True
            )
        except Exception as e:
            # Logging strictly without raising to avoid breaking chat streams
            logger.error(f"Failed to emit telemetry event {event.__class__.__name__}: {e}")

    async def close(self):
        """Close the redis connection pool."""
        await self._redis.aclose()
