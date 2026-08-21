#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
else
  . .venv/bin/activate
fi
python -m pytest -q
echo "PREFLIGHT PASSED - all automated safety and workflow checks passed."
