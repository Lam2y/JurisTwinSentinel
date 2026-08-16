#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT/backend"
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY="${PYTHON:-python3}"; fi
export PYTHONPATH="$PWD"
exec "$PY" scripts/finals_launcher.py
