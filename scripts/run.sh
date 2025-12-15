#!/usr/bin/env bash
set -euo pipefail

APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-2000}"
APP_MODULE="${APP_MODULE:-backend.app.main:app}"

# Activate virtualenv if present and not already active
if [[ -d ".venv" ]] && [[ -z "${VIRTUAL_ENV:-}" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Free the port if something is listening
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -t -i:"${APP_PORT}" || true)
  if [[ -n "${PIDS}" ]]; then
    echo "Stopping processes on port ${APP_PORT}: ${PIDS}"
    echo "${PIDS}" | xargs -r kill -9 || true
  fi
fi

exec python -m uvicorn "${APP_MODULE}" --host "${APP_HOST}" --port "${APP_PORT}"
