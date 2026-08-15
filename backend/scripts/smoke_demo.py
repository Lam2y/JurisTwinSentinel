import json
import httpx
BASE = "http://127.0.0.1:8000"

def show(label, response):
    response.raise_for_status(); data = response.json(); print(f"\n=== {label} ==="); print(json.dumps(data, indent=2)[:3000]); return data

with httpx.Client(base_url=BASE, timeout=10) as c:
    login = show("LOGIN", c.post("/api/auth/login", json={"email":"operations@regulatedbank.com","password":"Finals2026!"}))
    h = {"Authorization": f"Bearer {login['access_token']}"}
    show("RESET", c.post("/api/demo/reset", headers=h))
    show("DASHBOARD", c.get("/api/dashboard", headers=h))
    show("CASE", c.get("/api/cases/JT-2026-084", headers=h))
    show("GRAPH", c.get("/api/conflicts/CF-INCOME-001/graph", headers=h))
    sim = show("SIMULATION", c.post("/api/simulations/conflict/CF-INCOME-001/run", headers=h, json={}))
    approval = show("SUBMIT", c.post(f"/api/approvals/simulation/{sim['sim_ref']}/submit", headers=h, json={"selected_option":"C"}))
    show("APPROVE", c.post(f"/api/approvals/{approval['approval_ref']}/approve", headers=h, json={"comments":"smoke test"}))
    show("LEDGER VERIFY", c.get("/api/ledger/verify", headers=h))
    alert = show("BODYGUARD", c.post("/api/bodyguard/simulate-attack", headers=h))
    show("RESTORE", c.post(f"/api/bodyguard/alerts/{alert['alert_ref']}/restore", headers=h))
    show("FINAL STATUS", c.get("/api/demo/status", headers=h))
