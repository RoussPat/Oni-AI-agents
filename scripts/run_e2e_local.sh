#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${OPENAI_BASE_URL:-}" ]]; then
  echo "OPENAI_BASE_URL is not set. Example: http://127.0.0.1:11435/v1" >&2
  exit 1
fi

get_health_url() {
  local base="$1"
  base="${base%/}"
  if [[ "${base,,}" == *"/v1" ]]; then
    echo "$base/models"
  else
    echo "$base/v1/models"
  fi
}

HEALTH_URL="$(get_health_url "$OPENAI_BASE_URL")"
echo "Checking endpoint: $HEALTH_URL"
if ! curl -sSf --max-time 3 "$HEALTH_URL" >/dev/null; then
  echo "Endpoint not reachable at $HEALTH_URL" >&2
  exit 1
fi

# Force chat-completions path for compat servers like Ollama
export OPENAI_FORCE_CHAT=1

echo "Running pytest -m e2e ..."
if ! python -m pytest -q -m e2e; then
  code=$?
  if [[ "$code" -eq 5 ]]; then
    echo "No e2e tests collected; running optional integration smoke test instead..."
    python -m pytest -q Oni-AI-agents/tests/test_openai_local_runtime.py::test_optional_integration_roundtrip
    code=$?
  fi
  if [[ "$code" -ne 0 ]]; then
    echo "E2E run failed with exit code $code" >&2
    exit "$code"
  fi
fi

echo "E2E run completed successfully."
exit 0


