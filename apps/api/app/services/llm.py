"""
Provider-agnostic LLM client.
Supports: OpenAI-compatible APIs, Ollama (local free), Grok, Anthropic-style.
Recommended free/strong creative models 2026 (vylepsovak research):
- Local: Llama 3.3 70B, Qwen3-32B, Mistral Small, GLM family via Ollama
- API: DeepSeek-V3, Qwen3, Kimi K3 (long continuity)
"""
import os
import httpx
from typing import Optional


class LLMClient:
    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.timeout = 120.0

    async def generate(self, system: str, user: str, temperature: float = 0.85, max_tokens: int = 4096) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


llm_client = LLMClient()
