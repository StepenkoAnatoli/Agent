#!/usr/bin/env bash
# Agent launcher for macOS / Linux
cd "$(dirname "$0")"

echo "============================================"
echo "  Agent - local AI assistant"
echo "============================================"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] Python 3 was not found. Install it first (https://www.python.org)."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/3] First run: creating a private Python environment..."
  python3 -m venv .venv || {
    echo "[ERROR] Could not create the Python environment."
    exit 1
  }
else
  echo "[1/3] Environment found."
fi

echo "[2/3] Checking dependencies (first run downloads them)..."
.venv/bin/python -m pip install -r requirements.txt --quiet || {
  echo "[ERROR] Could not install dependencies. Check your internet connection."
  exit 1
}

echo "[3/3] Starting the server at http://localhost:8000"
( sleep 3; xdg-open http://localhost:8000 2>/dev/null || open http://localhost:8000 2>/dev/null ) &

.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000

echo "Server stopped."
