"""
Chat service configuration.

Extends the shared BaseConfig with chat-service-specific settings.
"""

from functools import lru_cache

from inferflow_shared.config import BaseConfig


class ChatServiceSettings(BaseConfig):
    """Chat service specific configuration."""

    # Service
    chat_service_host: str = "0.0.0.0"
    chat_service_port: int = 8000

    # LLM (future)
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # Redis Streams (future)
    inference_stream_key: str = "inferflow:inference_events"


@lru_cache
def get_settings() -> ChatServiceSettings:
    """Return cached settings instance."""
    return ChatServiceSettings()
