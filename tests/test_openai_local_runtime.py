from types import ModuleType, SimpleNamespace
from typing import Optional

import pytest

from src.oni_ai_agents.models.openai_model import OpenAIModel


def _make_fake_openai_module(
    *,
    provide_responses: bool,
    provide_chat: bool,
    text: str,
):
    """
    Create a fake `openai` module exposing an `AsyncOpenAI` that returns a client
    with either `responses.create(...)` or `chat.completions.create(...)`.
    """

    class _FakeResponses:
        def __init__(self, *, raise_error: bool = False):
            self._raise_error = raise_error

        async def create(
            self,
            *,
            model: str,
            input,
            temperature: float,
            max_output_tokens: Optional[int] = None,
            **kwargs,
        ):
            if self._raise_error:
                raise RuntimeError("404: not found")
            # Shape expected by OpenAIModel.generate_response (responses API)
            content = [SimpleNamespace(type="output_text", text=text)]
            item = SimpleNamespace(content=content)
            return SimpleNamespace(output=[item])

    class _FakeCompletions:
        async def create(
            self,
            *,
            model: str,
            messages,
            temperature: float,
            max_tokens: Optional[int] = None,
            **kwargs,
        ):
            # Shape expected by OpenAIModel.generate_response (chat.completions API)
            message = SimpleNamespace(content=text)
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

    class _FakeClient:
        def __init__(self, *, api_key: Optional[str] = None, base_url: Optional[str] = None, responses_raise: bool = False):
            if provide_responses:
                self.responses = _FakeResponses(raise_error=responses_raise)
            if provide_chat:
                self.chat = SimpleNamespace(completions=_FakeCompletions())

    class _FakeAsyncOpenAI:
        def __init__(self, *, api_key: Optional[str] = None, base_url: Optional[str] = None, responses_raise: bool = False):
            self._client = _FakeClient(api_key=api_key, base_url=base_url, responses_raise=responses_raise)

        # OpenAIModel expects to use the instance directly, not a builder.
        def __getattr__(self, name):
            return getattr(self._client, name)

    fake_mod = ModuleType("openai")
    fake_mod.AsyncOpenAI = _FakeAsyncOpenAI  # type: ignore[attr-defined]
    return fake_mod


@pytest.mark.asyncio
async def test_openai_local_responses_api(monkeypatch):
    # Arrange: fake openai with Responses API
    expected_text = "hello from responses"
    fake_openai = _make_fake_openai_module(provide_responses=True, provide_chat=False, text=expected_text)
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)
    # Ensure no real API key is picked up
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    model = OpenAIModel({"base_url": "http://localhost:8000/v1", "model": "gpt-oss"})

    # Act: call generate_response
    out = await model.generate_response("ping", temperature=0.1, max_tokens=16)

    # Assert: client is the fake (non-stub) and text matches
    client = await model._get_client()
    assert hasattr(client, "responses") and not hasattr(client, "chat")
    assert out == expected_text


@pytest.mark.asyncio
async def test_openai_local_chat_completions_api(monkeypatch):
    # Arrange: fake openai with Chat Completions API only
    expected_text = "hello from chat"
    fake_openai = _make_fake_openai_module(provide_responses=False, provide_chat=True, text=expected_text)


@pytest.mark.asyncio
async def test_fallback_from_responses_to_chat(monkeypatch):
    # Arrange: responses.create raises; chat returns ok
    expected_text = "ok"
    fake_openai = _make_fake_openai_module(provide_responses=True, provide_chat=True, text=expected_text)

    # Monkeypatch constructor to inject raising behavior
    def _factory(**kwargs):
        return fake_openai.AsyncOpenAI(**{**kwargs, "responses_raise": True})

    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)
    # Swap class to a factory wrapper that forwards responses_raise
    openai_mod = __import__("openai")
    openai_mod.AsyncOpenAI = _factory  # type: ignore[assignment]

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    model = OpenAIModel({"base_url": "http://localhost:8000/v1", "model": "gpt-oss"})
    out = await model.generate_response("ping")
    assert out == expected_text


@pytest.mark.asyncio
async def test_force_chat_skips_responses(monkeypatch):
    # Arrange: provide both, but force_chat=True should call only chat
    expected_text = "ok"
    fake_openai = _make_fake_openai_module(provide_responses=True, provide_chat=True, text=expected_text)
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    model = OpenAIModel({"base_url": "http://localhost:8000/v1", "model": "gpt-oss", "force_chat": True})
    out = await model.generate_response("ping")
    assert out == expected_text
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)
    # Ensure no real API key is picked up
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    model = OpenAIModel({"base_url": "http://localhost:8000/v1", "model": "gpt-oss"})

    # Act
    out = await model.generate_response("ping", temperature=0.1, max_tokens=16)

    # Assert
    client = await model._get_client()
    assert hasattr(client, "chat") and not hasattr(client, "responses")
    assert out == expected_text


@pytest.mark.skipif(
    not __import__("os").getenv("OPENAI_BASE_URL"),
    reason="No local OpenAI-compatible server advertised",
)
@pytest.mark.asyncio
async def test_optional_integration_roundtrip(monkeypatch):
    # Optional smoke test if a local server is running and reachable.
    # Skipped by default unless OPENAI_BASE_URL is set and the server responds.
    import os
    import socket
    import urllib.parse

    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url:
        pytest.skip("No base URL provided")

    # Quick reachability probe (TCP connect) and optional stricter target
    parsed = urllib.parse.urlparse(base_url)
    host, port = parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=0.75):
            pass
    except OSError:
        pytest.skip("Local OpenAI base URL not reachable")

    # If specifically targeting LM Studio default (`127.0.0.1:11435`) and vLLM id `gpt-oss:20b`,
    # enforce those assertions; otherwise treat as a generic OpenAI-compatible endpoint.
    strict_target = host == "127.0.0.1" and port == 11435

    # Verify /models endpoint responds
    import json as _json
    import urllib.request as _urlreq

    with _urlreq.urlopen(base_url.rstrip("/") + "/models", timeout=1.5) as resp:
        assert resp.status == 200
        payload = _json.loads(resp.read().decode("utf-8"))
        assert isinstance(payload, dict)
        assert "data" in payload
        if strict_target:
            names = {m.get("id") for m in payload.get("data", []) if isinstance(m, dict)}
            assert "gpt-oss:20b" in names

    model = OpenAIModel({"base_url": base_url, "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")})
    text = await model.generate_response("say hi in one word", temperature=0.0, max_tokens=5)
    assert isinstance(text, str)
    assert 0 < len(text.strip()) <= 32


