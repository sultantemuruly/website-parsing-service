#!/usr/bin/env sh
set -eu

PORT="${PORT:-8000}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$SCRIPT_DIR/.playwright-browsers}"

exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
