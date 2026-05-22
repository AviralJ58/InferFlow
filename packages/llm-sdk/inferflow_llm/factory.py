"""
Factory for creating and resolving provider instances.
"""

from inferflow_llm.models import ProviderConfig
from inferflow_llm.providers.base import BaseLLMProvider
from inferflow_llm.providers.gemini_provider import GeminiProvider
from inferflow_llm.providers.openai_provider import OpenAIProvider


class ProviderFactory:
    @staticmethod
    def create(provider_name: str, config: ProviderConfig) -> BaseLLMProvider:
        name = provider_name.lower().strip()

        if name == "gemini":
            return GeminiProvider(config)
        elif name == "openai":
            return OpenAIProvider(config)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")
