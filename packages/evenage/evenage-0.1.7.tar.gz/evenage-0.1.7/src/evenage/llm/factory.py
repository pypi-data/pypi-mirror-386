"""
LLM provider factory with lazy imports to avoid optional dependency issues.

This ensures that providers like Anthropic, Gemini, Groq, and OpenAI are only
imported when explicitly selected, so basic commands (e.g., `evenage init`)
don't require installing their SDKs.
"""

from importlib import import_module
from typing import Callable, Type

from evenage.llm.base import LLMProvider, LLMConfig


def _load_provider(module_path: str, class_name: str) -> Type[LLMProvider]:
    """Dynamically import and return the provider class.

    Raises a clear error if the underlying SDK isn't installed.
    """
    try:
        module = import_module(module_path)
        return getattr(module, class_name)
    except ModuleNotFoundError as e:
        missing = e.name or module_path
        raise ImportError(
            f"Optional dependency for provider is missing: {missing}.\n"
            f"Install the required package or use a different provider."
        ) from e
    except Exception as e:
        raise ImportError(
            f"Failed to load provider {class_name} from {module_path}: {e}"
        ) from e


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Create an LLM provider based on config.

    Supported providers:
    - ollama (default, local-first)
    - llamacpp (local)
    - openai (requires `openai`)
    - anthropic (requires `anthropic`)
    - gemini (requires `google-generativeai`)
    - groq (requires `groq`)
    """
    name = (config.provider or "ollama").lower()

    # Map provider name to (module_path, class_name)
    registry: dict[str, tuple[str, str]] = {
        "ollama": ("evenage.llm.ollama", "OllamaProvider"),
        "llamacpp": ("evenage.llm.llamacpp", "LlamaCppProvider"),
        "openai": ("evenage.llm.openai", "OpenAIProvider"),
        "anthropic": ("evenage.llm.anthropic", "AnthropicProvider"),
        "gemini": ("evenage.llm.gemini", "GeminiProvider"),
        "groq": ("evenage.llm.groq", "GroqProvider"),
    }

    if name not in registry:
        raise ValueError(
            f"Unknown LLM provider: {config.provider}. Supported: {', '.join(sorted(registry.keys()))}"
        )

    module_path, class_name = registry[name]
    provider_cls = _load_provider(module_path, class_name)
    return provider_cls(config)
