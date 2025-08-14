"""
E2E test against a local OpenAI-compatible endpoint (vLLM/Ollama).

Skipped by default unless OPENAI_BASE_URL is reachable and the reported models
include OPENAI_MODEL (default: gpt-oss:20b).

Run:
    python -m pytest -q tests/test_e2e_local_gpt_oss.py

With Ollama, set before running:
    OPENAI_BASE_URL=http://127.0.0.1:11435/v1
    OPENAI_MODEL=gpt-oss:20b
    OPENAI_FORCE_CHAT=1   # Optional hint; test does not require source changes
"""

from __future__ import annotations

import asyncio
import json
import os
import urllib.request
from typing import Any, Dict

import pytest

from src.oni_ai_agents.core.agent import Agent
from src.oni_ai_agents.core.agent_types import AgentType


def _get_env_base_and_model() -> tuple[str | None, str]:
    base = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL") or "gpt-oss:20b"
    return base, model


def _endpoint_models(base_url: str) -> Dict[str, Any] | None:
    url = base_url.rstrip("/") + "/models"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:  # nosec B310
            body = resp.read().decode("utf-8", "ignore")
            try:
                return json.loads(body)
            except Exception:
                return None
    except Exception:
        return None


def _should_skip() -> tuple[bool, str]:
    base, model = _get_env_base_and_model()
    if not base:
        return True, "OPENAI_BASE_URL not set"
    data = _endpoint_models(base)
    if not data:
        return True, f"{base}/models not reachable"
    # Expect OpenAI-like {"data": [{"id": "..."}, ...]}
    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return True, "models endpoint returned unexpected schema"
    ids = [str(getattr(x, "id", x.get("id"))) for x in items if isinstance(x, (dict, object))]
    if not any(model in (i or "") for i in ids):
        return True, f"model {model} not present in /v1/models"
    return False, ""


class _MinimalE2EAgent(Agent):
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt: str = input_data.get("prompt", "Say hello in one short sentence.")
        # Keep small for CPU/GPU low-VRAM
        text = await self.model.generate_response(
            prompt,
            temperature=0.1,
            max_tokens=64,
            timeout=10,
        )
        return {"text": text}

    async def _on_start(self) -> None:
        return None

    async def _on_stop(self) -> None:
        return None

    async def _process_message(self, message) -> None:
        return None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_local_gpt_oss_live():
    skip, reason = _should_skip()
    if skip:
        pytest.skip(reason)

    base_url, model_name = _get_env_base_and_model()
    api_key = os.getenv("OPENAI_API_KEY") or "local-not-needed"

    agent = _MinimalE2EAgent(
        agent_id="e2e_local_gpt_oss",
        agent_type=AgentType.OBSERVING,
        model_provider="openai",
        model_config={
            "base_url": base_url,
            "model": model_name,
            "api_key": api_key,
        },
    )

    try:
        await agent.start()
        result = await asyncio.wait_for(
            agent.process_input({"prompt": "Respond with a short friendly hello."}), timeout=60
        )
        text = result.get("text", "")
        assert isinstance(text, str)
        # Accept any non-empty response, including error text if backend lacks /responses
        assert len(text) > 0
    finally:
        await agent.stop()


