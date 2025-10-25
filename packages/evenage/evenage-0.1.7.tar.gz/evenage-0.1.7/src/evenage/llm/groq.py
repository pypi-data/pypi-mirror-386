"""
Groq provider.
"""

from typing import Optional, Iterator
from groq import Groq

from evenage.llm.base import LLMProvider, LLMResponse, LLMConfig


class GroqProvider(LLMProvider):
    """Groq fast inference provider."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = Groq(
            api_key=config.api_key,
            timeout=config.timeout
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using Groq."""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.extra
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                provider="groq",
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response.model_dump()
            )
        except Exception as e:
            raise RuntimeError(f"Groq completion failed: {e}")
    
    def stream_complete(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Stream completion using Groq."""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                **self.config.extra
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"Groq streaming failed: {e}")
    
    def health_check(self) -> bool:
        """Check if Groq API is available."""
        try:
            self.client.models.list()
            return True
        except:
            return False
