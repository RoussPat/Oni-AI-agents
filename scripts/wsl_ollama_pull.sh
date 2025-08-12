#!/usr/bin/env bash
set -euo pipefail

# Usage: wsl_ollama_pull.sh <model[:tag]> [-t]
# Example: wsl_ollama_pull.sh gpt-oss:20b -t

if [ $# -lt 1 ]; then
  echo "Usage: $0 <model[:tag]> [-t]" >&2
  exit 1
fi

MODEL="$1"; shift || true
TAIL=false
if [ "${1:-}" = "-t" ]; then
  TAIL=true
fi

HOST="127.0.0.1"
PORT="11435"
export OLLAMA_HOST="${HOST}:${PORT}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "[error] 'ollama' not found in WSL. Install: curl -fsSL https://ollama.com/install.sh | sh" >&2
  exit 1
fi

echo "[info] Pulling ${MODEL} from Ollama at ${OLLAMA_HOST}..."
# Ollama already streams progress to stdout; -t is a no-op to indicate tailing
ollama pull "${MODEL}"

echo "[ok] Pull complete. Installed models:"
ollama list || true

