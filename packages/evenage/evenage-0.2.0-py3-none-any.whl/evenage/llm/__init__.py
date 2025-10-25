"""
LLM integration layer for EvenAge.
Supports multiple providers with local-first defaults.
"""

from evenage.llm.base import LLMProvider, LLMResponse, LLMConfig
from evenage.llm.factory import create_llm_provider

__all__ = ["LLMProvider", "LLMResponse", "LLMConfig", "create_llm_provider"]
