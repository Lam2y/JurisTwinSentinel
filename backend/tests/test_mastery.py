import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.database import Base, SessionLocal, engine
from app.db.seed import seed_database
from app.db.models import Evidence, EvidenceOrigin, KnowledgeGap, ResolutionPattern
from app.services.ledger import verify_chain


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
    assert r.status_code == 200, r.text
    return {'Authorization': f"Bearer {r.json()['access_token']}"}


def test_runtime_evidence_ingestion_is_quarantined_and_does_not_change_user_answer(client):
    admin = login(client, 'superadmin@juristech.com')
    user = login(client, 'user@juristech.com')
    ingest = client.post('/api/admin/evidence/ingest', headers=admin, json={
        'source': 'Live SOP update',
        'title': 'Conflicting income evidence note',
        'body': 'Bank statements are prohibited for gig workers and payslips are compulsory.',
        'rule_key': 'income_document_rule',
        'authority': 'Operations Manager',
        'authority_level': 4,
        'sensitivity': 'internal',
    })
    assert ingest.status_code == 200, ingest.text
    body = ingest.json()
    assert body['quarantined'] is True
    assert body['approval_state'] == 'candidate_only'
    assert body['collisions']

    answer = client.post('/api/ask', headers=user, json={'question': 'Can gig workers use bank statements as income evidence?'})
    assert answer.status_code == 200
    data = answer.json()
    assert data['status'] == 'ANSWERED'
    assert data['sources'][0]['evidence_ref'] == 'EV-INCOME-PO-001'
    assert body['evidence_ref'] not in str(data)


def test_evidence_ingestion_rejects_personal_identifiers(client):
    admin = login(client, 'superadmin@juristech.com')
    r = client.post('/api/admin/evidence/ingest', headers=admin, json={
        'source': 'Email', 'title': 'Unsafe paste',
        'body': 'For jane@example.com account 123456789012345, bank statements are allowed.',
        'rule_key': 'income_document_rule', 'authority': 'Officer', 'authority_level': 2,
    })
    assert r.status_code == 422
    assert 'Redact personal data' in r.json()['detail']


def test_negative_feedback_escalates_governed_answer(client):
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    answer = client.post('/api/ask', headers=user, json={'question': 'What is the customer notification deadline?'}).json()
    assert answer['status'] == 'ANSWERED'
    feedback = client.post('/api/ask/feedback', headers=user, json={'interaction_ref': answer['interaction_ref'], 'helpful': False})
    assert feedback.status_code == 200
    assert feedback.json()['escalated'] is True
    gaps = client.get('/api/admin/gaps?status=open', headers=admin).json()
    assert any(g['reason'] == 'USER_FEEDBACK_ESCALATION' for g in gaps)


def test_user_cannot_rate_another_users_interaction(client):
    admin = login(client, 'superadmin@juristech.com')
    user = login(client, 'user@juristech.com')
    admin_answer = client.post('/api/ask', headers=admin, json={'question': 'What is the loan restructuring approval threshold?'}).json()
    r = client.post('/api/ask/feedback', headers=user, json={'interaction_ref': admin_answer['interaction_ref'], 'helpful': True})
    assert r.status_code == 403


def test_live_metrics_are_based_on_real_interactions(client):
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    a1 = client.post('/api/ask', headers=user, json={'question': 'What is the loan restructuring approval threshold?'}).json()
    client.post('/api/ask/feedback', headers=user, json={'interaction_ref': a1['interaction_ref'], 'helpful': True})
    client.post('/api/ask', headers=user, json={'question': 'Can QR marketplace payout screenshots be accepted as income proof?'}).json()
    metrics = client.get('/api/admin/metrics', headers=admin)
    assert metrics.status_code == 200
    v = metrics.json()['live_validation']
    assert v['interactions'] == 2
    assert v['answered'] == 1
    assert v['review_pending'] == 1
    assert v['helpful_count'] == 1
    assert v['median_latency_ms'] >= 0


