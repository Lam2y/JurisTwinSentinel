from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def login(email='operations@regulatedbank.com'):
    r=client.post('/api/auth/login',json={'email':email,'password':'Finals2026!'})
    assert r.status_code==200, r.text
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def test_v30_policy_atoms_and_bfs_impact_are_explainable():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        r=client.post('/api/live/challenge',headers=h,json={
            'source':'Judge handwritten instruction',
            'title':'Unexpected policy override',
            'body':'Effective immediately, bank statements are no longer accepted as income proof. Officers must request payslips from gig workers.',
            'authority':'Judge supplied evidence','authority_level':2,
        })
        assert r.status_code==200, r.text
        d=r.json(); p=d['analysis']['policy_atoms']
        assert d['verdict']=='CONTRADICTION'
        assert p['reasoning']['collision'] is True
        assert any(x['type']=='MODALITY_COLLISION' for x in p['reasoning']['collisions'])
        assert any(x['object']=='BANK_STATEMENT' and x['modality']=='PROHIBITED' for x in p['incoming'])
        impact=client.get(f"/api/live/challenges/{d['challenge_ref']}/impact",headers=h)
        assert impact.status_code==200
        i=impact.json()
        assert i['algorithm'].startswith('Breadth-first')
        assert i['affected_cases']==27
        assert len(i['sample_paths'])>=1
        assert i['sample_paths'][0]['path'][0]['type']=='policy'


def test_v30_real_file_evidence_gateway_and_invalid_json_guard():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        r=client.post('/api/live/evidence-drop',headers=h,json={
            'filename':'judge-policy.eml','mime_type':'message/rfc822',
            'content':'From: ops@example.test\nSubject: New income rule\n\nBank statements are not accepted. Gig workers must submit payslips.',
            'authority':'External operations lead','authority_level':3,'sensitivity':'internal',
        })
        assert r.status_code==200, r.text
        d=r.json()
        assert d['file_ingestion']['filename']=='judge-policy.eml'
        assert d['file_ingestion']['bytes']>0
        assert d['verdict']=='CONTRADICTION'
        assert len(d['analysis']['provenance']['content_sha256'])==64

        bad=client.post('/api/live/evidence-drop',headers=h,json={
            'filename':'broken.json','content':'{"policy": bad json}',
        })
        assert bad.status_code==422
        assert 'malformed' in bad.json()['detail'].lower()

        unsupported=client.post('/api/live/evidence-drop',headers=h,json={
            'filename':'malware.exe','content':'this is not an allowed evidence type',
        })
        assert unsupported.status_code==415


def test_v30_adversarial_harness_proves_safe_state():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        r=client.post('/api/live/red-team',headers=h,json={})
        assert r.status_code==200, r.text
        d=r.json()
        assert d['status']=='HARDENED'
        assert d['score']==100
        assert d['passed']==d['total']>=8
        assert d['state_mutations_persisted']==0
        assert d['canonical_decisions_modified']==0
        assert all(t['passed'] for t in d['tests'])


def test_v30_readiness_proves_reasoner_and_impact_engine():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        r=client.get('/api/system/readiness',headers=h)
        assert r.status_code==200
        d=r.json()
        assert d['status']=='READY'
        keys={x['key'] for x in d['checks'] if x['ok']}
        assert {'reasoner','impact','challenge','ledger','rbac','shields'} <= keys


def test_v30_signed_realtime_webhook_auth_and_replay_protection():
    import hashlib, hmac
    from app.core.config import get_settings
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        payload={
            'event_id':'evt-finals-001','source':'External Policy Bus','title':'Realtime income-policy event',
            'body':'Bank statements are not accepted as income evidence. Gig workers must submit payslips.',
            'authority':'External ops lead','authority_level':3,'sensitivity':'internal',
        }
        bad=client.post('/api/live/webhook',json=payload,headers={'X-JurisTwin-Signature':'forged'})
        assert bad.status_code==401
        material=f"{payload['event_id']}|{payload['body']}".encode()
        sig=hmac.new(get_settings().WEBHOOK_SECRET.encode(),material,hashlib.sha256).hexdigest()
        r=client.post('/api/live/webhook',json=payload,headers={'X-JurisTwin-Signature':sig})
        assert r.status_code==200, r.text
        d=r.json(); assert d['connector']['authenticated'] is True
        assert d['connector']['network_ingress']=='real HTTP POST'
        assert d['verdict']=='CONTRADICTION'
        replay=client.post('/api/live/webhook',json=payload,headers={'X-JurisTwin-Signature':sig})
        assert replay.status_code==200
        assert replay.json()['status']=='DUPLICATE_IGNORED'
        assert replay.json()['idempotent'] is True


def test_v30_digital_twin_emits_robust_decision_certificate():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        sim=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        cert=sim['analysis']['decision_certificate']
        assert sim['analysis']['engine'].endswith('v3')
        assert cert['recommended_option']==sim['recommended_option']
        assert cert['pareto_optimal'] is True
        assert cert['recommended_option'] in cert['pareto_frontier']
        assert 0 <= cert['worst_case_fit_p10'] <= 100
        assert cert['status'] in {'ROBUST','REVIEW'}
