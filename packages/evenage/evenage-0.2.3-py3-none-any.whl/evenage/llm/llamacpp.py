"""
llama.cpp provider for local models.
"""

from typing import Optional, Iterator
import requests
import json

from evenage.llm.base import LLMProvider, LLMResponse, LLMConfig


class LlamaCppProvider(LLMProvider):
    """llama.cpp local server provider."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.api_base or "http://localhost:8080"
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using llama.cpp."""
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "prompt": full_prompt,
            "temperature": self.config.temperature,
            "n_predict": self.config.max_tokens,
            "stream": False,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["content"],
                model=self.config.model,
                provider="llamacpp",
                tokens_used=data.get("tokens_predicted", 0) + data.get("tokens_evaluated", 0),
                finish_reason="stop" if data.get("stopped_eos", True) else "length",
                raw_response=data
            )
        except Exception as e:
            raise RuntimeError(f"llama.cpp completion failed: {e}")
    
    def stream_complete(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Stream completion using llama.cpp."""
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "prompt": full_prompt,
            "temperature": self.config.temperature,
            "n_predict": self.config.max_tokens,
            "stream": True,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=self.config.timeout,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    if line.startswith(b"data: "):
                        data = json.loads(line[6:])
                        if "content" in data:
                            yield data["content"]
        except Exception as e:
            raise RuntimeError(f"llama.cpp streaming failed: {e}")
    
    def health_check(self) -> bool:
        """Check if llama.cpp server is available."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
