from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def login():
    r = client.post('/api/auth/login', json={
        'email':'operations@regulatedbank.com',
        'password':'Finals2026!',
    })
    assert r.status_code == 200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def test_v20_judge_challenge_materialises_unseen_conflict_without_overwrite():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        r=client.post('/api/live/challenge',headers=h,json={
            'source':'Microsoft Teams — Live Judge Input',
            'title':'Judge supplied policy message',
            'body':'Effective immediately, bank statements are no longer accepted as standalone income proof. Officers must request payslips from gig workers.',
            'authority':'Live challenge participant',
            'authority_level':2,
            'sensitivity':'internal',
        })
        assert r.status_code==200, r.text
        d=r.json()
        assert d['verdict']=='CONTRADICTION'
        assert d['rule_key']=='income_document_rule'
        assert d['blast_radius']==27
        assert d['conflict_ref']
        assert d['status']=='quarantined'
        assert d['analysis']['decision_guard']['action'] in {'BLOCK_SILENT_OVERWRITE','HUMAN_REVIEW_BEFORE_CANONICALISATION'}
        assert d['analysis']['total_latency_ms'] >= 0
        graph=client.get(f"/api/conflicts/{d['conflict_ref']}/graph",headers=h).json()
        assert {n.get('relation') for n in graph['nodes']} >= {'approved','conflict'}
        assert client.get('/api/ledger/verify',headers=h).json()['ok'] is True


def test_v20_challenge_handles_aligned_unknown_and_invalid_inputs_safely():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        aligned=client.post('/api/live/challenge',headers=h,json={
            'source':'SharePoint — Live Judge Input',
            'title':'Aligned income guidance',
            'body':'Gig workers may submit verified bank statements as acceptable income evidence.',
            'authority':'Policy owner copy',
            'authority_level':3,
        })
        assert aligned.status_code==200
        assert aligned.json()['verdict']=='ALIGNED'
        assert aligned.json()['conflict_ref'] is None

        unknown=client.post('/api/live/challenge',headers=h,json={
            'source':'Unknown External Source',
            'title':'Unrelated operational note',
            'body':'The office cafeteria will use reusable cups for tomorrow morning service.',
            'authority':'Unknown sender',
            'authority_level':1,
        })
        assert unknown.status_code==200
        assert unknown.json()['verdict'] in {'NOVEL','NEEDS_REVIEW','ALIGNED'}

        invalid=client.post('/api/live/challenge',headers=h,json={
            'source':'X',
            'title':'No',
            'body':'bad',
        })
        assert invalid.status_code==422
        payload=invalid.json()
        assert payload['detail']=='Input rejected by Sentinel validation'
        assert payload['request_id']


def test_v20_readiness_and_twin_stress_proof():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        ready=client.get('/api/system/readiness',headers=h)
        assert ready.status_code==200
        d=ready.json()
        assert d['status']=='READY'
        assert d['score'] >= 85
        assert d['resilience']['external_ai_required'] is False

        sim=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        assert sim['analysis']['scenario_count']==1500
        assert 0 <= sim['analysis']['robustness_score'] <= 100
        assert len(sim['analysis']['sensitivity'])==6
        assert all('uncertainty' in o for o in sim['options'])
        assert sim['options'][2]['predicted_delay_days']==1.1
