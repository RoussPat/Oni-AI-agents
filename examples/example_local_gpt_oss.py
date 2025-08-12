"""
Example: Using a local OpenAI-compatible GPT-OSS server with the agents.

Reads OPENAI_BASE_URL and OPENAI_MODEL from the environment and creates a
minimal agent configured to talk to the local server.

If the server is not reachable, prints a helpful notice and exits with code 0
so CI does not fail.
"""

from __future__ import annotations

import asyncio
import os
import sys
import urllib.request
from typing import Any, Dict

from src.oni_ai_agents.core.agent import Agent
from src.oni_ai_agents.core.agent_types import AgentType


class _LocalDemoAgent(Agent):
    """Minimal agent just to exercise the model connection."""

    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt: str = input_data.get("prompt", "Say hello in one short sentence.")
        if not self.model:
            return {"error": "Model not initialized"}
        text = await self.model.generate_response(prompt)
        return {"text": text}

    async def _on_start(self) -> None:
        return None

    async def _on_stop(self) -> None:
        return None

    async def _process_message(self, message) -> None:  # pragma: no cover - demo only
        return None


def _check_server_reachable(base_url: str) -> bool:
    """Best-effort reachability check against the models endpoint."""
    url = base_url.rstrip("/") + "/models"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:  # nosec B310
            return 200 <= getattr(resp, "status", 200) < 500
    except Exception:
        return False


async def main() -> None:
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL")

    if not base_url or not model_name:
        print(
            "Local GPT-OSS not configured. Set OPENAI_BASE_URL and OPENAI_MODEL, then re-run."
        )
        sys.exit(0)

    if not _check_server_reachable(base_url):
        print(
            f"Local GPT-OSS server not reachable at {base_url}. "
            "Start it first, then re-run this example."
        )
        sys.exit(0)

    # Ensure OpenAI client is constructed (our adapter uses a stub if api_key is missing).
    api_key = os.getenv("OPENAI_API_KEY") or "local-not-needed"

    agent = _LocalDemoAgent(
        agent_id="local_gpt_oss_demo",
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
        result = await agent.process_input({"prompt": "Respond with a friendly hello in 1 short sentence."})
        text = result.get("text", "")
        if isinstance(text, str) and text.startswith("[openai-mock]"):
            print(
                "OpenAI client not available; returned mock output. Install requirements/models.txt to use the local server."
            )
        else:
            print("Local GPT-OSS response:", text)
    except Exception as e:  # pragma: no cover - demo resilience
        # Treat all failures as non-fatal for CI.
        print(f"Could not complete request to local GPT-OSS: {e}")
        sys.exit(0)
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())


