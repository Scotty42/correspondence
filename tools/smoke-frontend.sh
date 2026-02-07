#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

cd "${FRONTEND_DIR}"

PORT="${SMOKE_FRONTEND_PORT:-4174}"
HOST="${SMOKE_FRONTEND_HOST:-127.0.0.1}"

echo "[smoke-frontend] dir: ${FRONTEND_DIR}"
echo "[smoke-frontend] host:port ${HOST}:${PORT}"

if [[ ! -f package.json ]]; then
  echo "[smoke-frontend] ERROR: no package.json found in ${FRONTEND_DIR}"
  exit 1
fi

echo "[smoke-frontend] npm ci"
npm ci

echo "[smoke-frontend] npm run build"
npm run build

# Optional: preview smoke (comment out if you don’t want a server run)
echo "[smoke-frontend] npm run preview (temporary) on ${HOST}:${PORT}"
npm run preview -- --host "${HOST}" --port "${PORT}" &
PREVIEW_PID=$!

cleanup() {
  echo "[smoke-frontend] stopping preview (pid=${PREVIEW_PID})"
  kill "${PREVIEW_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Wait until it responds
URL="http://${HOST}:${PORT}/"
echo "[smoke-frontend] wait for ${URL}"
for i in {1..20}; do
  if curl -fsS "${URL}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "[smoke-frontend] GET ${URL}"
curl -fsSI "${URL}" | head -n 20

echo "[smoke-frontend] OK"