def test_publish_rejects_unapproved_or_conflicting_source_reference(client):
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    q = 'Do QR merchant settlement records count as income proof for self-employed applicants?'
    client.post('/api/ask', headers=user, json={'question': q})
    gap = client.get('/api/admin/gaps?status=open', headers=admin).json()[0]
    ing = client.post('/api/admin/evidence/ingest', headers=admin, json={
        'source': 'Merchant Ops Note', 'title': 'QR settlements',
        'body': 'QR merchant settlement records may be reviewed as supplemental income evidence.',
        'rule_key': 'income_document_rule', 'authority': 'Operations', 'authority_level': 2,
    }).json()
    r = client.post(f"/api/admin/gaps/{gap['gap_ref']}/publish", headers=admin, json={
        'answer': 'Use QR settlement records only for manual review.',
        'source_refs': [ing['evidence_ref']],
        'uncertainty_note': 'Manual review only.',
        'match_threshold': 0.62,
    })
    assert r.status_code == 422
    assert 'Only current approved supporting sources' in r.json()['detail']


def test_manual_publish_without_sources_requires_uncertainty_note(client):
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    client.post('/api/ask', headers=user, json={'question': 'Can QR settlement screenshots replace payslips for freelancers?'})
    gap = client.get('/api/admin/gaps?status=open', headers=admin).json()[0]
    r = client.post(f"/api/admin/gaps/{gap['gap_ref']}/publish", headers=admin, json={
        'answer': 'Escalate for manual verification.', 'source_refs': [], 'uncertainty_note': None, 'match_threshold': 0.62,
    })
    assert r.status_code == 422
    assert 'uncertainty / exception note' in r.json()['detail']


def test_decision_memory_can_be_rolled_back_and_gap_reopens(client):
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    q = 'Do QR merchant settlement records count as income proof for self-employed applicants?'
    client.post('/api/ask', headers=user, json={'question': q})
    gap = client.get('/api/admin/gaps?status=open', headers=admin).json()[0]
    published = client.post(f"/api/admin/gaps/{gap['gap_ref']}/publish", headers=admin, json={
        'answer': 'For now, QR merchant settlement records require manual verification.',
        'source_refs': [],
        'uncertainty_note': 'No approved source explicitly covers QR merchant settlement records.',
        'match_threshold': 0.58,
    })
    assert published.status_code == 200
    ref = published.json()['resolution_ref']
    reused = client.post('/api/ask', headers=user, json={'question': 'Can self-employed applicants use QR merchant settlement records as proof of income?'}).json()
    assert reused['handled_by'] == 'governed_pattern_memory'

    rolled = client.patch(f'/api/admin/patterns/{ref}', headers=admin, json={'active': False, 'reason': 'Policy owner requested review'})
    assert rolled.status_code == 200
    assert rolled.json()['active'] is False
    assert rolled.json()['reopened_gap'] == gap['gap_ref']
    with SessionLocal() as db:
        assert db.execute(select(ResolutionPattern).where(ResolutionPattern.resolution_ref == ref)).scalar_one().active is False
        assert db.execute(select(KnowledgeGap).where(KnowledgeGap.gap_ref == gap['gap_ref'])).scalar_one().status == 'open'


def test_two_current_approved_sources_disagree_and_system_fails_closed(client):
    user = login(client, 'user@juristech.com')
    with SessionLocal() as db:
        db.add(Evidence(
            evidence_ref='EV-SPLIT-001', source='Second Approved Policy', title='Conflicting approval',
            body='Bank statements are prohibited for gig workers and payslips are compulsory.',
            rule_key='income_document_rule', claim='bank_statement_prohibited', authority='Policy Committee',
            authority_level=5, version='v5.0', status='active', sensitivity='internal', approved=True, superseded=False,
        ))
        db.add(EvidenceOrigin(
            evidence_ref='EV-SPLIT-001', connector='Policy Repository', source_scope='formal_approval',
            collection_reason='Approved conflicting policy used to test canonical split-brain handling.',
            private_message_excluded=True, relevance_score=1.0,
        ))
        db.commit()
    r = client.post('/api/ask', headers=user, json={'question': 'Can gig workers use bank statements as income evidence?'})
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'REVIEW_PENDING'
    assert data['handled_by'] == 'canonical_conflict_gate'
    assert data['sources'] == []
    assert 'won’t choose' in data['answer']


