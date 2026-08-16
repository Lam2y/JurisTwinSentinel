"""Resilient local launcher for the Grand Finals.

The parent process starts immediately and prints progress while the API child imports scikit-learn
and warms the local policy models. This prevents a legitimate first-start delay from looking like
a frozen/crashed application on Windows.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
MARKER = ROOT / ".juristwin_port"


def free_port(start: int = 8000) -> int:
    requested = os.getenv("JURISTWIN_PORT")
    if requested:
        start = int(requested)
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free local port found in {start}-{start + 19}")


def healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=0.7) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main() -> int:
    try:
        port = free_port()
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    MARKER.write_text(str(port), encoding="ascii")
    env = os.environ.copy()
    env["JURISTWIN_PORT"] = str(port)
    env["PYTHONPATH"] = str(BACKEND)
    base = f"http://127.0.0.1:{port}"
    health = f"{base}/api/system/health"
    finals = f"{base}/finals"

    print("=" * 56)
    print("  JurisTwin Sentinel - Championship v5.7 MaxScore")
    print("=" * 56)
    print(f"Backend:   {base}")
    print(f"Finals UI: {finals}")
    print(f"Swagger:   {base}/docs")
    if port != 8000:
        print(f"[SAFE FAILOVER] Port 8000 is busy; using {port} instead.")
    print()
    print("[STARTING] Launching local governed runtime...")
    print("[AI] Loading offline learned policy models + symbolic verifier.")
    print("[INFO] A cold Windows/scikit-learn import can take several seconds.")
    print("[INFO] Do not press Ctrl+C while STARTING is displayed.")
    print()

    child = subprocess.Popen([sys.executable, "run.py"], cwd=str(BACKEND), env=env)
    started = time.monotonic()
    next_heartbeat = 1.5
    deadline = started + 75

    try:
        while time.monotonic() < deadline:
            code = child.poll()
            if code is not None:
                print(f"[ERROR] Backend exited before becoming healthy (exit code {code}).")
                return code or 1
            if healthy(health):
                elapsed = time.monotonic() - started
                print(f"[READY] JurisTwin API healthy in {elapsed:.1f}s.")
                print("[READY] Opening the finals interface now.")
                webbrowser.open(finals, new=2)
                print("[RUNNING] Keep this window open. Press Ctrl+C only when the demo is finished.")
                print()
                return child.wait()
            elapsed = time.monotonic() - started
            if elapsed >= next_heartbeat:
                stage = "warming local AI" if elapsed < 12 else "finishing startup checks"
                print(f"[STARTING {elapsed:>4.1f}s] {stage} ...")
                next_heartbeat += 2.0
            time.sleep(0.25)

        print("[ERROR] JurisTwin did not become healthy within 75 seconds.")
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
        return 1
    except KeyboardInterrupt:
        print("\n[STOPPING] Shutting down JurisTwin cleanly...")
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
