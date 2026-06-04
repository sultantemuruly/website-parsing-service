#!/usr/bin/env sh
set -eu

PORT="${PORT:-8000}"
export PYTHONPATH="${PWD}/src${PYTHONPATH:+:${PYTHONPATH}}"

exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