def test_resilience_self_test_is_live_and_persisted(client):
    admin = login(client, 'superadmin@juristech.com')
    r = client.post('/api/governance/resilience-test', headers=admin)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['status'] == 'PASS'
    assert data['score'] == 100
    assert all(x['ok'] for x in data['checks'])
    history = client.get('/api/governance/resilience-history', headers=admin).json()
    assert history[0]['run_ref'] == data['run_ref']


def test_compliance_and_risk_evidence_are_admin_only(client):
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    assert client.get('/api/governance/compliance', headers=user).status_code == 403
    c = client.get('/api/governance/compliance', headers=admin)
    r = client.get('/api/governance/risk-register', headers=admin)
    assert c.status_code == 200 and r.status_code == 200
    assert len(c.json()['mappings']) >= 4
    assert r.json()['controlled'] == r.json()['total']


def test_hmac_audit_chain_detects_database_tampering(client):
    admin = login(client, 'superadmin@juristech.com')
    client.post('/api/governance/resilience-test', headers=admin)
    with SessionLocal() as db:
        assert verify_chain(db)['ok'] is True
        from app.db.models import LedgerEntry
        row = db.execute(select(LedgerEntry).order_by(LedgerEntry.id).limit(1)).scalar_one()
        row.payload_json = '{"tampered":true}'
        db.commit()
    with SessionLocal() as db:
        check = verify_chain(db)
        assert check['ok'] is False
        assert check['errors']


def test_security_headers_are_present(client):
    r = client.get('/api/governance/health')
    assert r.status_code == 200
    assert r.headers['x-content-type-options'] == 'nosniff'
    assert r.headers['x-frame-options'] == 'DENY'
    assert "frame-ancestors 'none'" in r.headers['content-security-policy']
    assert r.headers['cache-control'] == 'no-store'


def test_technical_proof_states_limits_and_not_hardcoded_evidence(client):
    admin = login(client, 'superadmin@juristech.com')
    r = client.get('/api/governance/technical-proof', headers=admin)
    assert r.status_code == 200
    body = r.json()
    assert len(body['not_hardcoded_proofs']) >= 5
    assert len(body['limits']) >= 4
    assert body['model_card']['governance']['model_can_publish'] is False


def test_resolved_review_retention_is_enforced(client):
    from datetime import timedelta
    from app.services.common import utcnow
    from app.services.retention import apply_resolved_gap_retention, expired_resolved_gap_count

    with SessionLocal() as db:
        gap = KnowledgeGap(
            gap_ref='KG-OLD-RETENTION', fingerprint='f'*64,
            question='Old resolved review item', normalized_question='old resolved review item',
            predicted_domain='income_document_rule', domain_confidence=0.8,
            top_evidence_similarity=0.4, reason='TEST', status='resolved', occurrence_count=1,
            first_seen_at=utcnow()-timedelta(days=60), last_seen_at=utcnow()-timedelta(days=60),
            resolved_at=utcnow()-timedelta(days=45), resolution_ref='RES-ARCHIVED',
        )
        db.add(gap)
        db.commit()
        assert expired_resolved_gap_count(db) == 1
        deleted = apply_resolved_gap_retention(db, actor='test-retention')
        assert deleted == 1
        assert expired_resolved_gap_count(db) == 0
        assert db.execute(select(KnowledgeGap).where(KnowledgeGap.gap_ref == 'KG-OLD-RETENTION')).scalar_one_or_none() is None
        assert verify_chain(db)['ok'] is True


def test_final_response_lineage_gate_rejects_misleading_source_attribution(client):
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    client.post('/api/ask', headers=user, json={'question': 'Do QR merchant settlement records count as income proof for self-employed applicants?'})
    gap = client.get('/api/admin/gaps?status=open', headers=admin).json()[0]
    r = client.post(f"/api/admin/gaps/{gap['gap_ref']}/publish", headers=admin, json={
        'answer': 'Bank statements are prohibited for gig workers and payslips are compulsory.',
        'source_refs': ['EV-INCOME-PO-001'],
        'uncertainty_note': 'Testing source consistency.',
        'match_threshold': 0.62,
    })
    assert r.status_code == 422
    assert 'conflicts with the final response wording' in r.json()['detail']


