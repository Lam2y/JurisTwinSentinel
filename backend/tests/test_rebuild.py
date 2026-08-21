import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.main import app
from app.db.database import Base, SessionLocal, engine
from app.db.seed import seed_database
from app.db.models import Evidence, KnowledgeGap


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    with TestClient(app) as c:
        yield c


def login(client, email):
    r = client.post('/api/auth/login', json={'email': email, 'password': 'Finals2026!'})
    assert r.status_code == 200
    return {'Authorization': f"Bearer {r.json()['access_token']}"}


def test_known_answer_hides_contradictions(client):
    h = login(client, 'user@juristech.com')
    r = client.post('/api/ask', headers=h, json={'question': 'Can gig workers use bank statements as income evidence?'})
    assert r.status_code == 200
    body = r.json()
    assert body['status'] == 'ANSWERED'
    assert len(body['sources']) == 1
    assert body['sources'][0]['evidence_ref'] == 'EV-INCOME-PO-001'
    payload = str(body).lower()
    assert 'ev-income-fsd-003' not in payload
    assert 'continue requesting payslips' not in payload


def test_unknown_question_creates_gap_and_semantic_duplicate_collapses(client):
    h = login(client, 'user@juristech.com')
    q1 = 'Do QR merchant settlement records count as income proof for self-employed applicants?'
    q2 = 'Do QR merchant settlement records count as proof of income for self employed applicants?'
    assert client.post('/api/ask', headers=h, json={'question': q1}).json()['status'] == 'REVIEW_PENDING'
    assert client.post('/api/ask', headers=h, json={'question': q2}).json()['status'] == 'REVIEW_PENDING'
    a = login(client, 'superadmin@juristech.com')
    gaps = client.get('/api/admin/gaps?status=open', headers=a).json()
    assert len(gaps) == 1
    assert gaps[0]['occurrence_count'] == 2


def test_superadmin_analysis_separates_support_and_conflict(client):
    u = login(client, 'user@juristech.com')
    a = login(client, 'superadmin@juristech.com')
    client.post('/api/ask', headers=u, json={'question': 'Do QR merchant settlement records count as income proof for self-employed applicants?'})
    gap = client.get('/api/admin/gaps?status=open', headers=a).json()[0]
    detail = client.get(f"/api/admin/gaps/{gap['gap_ref']}", headers=a).json()
    analysis = detail['analysis']
    assert analysis['supporting']
    assert analysis['conflicting']
    assert analysis['why_sources_disagree']
    assert 'Logistic Regression' in analysis['technical_trace']['domain_model']


def test_publish_then_paraphrase_reuses_governed_pattern(client):
    u = login(client, 'user@juristech.com')
    a = login(client, 'superadmin@juristech.com')
    q = 'Do QR merchant settlement records count as income proof for self-employed applicants?'
    client.post('/api/ask', headers=u, json={'question': q})
    gap = client.get('/api/admin/gaps?status=open', headers=a).json()[0]
    detail = client.get(f"/api/admin/gaps/{gap['gap_ref']}", headers=a).json()
    refs = []
    answer = 'For now, QR merchant settlement records are not accepted as a direct substitute for approved income evidence. Escalate them for manual verification.'
    p = client.post(f"/api/admin/gaps/{gap['gap_ref']}/publish", headers=a, json={
        'answer': answer,
        'source_refs': refs,
        'uncertainty_note': 'Unsupported until formally approved.',
        'match_threshold': 0.58,
    })
    assert p.status_code == 200
    r = client.post('/api/ask', headers=u, json={'question': 'Can self-employed applicants use QR merchant settlement records as proof of income?'})
    assert r.status_code == 200
    assert r.json()['status'] == 'ANSWERED'
    assert r.json()['handled_by'] == 'governed_pattern_memory'
    assert r.json()['answer'] == answer


def test_regular_user_cannot_access_admin(client):
    h = login(client, 'user@juristech.com')
    assert client.get('/api/admin/overview', headers=h).status_code == 403
    assert client.get('/api/governance/privacy', headers=h).status_code == 403


def test_pii_is_masked_before_gap_persistence(client):
    u = login(client, 'user@juristech.com')
    a = login(client, 'superadmin@juristech.com')
    q = 'Can you approve a new benefit for alice@example.com account 123456789012345?'
    client.post('/api/ask', headers=u, json={'question': q})
    gaps = client.get('/api/admin/gaps?status=open', headers=a).json()
    stored = gaps[0]['question']
    assert 'alice@example.com' not in stored
    assert '123456789012345' not in stored
    assert '[EMAIL REDACTED]' in stored
    assert '[ACCOUNT REDACTED]' in stored


def test_bad_input_and_readiness(client):
    u = login(client, 'user@juristech.com')
    a = login(client, 'superadmin@juristech.com')
    assert client.post('/api/ask', headers=u, json={'question': 'x'}).status_code == 422
    readiness = client.get('/api/governance/readiness', headers=a)
    assert readiness.status_code == 200
    assert readiness.json()['status'] == 'READY'
    assert readiness.json()['score'] == 100
