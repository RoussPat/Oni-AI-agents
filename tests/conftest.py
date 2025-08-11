import os
import sys
from pathlib import Path

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