def test_frontend_contains_accessibility_and_reduced_motion_guards(client):
    from pathlib import Path
    static_dir = Path(__file__).resolve().parents[1] / 'app' / 'static'
    html = (static_dir / 'finals.html').read_text(encoding='utf-8')
    css = (static_dir / 'app.css').read_text(encoding='utf-8')
    assert 'class="skip-link"' in html
    assert 'aria-live="polite"' in html
    assert 'prefers-reduced-motion:reduce' in css
    assert 'focus-visible' in css
    assert 'prefers-contrast:more' in css


def test_oversized_request_is_rejected_at_api_boundary(client):
    oversized = 'x' * (1024 * 1024 + 100)
    r = client.post('/api/ask', content=oversized, headers={'content-type': 'application/json'})
    assert r.status_code == 413
    assert 'too large' in r.json()['detail'].lower()


def test_private_messages_are_blocked_and_never_persisted_as_evidence(client):
    admin = login(client, 'superadmin@juristech.com')
    r = client.post('/api/admin/evidence/ingest', headers=admin, json={
        'source': 'Teams PM', 'title': 'Private one-to-one instruction',
        'body': 'Bank statements are prohibited for gig workers and payslips are compulsory.',
        'rule_key': 'income_document_rule', 'authority': 'Manager', 'authority_level': 3,
        'source_scope': 'private_message',
    })
    assert r.status_code == 422
    assert 'Private/direct messages' in r.json()['detail']
    with SessionLocal() as db:
        assert db.execute(select(Evidence).where(Evidence.title == 'Private one-to-one instruction')).scalar_one_or_none() is None
        assert db.execute(select(EvidenceOrigin).where(EvidenceOrigin.source_scope == 'private_message')).scalar_one_or_none() is None


def test_irrelevant_group_chat_is_rejected_before_storage(client):
    admin = login(client, 'superadmin@juristech.com')
    r = client.post('/api/admin/evidence/ingest', headers=admin, json={
        'source': 'Teams · Operations Risk', 'title': 'Lunch coordination',
        'body': 'Hi team, lunch is moved to 1pm tomorrow and the pantry order is confirmed.',
        'rule_key': 'income_document_rule', 'authority': 'Operations', 'authority_level': 2,
        'source_scope': 'group_channel',
    })
    assert r.status_code == 422
    assert 'outside the relevant policy scope' in r.json()['detail']
    with SessionLocal() as db:
        assert db.execute(select(Evidence).where(Evidence.title == 'Lunch coordination')).scalar_one_or_none() is None


