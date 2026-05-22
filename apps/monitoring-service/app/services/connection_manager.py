"""
WebSocket connection manager.

Manages connected WebSocket clients and provides
broadcast capabilities for event fanout.
"""

from fastapi import WebSocket

from inferflow_shared.logging import setup_logging

logger = setup_logging("connection-manager")


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Provides methods to connect, disconnect, and broadcast
    messages to all connected clients.

    Future enhancements:
      - Per-client subscription filters
      - Connection heartbeat/keepalive
      - Client authentication
      - Rate limiting per client
    """

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        self._connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        """
        Send a message to all connected clients.

        Disconnected clients are automatically cleaned up.
        """
        disconnected = []
        for connection in self._connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self._connections.remove(conn)

    @property
    def active_count(self) -> int:
        """Return the number of active connections."""
        return len(self._connections)
