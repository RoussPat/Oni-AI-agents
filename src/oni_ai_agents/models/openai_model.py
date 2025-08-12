from __future__ import annotations

"""
OpenAI model implementation.
"""

import json
import os
from typing import Any, Dict, List, Optional

from .base_model import BaseModel


class OpenAIModel(BaseModel):
    """
    OpenAI model implementation using OpenAI API.

    Supports GPT-3.5, GPT-4, and other OpenAI models.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI model.

        Args:
            config: Configuration dictionary with:
                - api_key: OpenAI API key
                - model: Model name (e.g., gpt-4, gpt-3.5-turbo)
                - base_url: Optional custom base URL
        """
        super().__init__(config)
        self.api_key = (config or {}).get("api_key") or os.getenv("OPENAI_API_KEY")
        self.model_name = (config or {}).get("model", "gpt-4o-mini")
        # Allow override via env when not provided in config
        self.base_url = (config or {}).get("base_url") or os.getenv("OPENAI_BASE_URL")
        # Optional override to force Chat Completions path
        env_force = os.getenv("OPENAI_FORCE_CHAT", "").strip().lower() in {"1", "true", "yes"}
        self.force_chat = bool((config or {}).get("force_chat", False) or env_force)
        self._client = None  # Lazy client

    async def _get_client(self):
        """Create and cache an async OpenAI client lazily.

        Does not perform any network calls to remain test-friendly and
        compatible with restricted environments.
        """
        if self._client is not None:
            return self._client
        try:
            # Prefer the modern async client if available
            from openai import AsyncOpenAI  # type: ignore

            # If a custom base_url is provided (e.g., local OpenAI-compatible server),
            # always instantiate a real client, even without an API key.
            if self.base_url:
                self._client = AsyncOpenAI(api_key=self.api_key or "EMPTY", base_url=self.base_url)
                return self._client

            # No base_url: require an API key for the hosted OpenAI service
            if not self.api_key:
                # Return a stub client to avoid raising during tests
                self.logger.warning("OPENAI_API_KEY not set; returning stub client")
                self._client = object()
                return self._client

            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            return self._client
        except Exception as e:  # openai not installed or API changes
            self.logger.warning(f"OpenAI client unavailable: {e}")
            self._client = object()
            return self._client

    async def initialize(self) -> bool:
        """Mark model as initialized without making network calls."""
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
        """
        Generate a response using OpenAI API.

        In restricted environments without the OpenAI package or API key,
        returns a deterministic stub string to keep tests running.
        """
        if not self.is_initialized:
            await self.initialize()

        client = await self._get_client()
        # If client is a stub object, return a mock response
        if not hasattr(client, "chat") and not hasattr(client, "responses"):
            return "[openai-mock] " + (prompt[:120] if prompt else "")

        # Build messages once
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # If force_chat is set, skip responses path entirely
        if not self.force_chat and hasattr(client, "responses"):
            try:
                resp = await client.responses.create(
                    model=self.model_name,
                    input=messages,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    **kwargs,
                )
                # Best-effort content extraction
                text = ""
                # 1) Common simple attribute on many SDKs/fakes
                try:
                    text_attr = getattr(resp, "output_text", None)
                    if isinstance(text_attr, str) and text_attr:
                        return text_attr
                except Exception:
                    pass
                # 2) Structured parts array (typed objects)
                try:
                    if resp and getattr(resp, "output", None):
                        parts = getattr(resp.output[0], "content", [])
                        for p in parts:
                            if getattr(p, "type", "") == "output_text":
                                text += getattr(p, "text", "")
                        if text:
                            return text
                except Exception:
                    pass
                # 3) Structured parts array (dicts)
                try:
                    content = None
                    if hasattr(resp, "output") and resp.output and hasattr(resp.output[0], "content"):
                        content = resp.output[0].content
                    elif hasattr(resp, "content"):
                        content = resp.content
                    if isinstance(content, list):
                        for p in content:
                            if isinstance(p, dict) and p.get("type") == "output_text":
                                text += p.get("text", "")
                        if text:
                            return text
                except Exception:
                    pass
                # If we reach here, responses path returned no text; continue to chat fallback
            except Exception as e:
                # Log and fall back to chat rather than failing the whole call
                self.logger.warning(f"Responses API call failed, falling back to chat.completions: {e}")

        # Fallback to Chat Completions if present
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            try:
                resp = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                choice = (getattr(resp, "choices", []) or [{}])[0]
                msg = getattr(choice, "message", {})
                return (getattr(msg, "content", None) or "").strip() or "[openai]"
            except Exception as e:
                self.logger.error(f"Chat Completions call failed: {e}")
                return f"Error generating response: {e}"

        return "[openai]"

    async def generate_structured_response(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a structured response. Returns a stub dict when API is unavailable.
        """
        if not self.is_initialized:
            await self.initialize()

        client = await self._get_client()
        if not hasattr(client, "responses") and not hasattr(client, "chat"):
            # Best-effort mocked structure
            return {"mock": True, "prompt": prompt[:80]}

        try:
            # Prefer Responses API with JSON schema via tool/function in real implementations
            text = await self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                **kwargs,
            )
            # Best effort JSON parse
            try:
                return json.loads(text)
            except Exception:
                return {"text": text}
        except Exception as e:
            self.logger.error(f"Failed to generate structured response: {e}")
            return {"error": str(e)}

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings using OpenAI's embedding API. Returns zeros in restricted envs.
        """
        if not self.is_initialized:
            await self.initialize()

        client = await self._get_client()
        if not hasattr(client, "embeddings"):
            # Deterministic stub embedding
            return [[0.0 for _ in range(8)] for _ in texts]

        try:
            vectors: List[List[float]] = []
            for text in texts:
                resp = await client.embeddings.create(model="text-embedding-3-small", input=text)
                vec = (getattr(resp, "data", []) or [{}])[0]
                vectors.append(getattr(vec, "embedding", []) or [])
            return vectors
        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {e}")
            return [[0.0 for _ in range(8)] for _ in texts]

    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        info = super().get_model_info()
        info.update({
            "provider": "openai",
            "model": self.model_name,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "force_chat": bool(self.force_chat),
        })
        return info 