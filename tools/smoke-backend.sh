#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV="${ROOT_DIR}/.venv"
PY="${VENV}/bin/python"
PIP="${VENV}/bin/pip"

PORT="${SMOKE_BACKEND_PORT:-8081}"
HOST="${SMOKE_BACKEND_HOST:-127.0.0.1}"
HEALTH_URL="http://${HOST}:${PORT}/api/health"
SERVICES_URL="http://${HOST}:${PORT}/api/health/services"

echo "[smoke-backend] repo: ${ROOT_DIR}"
echo "[smoke-backend] python: ${PY}"
echo "[smoke-backend] host:port ${HOST}:${PORT}"

if [[ ! -x "${PY}" ]]; then
  echo "[smoke-backend] ERROR: venv not found at ${VENV}. Create it first."
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "[smoke-backend] pip upgrade + install requirements"
"${PY}" -m pip install --upgrade pip wheel >/dev/null
"${PIP}" install -r requirements.txt >/dev/null

echo "[smoke-backend] pip check"
"${PY}" -m pip check

echo "[smoke-backend] compileall app/"
"${PY}" -m compileall -q app

echo "[smoke-backend] get or create db"
export KORRESPONDENZ_DATABASE_URL="${KORRESPONDENZ_DATABASE_URL:-sqlite+aiosqlite:////tmp/korrespondenz.smoke.sqlite}"

echo "[smoke-backend] start uvicorn (temporary) on ${HOST}:${PORT}"
# Start server in background
"${VENV}/bin/uvicorn" app.main:app --host "${HOST}" --port "${PORT}" --proxy-headers --forwarded-allow-ips="${HOST}" &
UVICORN_PID=$!

cleanup() {
  echo "[smoke-backend] stopping uvicorn (pid=${UVICORN_PID})"
  kill "${UVICORN_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Wait until healthy (max ~20s)
echo "[smoke-backend] wait for health endpoint..."
for i in {1..20}; do
  if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "[smoke-backend] GET ${HEALTH_URL}"
curl -fsS "${HEALTH_URL}" | head -c 500 || (echo && exit 1)
echo

echo "[smoke-backend] GET ${SERVICES_URL}"
curl -fsS "${SERVICES_URL}" | head -c 500 || (echo && exit 1)
echo

echo "[smoke-backend] OK"

