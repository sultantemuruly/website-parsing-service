#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$(pwd)/.playwright-browsers}"
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"

echo "==> Installing Python dependencies..."
uv sync --frozen --no-dev

echo "==> Installing Playwright Chromium (browsers path: $PLAYWRIGHT_BROWSERS_PATH)..."
uv run playwright install --with-deps chromium

echo "==> Build complete."
