"""
Ollama provider - Local-first default.
"""

import requests
from typing import Optional, Iterator
import json

from evenage.llm.base import LLMProvider, LLMResponse, LLMConfig


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.api_base or "http://localhost:11434"
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate completion using Ollama."""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["message"]["content"],
                model=self.config.model,
                provider="ollama",
                tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                finish_reason=data.get("done_reason", "stop"),
                raw_response=data
            )
        except Exception as e:
            raise RuntimeError(f"Ollama completion failed: {e}")
    
    def stream_complete(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Stream completion using Ollama."""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data:
                        yield data["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Ollama streaming failed: {e}")
    
    def health_check(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
