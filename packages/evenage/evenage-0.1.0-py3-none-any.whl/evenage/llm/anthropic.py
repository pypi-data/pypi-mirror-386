"""
Anthropic provider.
"""

from typing import Optional, Iterator
from anthropic import Anthropic

from evenage.llm.base import LLMProvider, LLMResponse, LLMConfig


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = Anthropic(
            api_key=config.api_key,
            base_url=config.api_base,
            timeout=config.timeout
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using Anthropic."""
        
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                **self.config.extra
            )
            
            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                provider="anthropic",
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                raw_response={"id": response.id, "usage": response.usage.__dict__}
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic completion failed: {e}")
    
    def stream_complete(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Stream completion using Anthropic."""
        
        try:
            with self.client.messages.stream(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                **self.config.extra
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Anthropic streaming failed: {e}")
    
    def health_check(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            # Simple test with minimal tokens
            self.client.messages.create(
                model=self.config.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except:
            return False
