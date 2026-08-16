"""Choose a free local JurisTwin port and persist it for helper processes."""
from __future__ import annotations
import os
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER = ROOT / ".juristwin_port"
START = int(os.getenv("JURISTWIN_PORT", "8000"))


def is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


for port in range(START, START + 20):
    if is_free(port):
        MARKER.write_text(str(port), encoding="ascii")
        print(port)
        raise SystemExit(0)

raise SystemExit(f"No free JurisTwin port found in {START}-{START+19}")
