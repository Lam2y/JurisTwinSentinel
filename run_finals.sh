#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT/backend"
PYTHONPATH="$PWD" python scripts/open_finals_when_ready.py >/dev/null 2>&1 &
PYTHONPATH="$PWD" python run.py
