"""
Chat service — core business logic layer.

Orchestrates the flow:
  1. Receive message from router
  2. Load conversation context (future: from PostgreSQL)
  3. Call LLM provider (future: via llm-sdk)
  4. Publish inference event to Redis Streams (fire-and-forget)
  5. Return response / stream tokens via SSE

Design decisions:
  - Inference does NOT wait for persistence. The response is streamed
    back immediately, and a fire-and-forget event is published to Redis
    Streams for async ingestion by downstream workers.
  - This keeps the inference path fast and decoupled from storage.
"""

import uuid

from app.schemas import ChatRequest, ChatResponse


class ChatService:
    """
    Handles chat message processing and LLM orchestration.

    Future dependencies (injected via lifespan):
      - LLM provider client
      - Redis client (for event publishing)
      - Database session factory (for conversation context)
    """

    async def handle_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message and return a response.

        Current: returns a placeholder response.
        Future: calls LLM, streams tokens, publishes events.
        """
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # TODO: Load conversation history from DB
        # TODO: Call LLM provider via llm-sdk
        # TODO: Publish InferenceEvent to Redis Streams

        return ChatResponse(
            message="This is a placeholder response. LLM integration coming soon.",
            conversation_id=conversation_id,
            model="placeholder",
        )

    async def stream_message(self, request: ChatRequest):
        """
        Stream LLM tokens as an async generator (for SSE).

        Future: yield individual tokens from the LLM provider.
        """
        # TODO: Implement streaming via llm-sdk
        yield "Streaming not yet implemented."

    async def _publish_inference_event(self, event: dict) -> None:
        """
        Publish an inference event to Redis Streams (fire-and-forget).

        This is called after inference completes. It does NOT block
        the response to the user. Downstream consumers pick up the
        event asynchronously.

        Future: use Redis XADD to publish to the inference stream.
        """
        # TODO: Implement Redis Streams publishing
        pass
