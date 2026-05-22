"""
Telemetry wrapper for LLM providers.
"""

import asyncio
import time
import uuid
from typing import AsyncGenerator

from inferflow_llm.models import Message, StreamChunk
from inferflow_llm.providers.base import BaseLLMProvider
from inferflow_shared.telemetry.events import (
    InferenceStartedEvent,
    InferenceCompletedEvent,
    InferenceFailedEvent,
    InferenceCancelledEvent
)
from inferflow_shared.telemetry.producer import TelemetryProducer


class TelemetryWrapper(BaseLLMProvider):
    def __init__(self, inner_provider: BaseLLMProvider, producer: TelemetryProducer):
        self.inner_provider = inner_provider
        self.producer = producer
        self.config = inner_provider.config

    async def stream_chat(
        self,
        messages: list[Message],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        
        request_id = str(uuid.uuid4())
        conversation_id = kwargs.get("conversation_id", "unknown")
        
        provider_name = self.inner_provider.__class__.__name__.replace("Provider", "").lower()
        target_model = model or self.config.default_model

        start_time = time.perf_counter()
        first_token_time = None

        # Emit Started Event
        await self.producer.emit(
            InferenceStartedEvent(
                request_id=request_id,
                conversation_id=conversation_id,
                provider=provider_name,
                model=target_model
            )
        )

        try:
            stream = self.inner_provider.stream_chat(messages, model, **kwargs)
            async for chunk in stream:
                if first_token_time is None and chunk.content:
                    first_token_time = time.perf_counter()
                
                # Append request_id to metadata if it's the final chunk
                if chunk.is_done:
                    total_time = time.perf_counter() - start_time
                    ttft = (first_token_time - start_time) if first_token_time else total_time
                    
                    # Extract token usage from the provider's final chunk
                    usage = chunk.token_usage or {}
                    
                    chunk.metadata = {
                        "request_id": request_id,
                        "ttft_ms": int(ttft * 1000),
                        "total_latency_ms": int(total_time * 1000),
                        "provider": provider_name,
                        "model": target_model,
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    }
                    
                    await self.producer.emit(
                        InferenceCompletedEvent(
                            request_id=request_id,
                            conversation_id=conversation_id,
                            provider=provider_name,
                            model=target_model,
                            ttft_ms=int(ttft * 1000),
                            total_latency_ms=int(total_time * 1000),
                            prompt_tokens=usage.get("prompt_tokens"),
                            completion_tokens=usage.get("completion_tokens"),
                            total_tokens=usage.get("total_tokens"),
                        )
                    )
                
                yield chunk

        except asyncio.CancelledError:
            total_time = time.perf_counter() - start_time
            ttft = (first_token_time - start_time) if first_token_time else None
            await self.producer.emit(
                InferenceCancelledEvent(
                    request_id=request_id,
                    conversation_id=conversation_id,
                    provider=provider_name,
                    model=target_model,
                    ttft_ms=int(ttft * 1000) if ttft else None,
                    total_latency_ms=int(total_time * 1000)
                )
            )
            raise
        except Exception as e:
            total_time = time.perf_counter() - start_time
            ttft = (first_token_time - start_time) if first_token_time else None
            await self.producer.emit(
                InferenceFailedEvent(
                    request_id=request_id,
                    conversation_id=conversation_id,
                    provider=provider_name,
                    model=target_model,
                    ttft_ms=int(ttft * 1000) if ttft else None,
                    total_latency_ms=int(total_time * 1000),
                    error=str(e)
                )
            )
            raise
