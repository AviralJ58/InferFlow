"""
Chat service — orchestrates inference and streaming.
"""

import asyncio
import json
from collections.abc import AsyncGenerator

from inferflow_shared.logging import setup_logging

from app.domain.models import Message
from app.repositories.base import ConversationRepository
from app.schemas.chat import StreamChatRequest

logger = setup_logging("chat-service")


class ChatService:
    def __init__(self, repository: ConversationRepository):
        self._repository = repository

    async def stream_message(self, request: StreamChatRequest) -> AsyncGenerator[dict, None]:
        """
        Process a user message and stream the assistant's response.
        
        Yields dictionaries formatted for sse-starlette.
        """
        # 1. Fetch conversation
        conversation = await self._repository.get_by_id(request.conversation_id)
        if not conversation:
            yield {"event": "error", "data": json.dumps({"error": "Conversation not found"})}
            return

        # 2. Add user message
        user_message = Message(role="user", content=request.message)
        await self._repository.add_message(conversation.id, user_message)

        # 3. Prepare assistant message placeholder
        assistant_message = Message(role="assistant", content="")
        await self._repository.add_message(conversation.id, assistant_message)

        # 4. Simulate LLM streaming
        # Future: Call llm_sdk provider here and iterate over its token stream
        mock_response = f"This is a simulated streaming response to: '{request.message}'. " \
                        f"In the future, this will be wired to a real LLM via the llm-sdk."

        tokens = mock_response.split(" ")

        for i, token in enumerate(tokens):
            await asyncio.sleep(0.05)  # Simulate network latency

            # Append token to the assistant message
            chunk = token + (" " if i < len(tokens) - 1 else "")
            assistant_message.content += chunk

            # Create stream event
            event_data = {
                "message_id": assistant_message.id,
                "conversation_id": conversation.id,
                "content": chunk,
                "is_done": False
            }
            yield {"event": "token", "data": json.dumps(event_data)}

        # Update the final message in repository (just touches updated_at)
        await self._repository.update(conversation)

        # 5. Send done event
        final_event_data = {
            "message_id": assistant_message.id,
            "conversation_id": conversation.id,
            "content": "",
            "is_done": True
        }
        yield {"event": "done", "data": json.dumps(final_event_data)}

        # 6. Future: Publish InferenceEvent to Redis Streams
        # await self._publish_inference_event(...)
        logger.info(f"Finished streaming response for conversation {conversation.id}")
