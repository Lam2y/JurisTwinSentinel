"""Open the finals UI only after the local API is actually ready."""
from __future__ import annotations

import time
import urllib.error
import urllib.request
import webbrowser

HEALTH_URL = "http://127.0.0.1:8000/api/system/health"
FINALS_URL = "http://127.0.0.1:8000/finals"


def ready() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=0.75) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main() -> int:
    # Give Uvicorn up to 30 seconds on a slower finals laptop.
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if ready():
            webbrowser.open(FINALS_URL, new=2)
            return 0
        time.sleep(0.25)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