def test_relevant_group_chat_is_quarantined_with_privacy_origin_metadata(client):
    admin = login(client, 'superadmin@juristech.com')
    r = client.post('/api/admin/evidence/ingest', headers=admin, json={
        'source': 'Teams · Operations Risk', 'title': 'Gig income process clarification',
        'body': 'Bank statements are prohibited for gig workers and payslips are compulsory.',
        'rule_key': 'income_document_rule', 'authority': 'Operations Manager', 'authority_level': 3,
        'source_scope': 'group_channel',
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['quarantined'] is True
    assert data['source_scope'] == 'group_channel'
    assert data['private_message_excluded'] is True
    assert data['collection_relevance'] >= 0.55
    with SessionLocal() as db:
        origin = db.execute(select(EvidenceOrigin).where(EvidenceOrigin.evidence_ref == data['evidence_ref'])).scalar_one()
        assert origin.source_scope == 'group_channel'
        assert origin.private_message_excluded is True
        assert origin.relevance_score >= 0.55


def test_encrypted_customer_export_is_superadmin_only_and_decryptable_with_passphrase(client):
    import base64, json
    from app.services.secure_exchange import decrypt_export_payload
    user = login(client, 'user@juristech.com')
    admin = login(client, 'superadmin@juristech.com')
    question = 'What is the customer notification deadline?'
    client.post('/api/ask', headers=user, json={'question': question})
    assert client.post('/api/governance/customer-export', headers=user, json={'passphrase': 'StrongPass!2026', 'include_feedback': True}).status_code == 403
    r = client.post('/api/governance/customer-export', headers=admin, json={'passphrase': 'StrongPass!2026', 'include_feedback': True})
    assert r.status_code == 200, r.text
    body = r.json()
    file_bytes = base64.b64decode(body['content_base64'])
    assert question.encode() not in file_bytes
    envelope = json.loads(file_bytes.decode())
    assert envelope['cipher'] == 'AES-256-GCM'
    plaintext = decrypt_export_payload(envelope, 'StrongPass!2026')
    assert plaintext['interactions'][0]['question_masked'] == question
    assert body['manifest']['passphrase_persisted'] is False
    assert body['manifest']['audit_txid'].startswith('JT-')


def test_system_transfer_boundary_requires_api_key_hmac_and_checksum(client):
    import base64, hashlib, json, time
    from app.core.config import get_settings
    from app.services.secure_exchange import sign_transfer_payload
    ciphertext = b'encrypted-customer-packet'
    packet = {
        'transfer_ref': 'TX-SYSTEM-001',
        'source_system': 'Core Banking Sandbox',
        'purpose': 'encrypted customer decision export',
        'cipher': 'AES-256-GCM',
        'payload_sha256': hashlib.sha256(ciphertext).hexdigest(),
        'ciphertext_b64': base64.b64encode(ciphertext).decode(),
    }
    raw = json.dumps(packet, separators=(',', ':')).encode()
    ts = str(int(time.time()))
    assert client.post('/api/integration/secure-packet', content=raw, headers={'content-type':'application/json'}).status_code == 401
    bad = client.post('/api/integration/secure-packet', content=raw, headers={
        'content-type':'application/json', 'X-JurisTwin-API-Key':'wrong', 'X-JurisTwin-Timestamp':ts,
        'X-JurisTwin-Signature':sign_transfer_payload(raw, ts),
    })
    assert bad.status_code == 401
    good = client.post('/api/integration/secure-packet', content=raw, headers={
        'content-type':'application/json', 'X-JurisTwin-API-Key':get_settings().INTEGRATION_API_KEY,
        'X-JurisTwin-Timestamp':ts, 'X-JurisTwin-Signature':sign_transfer_payload(raw, ts),
    })
    assert good.status_code == 200, good.text
    assert good.json()['plaintext_received'] is False
    assert good.json()['audit_txid'].startswith('JT-')


def test_transfer_self_test_exposes_fingerprint_not_secret(client):
    from app.core.config import get_settings
    admin = login(client, 'superadmin@juristech.com')
    r = client.post('/api/governance/transfer-self-test', headers=admin)
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'PASS'
    assert data['api_key_gate'] and data['hmac_integrity'] and data['replay_window']
    assert data['api_key_exposed_to_browser'] is False
    assert get_settings().INTEGRATION_API_KEY not in str(data)


def test_monte_carlo_decision_twin_runs_1500_scenarios_and_is_audited(client):
    admin = login(client, 'superadmin@juristech.com')
    r = client.post('/api/admin/compare/income_document_rule/simulate', headers=admin, json={
        'delay': 0.40, 'complaint': 0.35, 'alignment': 0.25,
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['scenario_count'] == 1500
    assert len(data['options']) == 3
    assert sum(x['uncertainty']['samples'] for x in data['options']) == 1500
    assert data['recommended_option'] == 'C'
    assert data['decision_certificate']['status'] == 'ROBUST'
    audit = client.get('/api/governance/audit?limit=20', headers=admin).json()['entries']
    assert any(x['action'] == 'DECISION_TWIN_RUN' for x in audit)


def test_frontend_outlines_privacy_export_transfer_audit_and_digital_twin(client):
    from pathlib import Path
    static_dir = Path(__file__).resolve().parents[1] / 'app' / 'static'
    js = (static_dir / 'app.js').read_text(encoding='utf-8')
    css = (static_dir / 'app.css').read_text(encoding='utf-8')
    for term in ['Group channel ≠ permission to collect everything', 'Generate encrypted .jtx export', 'TLS + API key + HMAC boundary', 'Audit Evidence', 'Monte Carlo Decision Digital Twin']:
        assert term in js
    for term in ['privacy-boundary-hero', 'data-security-grid', 'audit-slide', 'twin-shell']:
        assert term in css
