"""
LLM Provider base interface.

Future: each provider (OpenAI, Anthropic, etc.) will implement
this abstract interface, enabling hot-swappable model routing.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel


class CompletionRequest(BaseModel):
    """Normalized request to any LLM provider."""

    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False


class CompletionResponse(BaseModel):
    """Normalized response from any LLM provider."""

    content: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Each provider implementation must support both synchronous
    and streaming completions.
    """

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate a completion for the given request."""
        ...

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream completion tokens for the given request."""
        ...
