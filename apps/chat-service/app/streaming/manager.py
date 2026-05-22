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
    Manages active streaming tasks for cancellation.
    """
    def __init__(self):
        # Maps conversation_id -> asyncio.Task
        self._active_tasks: dict[str, asyncio.Task] = {}

    def register(self, conversation_id: str, task: asyncio.Task) -> None:
        """Register an active streaming task."""
        self._active_tasks[conversation_id] = task
        logger.debug(f"Registered stream task for conversation {conversation_id}")

        # Auto-remove when done
        task.add_done_callback(lambda t: self.unregister(conversation_id))

    def unregister(self, conversation_id: str) -> None:
        """Remove a task from the registry."""
        if conversation_id in self._active_tasks:
            del self._active_tasks[conversation_id]
            logger.debug(f"Unregistered stream task for conversation {conversation_id}")

    def cancel(self, conversation_id: str) -> bool:
        """Cancel an active stream."""
        task = self._active_tasks.get(conversation_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled stream task for conversation {conversation_id}")
            return True
        return False

# Global instance for now
stream_manager = StreamManager()
