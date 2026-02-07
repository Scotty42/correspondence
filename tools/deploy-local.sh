#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/korrespondenz"

echo "[deploy] cd ${ROOT}"
cd "${ROOT}"

echo "[deploy] ensure clean working tree"
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "[deploy] ERROR: you have uncommitted changes. Commit/stash first."
  git status --porcelain
  exit 1
fi

echo "[deploy] fetch + fast-forward main"
git checkout main >/dev/null
git fetch origin
git pull --ff-only

echo "[deploy] backend: install deps"
"${ROOT}/.venv/bin/python" -m pip install --upgrade pip wheel >/dev/null
"${ROOT}/.venv/bin/pip" install -r requirements.txt >/dev/null
"${ROOT}/.venv/bin/python" -m pip check

echo "[deploy] backend: compile"
"${ROOT}/.venv/bin/python" -m compileall -q app

echo "[deploy] frontend: install + build"
cd "${ROOT}/frontend"
npm ci
npm run build

echo "[deploy] run config unit test (fast)"
cd "${ROOT}"
PYTHONPATH=/opt/korrespondenz "${ROOT}/.venv/bin/python" -m pytest -q tests/test_settings_db.py

echo "[deploy] restart services"
systemctl restart korrespondenz.service
systemctl restart korrespondenz-frontend.service

echo "[deploy] check services"
systemctl --no-pager --full status korrespondenz.service | head -n 20
systemctl --no-pager --full status korrespondenz-frontend.service | head -n 20

echo "[deploy] OK"

