"""Send a real signed evidence event to a running JurisTwin Sentinel instance.

Run in a second terminal while the Finals app is open:
    python backend/scripts/send_live_webhook.py

This uses only Python's standard library. It is a genuine HTTP POST to the HMAC-authenticated
connector gateway, not an in-process demo shortcut.
"""
import hashlib
import hmac
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

ROOT=Path(__file__).resolve().parents[2]
PORT_FILE=ROOT / ".juristwin_port"
default_port=PORT_FILE.read_text(encoding="ascii").strip() if PORT_FILE.exists() else "8000"
URL=os.getenv("JURISTWIN_WEBHOOK_URL",f"http://127.0.0.1:{default_port}/api/live/webhook")
SECRET=os.getenv("WEBHOOK_SECRET")
if not SECRET:
    raise SystemExit("WEBHOOK_SECRET is not configured. Run setup_windows.bat or tools/bootstrap_env.py first.")
PAYLOAD={
    "event_id":"evt-live-finals-001",
    "source":"External Policy Bus",
    "title":"Realtime judge policy event",
    "body":"Effective immediately, bank statements are no longer accepted as standalone income evidence. Gig workers must submit payslips.",
    "authority":"External Operations Lead",
    "authority_level":3,
    "sensitivity":"internal",
}
material=f"{PAYLOAD['event_id']}|{PAYLOAD['body']}".encode("utf-8")
signature=hmac.new(SECRET.encode("utf-8"),material,hashlib.sha256).hexdigest()
request=urllib.request.Request(
    URL,
    data=json.dumps(PAYLOAD).encode("utf-8"),
    headers={"Content-Type":"application/json","X-JurisTwin-Signature":signature},
    method="POST",
)
try:
    with urllib.request.urlopen(request,timeout=10) as response:
        result=json.loads(response.read().decode("utf-8"))
        print(json.dumps(result,indent=2))
except urllib.error.HTTPError as exc:
    print(exc.status,exc.read().decode("utf-8"))
