"""
OpenAI API provider implementation.
"""

import asyncio
from typing import AsyncGenerator, List
from openai import AsyncOpenAI
from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError

from inferflow_llm.providers.base import BaseLLMProvider
from inferflow_llm.models import Message, StreamChunk, ProviderConfig
from inferflow_llm.exceptions import (
    ProviderConnectionError, 
    ProviderRateLimitError, 
    ProviderAuthenticationError,
    ProviderStreamingError
)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=self.config.api_key)

    async def stream_chat(
        self, 
        messages: List[Message], 
        model: str | None = None
    ) -> AsyncGenerator[StreamChunk, None]:
        
        target_model = model or self.config.default_model
        
        # Convert internal messages to OpenAI format
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        try:
            stream = await self.client.chat.completions.create(
                model=target_model,
                messages=openai_messages,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    content = delta.content
                    finish_reason = chunk.choices[0].finish_reason
                    
                    if content is not None:
                        yield StreamChunk(
                            content=content,
                            is_done=False
                        )
                    
                    if finish_reason is not None:
                        yield StreamChunk(
                            content="",
                            is_done=True,
                            finish_reason=finish_reason
                        )

        except APIConnectionError as e:
            raise ProviderConnectionError(f"OpenAI connection error: {e}") from e
        except RateLimitError as e:
            raise ProviderRateLimitError(f"OpenAI Rate Limit Exceeded: {e}") from e
        except AuthenticationError as e:
            raise ProviderAuthenticationError(f"OpenAI Auth Error: {e}") from e
        except APIError as e:
            raise ProviderStreamingError(f"OpenAI API Error: {e}") from e
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise ProviderStreamingError(f"Unexpected streaming error: {e}") from e
