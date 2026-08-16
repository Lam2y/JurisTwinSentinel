from __future__ import annotations
import os
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
MARKER = ROOT / ".juristwin_port"


def runtime_port() -> int:
    if os.getenv("JURISTWIN_PORT"):
        port = int(os.environ["JURISTWIN_PORT"])
    elif MARKER.exists():
        port = int(MARKER.read_text(encoding="ascii").strip())
    else:
        port = 8000
    MARKER.write_text(str(port), encoding="ascii")
    return port


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=runtime_port(), reload=False)
