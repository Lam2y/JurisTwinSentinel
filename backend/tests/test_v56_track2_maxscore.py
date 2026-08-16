from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db.database import SessionLocal
from app.db.models import Integration, User
from app.services.common import dumps

client=TestClient(app)

def auth(email='operations@regulatedbank.com'):
    r=client.post('/api/auth/login',json={'email':email,'password':'Finals2026!'})
    assert r.status_code==200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}

def test_track2_answer_is_multi_source_and_first_class():
    h=auth(); client.post('/api/demo/reset',headers=h)
    r=client.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'})
    assert r.status_code==200
    d=r.json()
    assert d['status']=='CONFLICT_PRESENT'
    assert d['synthesis']['sources_considered']>=3
    sources={x['source'] for x in d['source_mix']}
    assert 'Outlook Approval' in sources
    assert {'FSD','Teams Message'} & sources
    assert 'fake consensus' in d['synthesis']['summary'].lower()


def test_officer_access_is_assignment_only_no_flagship_exception():
    h=auth()
    db=SessionLocal()
    try:
        officer=db.execute(select(User).where(User.email=='officer@regulatedbank.com')).scalar_one()
        original=officer.assigned_case_refs
        officer.assigned_case_refs=dumps([]); db.commit()
        oh=auth('officer@regulatedbank.com')
        r=client.post('/api/memory/search',headers=oh,json={'query':'bank statement','limit':10,'filters':{}})
        assert r.status_code==200
        matched=[x for x in r.json()['results'] if x.get('case_ref')=='JT-2026-084']
        assert matched and all('[REDACTED' in (x.get('body') or '') for x in matched)
        officer.assigned_case_refs=original;db.commit()
    finally: db.close()


def test_semantic_connector_truthfully_names_runtime():
    h=auth();client.post('/api/demo/reset',headers=h)
    items=client.get('/api/integrations',headers=h).json()
    vector=next(x for x in items if x['key']=='vector')
    assert vector['name']=='Local Semantic Retrieval Index'
    assert vector['details']['engine']=='BM25 + cosine'
    assert vector['details']['pilot_target']=='ChromaDB'


def test_overview_surfaces_verified_answer_above_fold_contract():
    html=client.get('/finals').text
    js=client.get('/static/sentinel.js?v=5.7.0').text
    assert 'Ask JurisTwin' in js
    assert 'PLAIN-LANGUAGE ENTERPRISE MEMORY' in js
    assert 'overviewQuestion' in js and 'overviewAsk' in js
    assert 'Manager · full evidence' in js and 'Intern · redacted' in js
    assert 'What JurisTwin checked' in js
    assert '/static/sentinel.js?v=5.7.0' in html


def test_twin_is_explicitly_process_optimisation():
    js=client.get('/static/sentinel.js?v=5.7.0').text
    assert 'PROCESS OPTIMISATION' in js
    assert 'Run process optimisation' in js
