#!/usr/bin/env bash
set -euo pipefail

# One-command startup for Ollama in WSL, bound to 127.0.0.1:11435

HOST="127.0.0.1"
PORT="11435"
BASE="http://${HOST}:${PORT}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "[error] 'ollama' not found in WSL. Install: curl -fsSL https://ollama.com/install.sh | sh" >&2
  exit 1
fi

export OLLAMA_HOST="${HOST}:${PORT}"

LOG_FILE="/tmp/ollama_${PORT}.log"
PID_FILE="/tmp/ollama_${PORT}.pid"

# If a previous process is running on the same port, leave it be
if curl -sf "${BASE}/v1/models" >/dev/null 2>&1 || curl -sf "${BASE}/api/tags" >/dev/null 2>&1; then
  echo "[ok] Ollama already listening at ${BASE}"
else
  echo "[info] Starting Ollama at ${OLLAMA_HOST} ..."
  nohup ollama serve >"${LOG_FILE}" 2>&1 &
  echo $! >"${PID_FILE}"
fi

echo "[info] Waiting for health at ${BASE}/v1/models ..."
attempts=0
until curl -sf "${BASE}/v1/models" >/dev/null 2>&1 || curl -sf "${BASE}/api/tags" >/dev/null 2>&1; do
  attempts=$((attempts+1))
  if [ ${attempts} -gt 60 ]; then
    echo "[error] Ollama did not become healthy in time. See ${LOG_FILE}" >&2
    exit 1
  fi
  sleep 1
done

echo "[ok] Ollama listening on ${OLLAMA_HOST}"
echo "[ok] GET ${BASE}/v1/models ->"
curl -s "${BASE}/v1/models" || curl -s "${BASE}/api/tags"
echo

echo "[note] Logs: ${LOG_FILE}  PID: $(cat "${PID_FILE}" 2>/dev/null || echo "?")"

