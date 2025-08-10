from __future__ import annotations

"""
Anthropic model implementation.
"""

import json
import os
from typing import Any, Dict, List, Optional

from .base_model import BaseModel


class AnthropicModel(BaseModel):
    """
    Anthropic model implementation using Claude API.

    Supports Claude-3 and other Anthropic models.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anthropic model.

        Args:
            config: Configuration dictionary with:
                - api_key: Anthropic API key
                - model: Model name (e.g., claude-3-sonnet-20240229)
        """
        super().__init__(config)
        self.api_key = (config or {}).get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = (config or {}).get("model", "claude-3-5-sonnet-20241022")
        self._client = None

    async def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic  # type: ignore

            if not self.api_key:
                self.logger.warning("ANTHROPIC_API_KEY not set; returning stub client")
                self._client = object()
                return self._client
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            return self._client
        except Exception as e:
            self.logger.warning(f"Anthropic client unavailable: {e}")
            self._client = object()
            return self._client

    async def initialize(self) -> bool:
        await self._get_client()
        self.is_initialized = True
        return True

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Generate a response using Anthropic API or return a stub in restricted envs."""
        if not self.is_initialized:
            await self.initialize()

        client = await self._get_client()
        if not hasattr(client, "messages"):
            return "[anthropic-mock] " + (prompt[:120] if prompt else "")

        try:
            messages = []
            if system_prompt:
                # Claude expects user content; include system as preface
                messages.append({"role": "user", "content": f"System: {system_prompt}\n\nUser: {prompt}"})
            else:
                messages.append({"role": "user", "content": prompt})

            resp = await client.messages.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            content = getattr(resp, "content", [])
            if content and hasattr(content[0], "text"):
                return (content[0].text or "").strip()
            return "[anthropic]"
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {e}"

    async def generate_structured_response(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs,
    ) -> Dict[str, Any]:
        if not self.is_initialized:
            await self.initialize()

        client = await self._get_client()
        if not hasattr(client, "messages"):
            return {"mock": True, "prompt": prompt[:80]}

        try:
            # In real impl we'd use tools schema. For now, fallback to text and parse best-effort.
            text = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=kwargs.get("max_tokens"),
            )
            try:
                return json.loads(text)
            except Exception:
                return {"text": text}
        except Exception as e:
            self.logger.error(f"Failed to generate structured response: {e}")
            return {"error": str(e)}

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.is_initialized:
            await self.initialize()
        client = await self._get_client()
        if not hasattr(client, "embeddings"):
            return [[0.0 for _ in range(8)] for _ in texts]
        try:
            vectors: List[List[float]] = []
            for t in texts:
                resp = await client.embeddings.create(model="text-embedding-3-small", input=t)
                vectors.append(getattr(resp, "embedding", []) or [])
            return vectors
        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {e}")
            return [[0.0 for _ in range(8)] for _ in texts]

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info.update({
            "provider": "anthropic",
            "model": self.model_name,
            "has_api_key": bool(self.api_key),
        })
        return info 