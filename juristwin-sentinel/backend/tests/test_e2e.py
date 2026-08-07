import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./test_juristwin.db"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def login(email="operations@regulatedbank.com"):
    r = client.post("/api/auth/login", json={"email": email, "password": "Finals2026!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_full_grand_finals_story():
    with client:
        h = login()
        client.post("/api/demo/reset", headers=h)
        d = client.get("/api/dashboard", headers=h).json()
        assert d["metrics"]["active_cases"] == 128
        assert d["metrics"]["decision_conflicts"] == 3
        assert d["metrics"]["customers_at_risk"] == 27

        case = client.get("/api/cases/JT-2026-084", headers=h).json()
        assert case["conflict"]["conflict_ref"] == "CF-INCOME-001"
        assert len(case["timeline"]) >= 4

        graph = client.get("/api/conflicts/CF-INCOME-001/graph", headers=h).json()
        assert len(graph["nodes"]) >= 6

        sim = client.post("/api/simulations/conflict/CF-INCOME-001/run", headers=h, json={}).json()
        assert sim["recommended_option"] == "C"
        option_c = next(x for x in sim["options"] if x["key"] == "C")
        assert option_c["predicted_delay_days"] == 1.1
        assert option_c["complaint_probability"] == 17

        approval = client.post(f"/api/approvals/simulation/{sim['sim_ref']}/submit", headers=h, json={"selected_option": "C"}).json()
        approved = client.post(f"/api/approvals/{approval['approval_ref']}/approve", headers=h, json={"comments": "Grand Finals governed publish"}).json()
        assert approved["decision_contract"]["decision_ref"] == "JT-084"

        d2 = client.get("/api/dashboard", headers=h).json()
        assert d2["metrics"]["decision_conflicts"] == 2
        assert d2["metrics"]["customers_at_risk"] == 0
        assert d["metrics"]["protected_decisions"] == 94
        assert d2["metrics"]["protected_decisions"] == 121

        chain = client.get("/api/ledger/verify", headers=h).json()
        assert chain["ok"] is True

        alert = client.post("/api/bodyguard/simulate-attack", headers=h).json()
        assert alert["status"] == "open"
        restored = client.post(f"/api/bodyguard/alerts/{alert['alert_ref']}/restore", headers=h).json()
        assert restored["status"] == "restored"
        assert client.get("/api/ledger/verify", headers=h).json()["ok"] is True


def test_bodyguard_requires_published_decision():
    with client:
        h = login()
        client.post("/api/demo/reset", headers=h)
        r = client.post("/api/bodyguard/simulate-attack", headers=h)
        assert r.status_code == 409

def test_intern_sees_restricted_evidence_redacted():
    with client:
        manager = login()
        client.post("/api/demo/reset", headers=manager)
        h = login("intern@regulatedbank.com")
        r = client.post("/api/memory/search", headers=h, json={"query":"customer stalled bank statement", "limit":10})
        assert r.status_code == 200
        results = r.json()["results"]
        restricted = [x for x in results if x.get("sensitivity") == "restricted"]
        assert restricted
        assert all(x["body"] == "[REDACTED BY SENTINEL SHIELD]" for x in restricted)
