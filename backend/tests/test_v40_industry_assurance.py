import hashlib
import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.observability import rate_limiter

client=TestClient(app)


def login():
    r=client.post('/api/auth/login',json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
    assert r.status_code==200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def reset(h):
    r=client.post('/api/demo/reset',headers=h)
    assert r.status_code==200


def test_security_headers_runtime_telemetry_and_readiness_v4():
    with client:
        h=login(); reset(h)
        r=client.get('/api/system/health',headers=h)
        assert r.status_code==200
        assert r.headers['x-content-type-options']=='nosniff'
        assert r.headers['x-frame-options']=='DENY'
        assert r.headers['x-juristwin-governed']=='true'
        assert r.headers.get('content-security-policy')
        assert r.json()['version']=='5.7.0'
        a=client.get('/api/assurance/overview',headers=h).json()
        assert a['platform']=='JurisTwin Sentinel Championship v5.7'
        assert a['invariants']['status']=='HEALTHY'
        assert a['telemetry']['requests']>=1
        ready=client.get('/api/system/readiness',headers=h).json()
        assert ready['status']=='READY'
        assert ready['score']==100
        keys={x['key'] for x in ready['checks']}
        assert {'invariants','hardening'} <= keys


def test_governance_gate_rollout_and_proof_pack_digest():
    with client:
        h=login(); reset(h)
        sim=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        assert sim['analysis']['decision_certificate']['status']=='ROBUST'
        gate=client.get('/api/assurance/governance-gate/CF-INCOME-001',headers=h).json()
        assert gate['status']=='PASS'
        assert gate['score']==100
        rollout=client.get('/api/assurance/rollout-plan/CF-INCOME-001',headers=h).json()
        assert [w['name'] for w in rollout['waves']]==['CANARY','CONTROLLED','FULL']
        assert sum(w['case_count'] for w in rollout['waves'])==rollout['affected_cases']==27
        pack=client.get('/api/assurance/proof-pack',headers=h).json()
        digest=pack['proof']['bundle_digest']
        clone=dict(pack); clone.pop('proof',None); clone.pop('status',None)
        # service fingerprints the payload before the derived status/proof envelope is appended
        expected=hashlib.sha256(json.dumps(clone,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
        assert digest==expected
        assert len(pack['proof']['signature'])==64
        verified=client.post('/api/assurance/verify-proof',headers=h,json={'digest':digest,'signature':pack['proof']['signature']}).json()
        assert verified['valid'] is True
        forged=client.post('/api/assurance/verify-proof',headers=h,json={'digest':digest,'signature':'0'*64}).json()
        assert forged['valid'] is False
        assert pack['ledger']['verified'] is True
        assert pack['impact']['affected_cases']==27


def test_decision_replay_after_governed_publish():
    with client:
        h=login(); reset(h)
        sim=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        approval=client.post(f"/api/approvals/simulation/{sim['sim_ref']}/submit",headers=h,json={'selected_option':'C'}).json()
        approved=client.post(f"/api/approvals/{approval['approval_ref']}/approve",headers=h,json={'comments':'v4 replay test'})
        assert approved.status_code==200
        replay=client.get('/api/assurance/replay/JT-084',headers=h).json()
        assert replay['status']=='REPLAYABLE'
        assert replay['chain']['ok'] is True
        assert replay['current']['version']=='v4.1'
        labels={x['label'] for x in replay['timeline']}
        assert 'Decision Approved' in labels
        assert 'Decision Propagated' in labels


def test_v4_red_team_has_industry_invariant_checks():
    with client:
        h=login(); reset(h)
        d=client.post('/api/live/red-team',headers=h,json={}).json()
        assert d['status']=='HARDENED'
        assert d['score']==100
        assert d['passed']==d['total']>=14
        keys={x['key'] for x in d['tests']}
        assert {'invariants','progressive_delivery','proof_pack'} <= keys


def test_rate_limiter_rejects_after_window_budget():
    key='unit-test-isolated-key-v4'
    assert rate_limiter.allow(key,2,60)[0] is True
    assert rate_limiter.allow(key,2,60)[0] is True
    allowed,retry=rate_limiter.allow(key,2,60)
    assert allowed is False
    assert retry>=1
