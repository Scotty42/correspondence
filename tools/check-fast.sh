#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/korrespondenz"
cd "${ROOT}"

echo "[check-fast] backend: pip check + compile"
"${ROOT}/.venv/bin/python" -m pip check
"${ROOT}/.venv/bin/python" -m compileall -q app

echo "[check-fast] frontend: build"
cd "${ROOT}/frontend"
npm run build

echo "[check-fast] settings tests"
cd "${ROOT}"
PYTHONPATH=/opt/korrespondenz "${ROOT}/.venv/bin/python" -m pytest -q tests/test_settings_db.py

echo "[check-fast] OK"
