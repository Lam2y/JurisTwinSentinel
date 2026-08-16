"""Open the finals UI only after the selected local API port is actually ready."""
from __future__ import annotations
import os
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER = ROOT / ".juristwin_port"


def port() -> int:
    if os.getenv("JURISTWIN_PORT"):
        return int(os.environ["JURISTWIN_PORT"])
    if MARKER.exists():
        return int(MARKER.read_text(encoding="ascii").strip())
    return 8000


def ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=0.75) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main() -> int:
    p = port()
    health = f"http://127.0.0.1:{p}/api/system/health"
    finals = f"http://127.0.0.1:{p}/finals"
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if ready(health):
            webbrowser.open(finals, new=2)
            return 0
        time.sleep(0.25)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
