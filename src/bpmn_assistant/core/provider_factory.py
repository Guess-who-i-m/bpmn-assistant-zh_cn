from bpmn_assistant.core.provider_impl import (
    AnthropicProvider,
    LiteLLMProvider,
)

from .enums import OutputMode, Provider
from .llm_provider import LLMProvider
from .provider_impl import AliProvider


class ProviderFactory:
    @staticmethod
    def get_provider(
        provider: Provider, api_key: str, output_mode: OutputMode = OutputMode.JSON
    ) -> LLMProvider:

        if provider in [Provider.OPENAI, Provider.FIREWORKS_AI, Provider.GOOGLE]:
            return LiteLLMProvider(api_key, output_mode)
        elif provider == Provider.ANTHROPIC:
            return AnthropicProvider(api_key, output_mode)
        elif provider == Provider.ALI:
            return AliProvider(api_key, output_mode)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
