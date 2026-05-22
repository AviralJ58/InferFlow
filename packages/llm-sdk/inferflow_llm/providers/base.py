"""
Base interface for LLM providers.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from inferflow_llm.models import Message, ProviderConfig, StreamChunk


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Ensures that any implementation supports the normalized contracts.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[Message],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a chat completion response progressively.
        Yields normalized StreamChunk objects.
        """
        pass

    # Future: def generate_chat(...)
