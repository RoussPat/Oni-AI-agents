import json
import os
import sys
import urllib.request
from pathlib import Path

import pytest

# Ensure the project 'src' package is importable when running tests directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Speed up test suite by default
os.environ.setdefault("FAST_TESTS", "1")

# Optional: eliminate artificial model delays; avoid global caching that can
# interfere with monkeypatching-based tests
try:
    from src.oni_ai_agents.models.local_model import LocalModel

    _ORIG_LOCAL_INIT = LocalModel.__init__

    def _patched_local_init(self, config=None):
        cfg = dict(config or {})
        if os.getenv("FAST_TESTS", "0") == "1":
            cfg["delay"] = 0.0
        _ORIG_LOCAL_INIT(self, cfg)

    LocalModel.__init__ = _patched_local_init  # type: ignore[assignment]
except Exception:
    # Non-fatal if modules move; tests will still run
    pass


@pytest.fixture(scope="session")
def local_openai_available() -> bool:
    """Return True if a local OpenAI-compatible endpoint appears available.

    Probes `${OPENAI_BASE_URL}/models` (assuming base includes `/v1`).
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url:
        return False
    url = base_url.rstrip("/") + "/models"
    # Try HEAD first, then GET
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=1.5) as resp:  # nosec B310
            if not (200 <= getattr(resp, "status", 200) < 500):
                return False
    except Exception:
        try:
            with urllib.request.urlopen(url, timeout=2.5) as resp:  # nosec B310
                if not (200 <= getattr(resp, "status", 200) < 300):
                    return False
                # Ensure it's JSON-like
                data = json.loads(resp.read().decode("utf-8"))
                return isinstance(data, dict)
        except Exception:
            return False
    return True


@pytest.fixture(scope="session")
def model_provider_and_config(local_openai_available):
    """Provide (provider, config) for models used in E2E tests.

    - If local OpenAI endpoint is available: returns ("openai", {base_url, model, force_chat=True})
    - Otherwise: returns ("local", {delay: 0.0})
    """
    if local_openai_available:
        base_url = os.getenv("OPENAI_BASE_URL")
        model_name = os.getenv("OPENAI_MODEL", "gpt-oss")
        return (
            "openai",
            {"base_url": base_url, "model": model_name, "force_chat": True},
        )
    return ("local", {"delay": 0.0})

