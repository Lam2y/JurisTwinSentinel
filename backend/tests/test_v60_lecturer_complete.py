from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def auth(email="operations@regulatedbank.com"):
    r = client.post("/api/auth/login", json={"email": email, "password": "Finals2026!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def reset(h):
    r = client.post("/api/demo/reset", headers=h)
    assert r.status_code == 200, r.text


def test_management_controls_map_all_lecturer_requirements_live():
    with client:
        h = auth(); reset(h)
        r = client.get("/api/system/manager-control-summary", headers=h)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "COMPLETE"
        assert d["score"] == 100
        assert d["passed"] == d["total"] == 8
        assert {x["key"] for x in d["controls"]} == {
            "trusted_answer", "source_scope", "authority_majority", "privacy",
            "customer_security", "secure_transfer", "audit", "realtime",
        }
        assert all(x["original"] and x["now"] and x["proof"] and x["action"] for x in d["controls"])


def test_answer_is_definite_source_bound_and_explains_hybrid_retrieval():
    with client:
        h = auth(); reset(h)
        r = client.post("/api/memory/answer", headers=h, json={
            "question": "Can gig workers use bank statements as income evidence?",
            "preview_role": "manager",
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["management_status"] == "GOVERNED_ANSWER"
        assert d["answer"]
        assert d["primary_source"]
        assert d["sources_used"]
        assert d["primary_source"]["source"] == "Outlook Approval"
        assert d["resolution"]["mode"] == "APPROVED_AUTHORITY"
        assert "Keyword/BM25" in d["resolution"]["retrieval_strategy"]
        assert "same-tier majority" in d["resolution"]["winner_rule"]
        assert isinstance(d["retrieval_matches"], list) and d["retrieval_matches"]
        assert d["freshness"]["answer_recomputed"] is True


def test_source_scope_is_manager_configurable_but_privacy_boundaries_cannot_be_weakened():
    with client:
        h = auth(); reset(h)

        # A manager can narrow Teams to a selected group, but cannot enable private DMs or make
        # Teams chat an official policy authority.
        r = client.patch("/api/integrations/teams/policy", headers=h, json={"config": {
            "allowed_channels": ["Compliance"],
            "personal_dm_allowed": True,
            "channel_scope": "all_messages",
            "policy_authority_enabled": True,
        }})
        assert r.status_code == 200, r.text
        td = r.json()["details"]
        assert td["allowed_channels"] == ["Compliance"]
        assert td["personal_dm_allowed"] is False
        assert td["channel_scope"] == "group_and_channels_only"
        assert td["policy_authority_enabled"] is False
        assert td["client_training_allowed"] is False

        # Official-email boundary is also immutable from the management UI/API.
        r = client.patch("/api/integrations/outlook/policy", headers=h, json={"config": {
            "official_only": False,
            "allowed_sender_roles": ["Product Owner"],
        }})
        assert r.status_code == 200, r.text
        od = r.json()["details"]
        assert od["official_only"] is True
        assert od["allowed_sender_roles"] == ["Product Owner"]
        assert od["client_training_allowed"] is False


def test_allowed_teams_group_list_actually_changes_runtime_retrieval():
    with client:
        h = auth(); reset(h)
        # Seed Teams evidence is in "Operations Policy group". Narrowing to an unrelated group
        # must remove it from the governed answer's eligible source mix on the very next request.
        r = client.patch("/api/integrations/teams/policy", headers=h, json={"config": {
            "allowed_channels": ["Compliance Only"],
        }})
        assert r.status_code == 200, r.text
        ans = client.post("/api/memory/answer", headers=h, json={
            "question": "Can gig workers use bank statements as income evidence?",
            "preview_role": "manager",
        }).json()
        assert ans["management_status"] == "GOVERNED_ANSWER"
        assert all("teams" not in str(x.get("source", "")).lower() for x in ans.get("source_mix", []))
        assert all("teams" not in str(x.get("source", "")).lower() for x in ans.get("retrieval_matches", []))
        assert ans["primary_source"]["source"] == "Outlook Approval"
        reset(h)


def test_customer_export_security_is_server_side_and_audited():
    with client:
        manager = auth(); reset(manager)
        ok = client.post("/api/cases/export.csv", headers=manager, json={
            "mode": "masked", "reason": "Lecturer security demonstration"
        })
        assert ok.status_code == 200, ok.text
        assert ok.headers["x-juristwin-export-mode"] == "masked"
        assert "MASKED" in ok.text

        blocked = client.post("/api/cases/export.csv", headers=manager, json={
            "mode": "full", "reason": "Lecturer restricted export test"
        })
        assert blocked.status_code == 403

        overview = client.get("/api/system/security-overview", headers=manager).json()
        events = [x["action"] for x in overview["audit"]]
        assert "CUSTOMER_EXPORT_AUTHORIZED" in events
        assert "CUSTOMER_EXPORT_BLOCKED" in events


def test_static_ui_exposes_lecturer_controls_in_manager_language_and_large_text():
    with client:
        h = auth(); reset(h)
        html = client.get("/finals").text
        js = client.get("/static/sentinel.js?v=6.0.0").text
        css = client.get("/static/sentinel.css?v=6.0.0").text
        assert "sentinel.css?v=6.0.0" in html and "sentinel.js?v=6.0.0" in html
        assert "Management Controls" in js
        assert "ORIGINAL PROTOTYPE" in js and "LIVE PROOF" in js
        assert "HOW SOURCES WERE FOUND" in js
        assert "APPROVED GROUPS / CHANNELS" in js
        assert "Private DMs" in js
        assert "live-source-monitor" in css
        assert "control-upgrade-card" in css
        assert "font-size:14px" in css or "font-size: 14px" in css


def test_governance_case_cohort_is_ready_for_publish_demo_after_reset():
    with client:
        h = auth(); reset(h)
        d = client.get("/api/dashboard", headers=h).json()
        assert d["metrics"]["active_cases"] == 128
        rollout = client.get("/api/assurance/rollout-plan/CF-INCOME-001", headers=h).json()
        assert rollout["affected_cases"] == 27
        assert sum(x["case_count"] for x in rollout["waves"]) == 27
