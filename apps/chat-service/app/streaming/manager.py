"""
Streaming manager for handling active SSE streams.

Maintains a registry of active streams to allow future features
such as cancellation and timeout handling.
"""

import asyncio

from inferflow_shared.logging import setup_logging

logger = setup_logging("streaming-manager")

class StreamManager:
    """
    Manages active streaming tasks.
    
    Future: Use this to cancel tasks if the client disconnects or requests cancellation.
    """
    def __init__(self):
        # Maps message_id -> asyncio.Task
        self._active_tasks: dict[str, asyncio.Task] = {}

    def register(self, message_id: str, task: asyncio.Task) -> None:
        """Register an active streaming task."""
        self._active_tasks[message_id] = task
        logger.debug(f"Registered stream task for message {message_id}")

        # Auto-remove when done
        task.add_done_callback(lambda t: self.unregister(message_id))

    def unregister(self, message_id: str) -> None:
        """Remove a task from the registry."""
        if message_id in self._active_tasks:
            del self._active_tasks[message_id]
            logger.debug(f"Unregistered stream task for message {message_id}")

    def cancel(self, message_id: str) -> bool:
        """Cancel an active stream."""
        task = self._active_tasks.get(message_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled stream task for message {message_id}")
            return True
        return False

# Global instance for now
stream_manager = StreamManager()
