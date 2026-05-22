"""
Chat service — orchestrates inference and streaming.
"""

import asyncio
import json
from collections.abc import AsyncGenerator

from inferflow_llm.factory import ProviderFactory
from inferflow_llm.models import Message as SDKMessage
from inferflow_llm.models import ProviderConfig
from inferflow_llm.providers.base import BaseLLMProvider
from inferflow_shared.logging import setup_logging

from app.config import get_settings
from app.domain.models import Message
from app.repositories.base import ConversationRepository
from app.schemas.chat import StreamChatRequest
from app.streaming.manager import stream_manager

logger = setup_logging("chat-service")
settings = get_settings()

from app.api.models import SUPPORTED_MODELS

class ChatService:
    def __init__(self, repository: ConversationRepository):
        self._repository = repository

    def _get_provider(self, model_id: str | None) -> BaseLLMProvider:
        """Resolve the provider from the requested model."""
        target_model = next((m for m in SUPPORTED_MODELS if m["id"] == model_id), None)
        if not target_model:
            # Fallback to default
            provider_name = settings.default_provider
        else:
            provider_name = target_model["provider"]

        # Get API key
        if provider_name == "openai":
            api_key = settings.openai_api_key
        else:
            api_key = settings.gemini_api_key

        config = ProviderConfig(
            api_key=api_key,
            default_model=model_id or settings.default_model
        )
        return ProviderFactory.create(provider_name, config)

    async def stream_message(self, request: StreamChatRequest) -> AsyncGenerator[dict, None]:
        """
        Process a user message and stream the assistant's response.
        """
        # Fetch conversation
        conversation = await self._repository.get_by_id(request.conversation_id)
        if not conversation:
            yield {"event": "error", "data": json.dumps({"error": "Conversation not found"})}
            return

        # Add user message
        user_message = Message(role="user", content=request.message)
        await self._repository.add_message(conversation.id, user_message)

        # Prepare assistant message placeholder
        assistant_message = Message(role="assistant", content="")
        await self._repository.add_message(conversation.id, assistant_message)

        # Convert app domain Messages to SDK Messages for the provider
        sdk_messages = [
            SDKMessage(role=m.role, content=m.content)
            for m in conversation.messages
            if m.role in ["user", "assistant", "system"] and m.content
        ]

        # Register active task for cancellation
        current_task = asyncio.current_task()
        if current_task:
            stream_manager.register(conversation.id, current_task)

        try:
            # Instantiate provider per request
            provider = self._get_provider(request.model)
            # Stream from provider
            stream = provider.stream_chat(sdk_messages, request.model)

            async for chunk in stream:
                # Append token to the assistant message
                assistant_message.content += chunk.content

                # Create stream event
                event_data = {
                    "message_id": assistant_message.id,
                    "conversation_id": conversation.id,
                    "content": chunk.content,
                    "is_done": chunk.is_done
                }
                yield {
                    "event": "token" if not chunk.is_done else "done",
                    "data": json.dumps(event_data)
                }

        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for conversation {conversation.id}")
            # Ensure the partial message is saved before the task terminates
            await self._repository.update(conversation)
            raise
        except Exception as e:
            logger.error(f"Provider stream error: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
        finally:
            # Update the final message in repository
            await self._repository.update(conversation)

            # Future: Publish InferenceEvent to Redis Streams
            # await self._publish_inference_event(...)
            logger.info(f"Finished streaming response for conversation {conversation.id}")

    def cancel_stream(self, conversation_id: str) -> bool:
        """Cancel an active stream for a conversation."""
        return stream_manager.cancel(conversation_id)
