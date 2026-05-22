"""
Gemini API provider implementation using google-genai.
"""

import asyncio
from collections.abc import AsyncGenerator

from google import genai
from google.genai.errors import APIError

from inferflow_llm.exceptions import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderStreamingError,
)
from inferflow_llm.models import Message, ProviderConfig, StreamChunk
from inferflow_llm.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=self.config.api_key)

    async def stream_chat(
        self,
        messages: list[Message],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:

        target_model = model or self.config.default_model

        # Convert internal messages to Gemini format.
        # Note: google-genai accepts dicts or Content objects
        # For simple mapping:
        gemini_contents = []
        for msg in messages:
            # Gemini primarily uses 'user' and 'model'
            role = "model" if msg.role == "assistant" else "user"
            gemini_contents.append({"role": role, "parts": [{"text": msg.content}]})

        try:
            # Yielding loop wrapper for timeout handling
            async def _generate():
                response = await self.client.aio.models.generate_content_stream(
                    model=target_model,
                    contents=gemini_contents
                )
                async for chunk in response:
                    yield chunk

            # Stream with asyncio.timeout
            # (Note: self.config.timeout_ms applies to total stream life, but often we want per-chunk timeout.
            # We'll use total timeout for simplicity, or omit if long running)
            last_usage = None
            async for raw_chunk in _generate():
                content = raw_chunk.text
                if content:
                    yield StreamChunk(
                        content=content,
                        is_done=False
                    )
                # Gemini attaches usage_metadata on some/last chunks
                if hasattr(raw_chunk, 'usage_metadata') and raw_chunk.usage_metadata:
                    um = raw_chunk.usage_metadata
                    last_usage = {
                        "prompt_tokens": getattr(um, 'prompt_token_count', None),
                        "completion_tokens": getattr(um, 'candidates_token_count', None),
                        "total_tokens": getattr(um, 'total_token_count', None),
                    }

            # Signal stream completion
            yield StreamChunk(
                content="",
                is_done=True,
                finish_reason="stop",
                token_usage=last_usage
            )

        except TimeoutError as e:
            raise ProviderConnectionError(f"Gemini streaming timed out: {e}") from e
        except asyncio.CancelledError:
            # Task cancellation from the app
            raise
        except APIError as e:
            if e.code == 401 or e.code == 403:
                raise ProviderAuthenticationError(f"Gemini Auth Error: {e.message}") from e
            elif e.code == 429:
                raise ProviderRateLimitError(f"Gemini Rate Limit Exceeded: {e.message}") from e
            else:
                raise ProviderStreamingError(f"Gemini API Error: {e.message}") from e
        except Exception as e:
            raise ProviderStreamingError(f"Unexpected streaming error: {e}") from e
