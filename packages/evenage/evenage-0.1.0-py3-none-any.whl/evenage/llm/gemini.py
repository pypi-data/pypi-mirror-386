"""
Google Gemini provider.
"""

from typing import Optional, Iterator
import google.generativeai as genai

from evenage.llm.base import LLMProvider, LLMResponse, LLMConfig


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        
        self.model = genai.GenerativeModel(
            model_name=config.model,
            generation_config={
                "temperature": config.temperature,
                "max_output_tokens": config.max_tokens,
                **config.extra
            }
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using Gemini."""
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self.model.generate_content(full_prompt)
            
            # Extract token counts
            tokens_used = 0
            if hasattr(response, "usage_metadata"):
                tokens_used = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )
            
            return LLMResponse(
                content=response.text,
                model=self.config.model,
                provider="gemini",
                tokens_used=tokens_used,
                finish_reason=str(response.candidates[0].finish_reason) if response.candidates else "stop",
                raw_response={"candidates": len(response.candidates)}
            )
        except Exception as e:
            raise RuntimeError(f"Gemini completion failed: {e}")
    
    def stream_complete(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Stream completion using Gemini."""
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self.model.generate_content(full_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise RuntimeError(f"Gemini streaming failed: {e}")
    
    def health_check(self) -> bool:
        """Check if Gemini API is available."""
        try:
            self.model.generate_content("test")
            return True
        except:
            return False
