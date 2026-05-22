"""
InferFlow Ingestion Worker — entry point.

This is a standalone async worker that:
  1. Connects to Redis Streams as a consumer group member
  2. Reads inference events published by the chat service
  3. Persists them to PostgreSQL (conversations, messages, inference_logs)

Design decisions:
  - Runs as its own process (not inside FastAPI) because it's a
    long-running consumer loop, not a request/response service.
  - Uses Redis consumer groups for horizontal scaling: multiple
    workers can share the load without duplicating work.
  - Fire-and-forget from the chat service's perspective: inference
    latency is never blocked by persistence.

Usage:
  uv run python -m worker.main
"""

import asyncio
import signal

from inferflow_shared.logging import setup_logging
from worker.config import get_settings
from worker.consumer import InferenceEventConsumer

settings = get_settings()
logger = setup_logging("ingestion-worker", level=settings.log_level)


async def main():
    """Start the ingestion worker."""
    logger.info("Ingestion worker starting...")

    consumer = InferenceEventConsumer()
    shutdown_event = asyncio.Event()

    # Graceful shutdown on SIGTERM/SIGINT
    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        await consumer.start(shutdown_event)
    except Exception:
        logger.exception("Ingestion worker encountered a fatal error")
    finally:
        await consumer.stop()
        logger.info("Ingestion worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
