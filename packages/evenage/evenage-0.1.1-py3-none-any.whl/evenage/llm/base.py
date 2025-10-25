"""
Base LLM provider interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    
    provider: str = "ollama"  # Default to local Ollama
    model: str = "llama2"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    extra: Dict[str, Any] = {}


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    
    content: str
    model: str
    provider: str
    tokens_used: int
    finish_reason: str
    raw_response: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a completion."""
        pass
    
    @abstractmethod
    def stream_complete(self, prompt: str, system_prompt: Optional[str] = None):
        """Generate a streaming completion."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is available."""
        pass
