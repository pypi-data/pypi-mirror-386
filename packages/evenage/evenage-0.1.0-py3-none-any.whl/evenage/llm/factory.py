"""
LLM provider factory.
"""

from evenage.llm.base import LLMProvider, LLMConfig
from evenage.llm.ollama import OllamaProvider
from evenage.llm.openai import OpenAIProvider
from evenage.llm.anthropic import AnthropicProvider
from evenage.llm.gemini import GeminiProvider
from evenage.llm.groq import GroqProvider
from evenage.llm.llamacpp import LlamaCppProvider


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Create an LLM provider based on config.
    
    Supported providers:
    - ollama (default, local-first)
    - llamacpp (local)
    - openai
    - anthropic
    - gemini
    - groq
    """
    
    providers = {
        "ollama": OllamaProvider,
        "llamacpp": LlamaCppProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "groq": GroqProvider,
    }
    
    provider_class = providers.get(config.provider.lower())
    if not provider_class:
        raise ValueError(
            f"Unknown LLM provider: {config.provider}. "
            f"Supported: {', '.join(providers.keys())}"
        )
    
    return provider_class(config)
