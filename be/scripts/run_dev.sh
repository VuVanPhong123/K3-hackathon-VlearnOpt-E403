#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BE_DIR"

if [ ! -d ".venv" ]; then
  "$SCRIPT_DIR/setup_venv.sh"
fi

source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
