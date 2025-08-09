#!/usr/bin/env bash
set -euo pipefail

# Idempotent project setup for WSL/headless environments
# - Creates a local venv at .venv
# - Installs Python deps from requirements.txt

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)
cd "$PROJECT_ROOT"

echo "[setup] Ensuring python3-venv is available (WSL)"
if ! dpkg -s python3-venv >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y python3-venv
fi

if [ ! -d .venv ]; then
  echo "[setup] Creating virtual environment at .venv"
  python3 -m venv .venv
fi

echo "[setup] Activating venv and upgrading pip"
source .venv/bin/activate
python -m pip install --upgrade pip

echo "[setup] Installing project requirements"
pip install -r requirements.txt

echo "[setup] Setup complete. To activate: source .venv/bin/activate"

