#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "==> Installing Python dependencies..."
uv sync --frozen --no-dev

echo "==> Build complete."
