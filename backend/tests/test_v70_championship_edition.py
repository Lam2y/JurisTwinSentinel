from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


def auth(email='operations@regulatedbank.com'):
    r=client.post('/api/auth/login',json={'email':email,'password':'Finals2026!'})
    assert r.status_code==200,r.text
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def test_v70_first_minute_role_proof_and_runtime_impact_are_visible():
    js=(ROOT/'frontend'/'src'/'sentinel.js').read_text(encoding='utf-8')
    css=(ROOT/'frontend'/'src'/'sentinel.css').read_text(encoding='utf-8')
    html=(ROOT/'frontend'/'src'/'finals.html').read_text(encoding='utf-8')
    assert 'CONFLICT DETECTED' in js
    assert 'CASES TRACED' in js
    assert 'Preview same question as Intern' in js
    assert 'Restricted evidence is redacted server-side.' in js
    assert 'Question received' in js and 'Authority resolved' in js
    assert '.first-minute-impact' in css and '.role-proof-callout' in css
    assert '/static/sentinel.js?v=7.0.0' in html


def test_answer_exposes_backend_runtime_impact_and_intern_boundary():
    with client:
        h=auth()
        assert client.post('/api/demo/reset',headers=h).status_code==200
        manager=client.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        assert manager['status']=='CONFLICT_PRESENT'
        assert manager['impact']['affected_cases']==27
        assert manager['impact']['conflict_ref']=='CF-INCOME-001'
        assert manager['runtime_trace']['sources_scoped']>=3
        assert manager['runtime_trace']['affected_cases']==27
        intern=client.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'intern'}).json()
        assert intern['status']=='RESTRICTED'
        assert any(x.get('redacted') for x in intern.get('source_mix',[]))


def test_v70_live_control_changes_source_pool_without_breaking_answer():
    with client:
        h=auth()
        client.post('/api/demo/reset',headers=h)
        before=client.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        patch=client.patch('/api/integrations/sharepoint/policy',headers=h,json={'config':{'retrieval_enabled':False}})
        assert patch.status_code==200,patch.text
        after=client.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        assert after['answer']==before['answer']
        assert after['primary_source']['source']=='Outlook Approval'
        assert all(str(x.get('source','')).lower()!='fsd' for x in after.get('source_mix',[]))
        client.post('/api/demo/reset',headers=h)


def test_v70_compare_governance_challenge_and_security_are_stage_visible():
    js=(ROOT/'frontend'/'src'/'sentinel.js').read_text(encoding='utf-8')
    css=(ROOT/'frontend'/'src'/'sentinel.css').read_text(encoding='utf-8')
    for phrase in [
        'Option B fixes one document.',
        'Option C fixes the organisation.',
        'PROCESS OPTIMISATION',
        'AI PUBLICATION AUTHORITY',
        'JUDGE CHALLENGE MODE',
        'LIVE INPUT · RECEIVED',
        'QUARANTINED',
        'LIVE BACKEND RESULT · HTTP',
        'EXPORT BLOCKED',
    ]:
        assert phrase in js
    for cls in ['.twin-stage-line','.authority-zero-stage','.challenge-verdict-stage','.security-live-result']:
        assert cls in css


def test_v70_unseen_runtime_and_backend_export_enforcement():
    with client:
        h=auth()
        client.post('/api/demo/reset',headers=h)
        challenge=client.post('/api/live/challenge',headers=h,json={
            'source':'Judge Live Input','title':'Unseen finals instruction',
            'body':'Effective immediately, bank statements are no longer accepted. Officers must request payslips from gig workers.',
            'authority':'Judge supplied evidence','authority_level':2,'sensitivity':'internal'
        })
        assert challenge.status_code==200,challenge.text
        d=challenge.json()
        assert d['verdict']=='CONTRADICTION'
        assert d['blast_radius']==27
        assert len(d['analysis'].get('stages',[]))>=5
        # Manager may take a masked export but backend denies full raw customer data for this role.
        ok=client.post('/api/cases/export.csv',headers=h,json={'mode':'masked','reason':'Finals live controlled export'})
        assert ok.status_code==200
        blocked=client.post('/api/cases/export.csv',headers=h,json={'mode':'full','reason':'Finals live restricted export test'})
        assert blocked.status_code==403
        client.post('/api/demo/reset',headers=h)
