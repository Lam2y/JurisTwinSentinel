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

URL=os.getenv("JURISTWIN_WEBHOOK_URL","http://127.0.0.1:8000/api/live/webhook")
SECRET=os.getenv("WEBHOOK_SECRET","juristwin-finals-webhook-secret")
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
