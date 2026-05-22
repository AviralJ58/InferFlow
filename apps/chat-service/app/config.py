"""
Chat service configuration.

Extends the shared BaseConfig with chat-service-specific settings.
"""

from functools import lru_cache

from inferflow_shared.config import BaseConfig
from pydantic import Field


class ChatServiceSettings(BaseConfig):
    """
    Service-specific settings.
    Inherits app_name, environment, log_level, redis_url, database_url.
    """
    app_name: str = "inferflow-chat-service"

    # LLM Settings
    gemini_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    default_provider: str = Field(default="gemini")
    default_model: str = Field(default="gemini-2.5-flash")

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
