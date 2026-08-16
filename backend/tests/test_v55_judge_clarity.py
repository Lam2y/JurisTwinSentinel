from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
_TOKEN = None


def login():
    global _TOKEN
    if _TOKEN:
        return {'Authorization': f'Bearer {_TOKEN}'}
    r = client.post('/api/auth/login', json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
    assert r.status_code == 200, r.text
    _TOKEN = r.json()['access_token']
    return {'Authorization': f'Bearer {_TOKEN}'}


def reset(h):
    assert client.post('/api/demo/reset', headers=h).status_code == 200


def test_seeded_conflicts_explain_exact_messages_authority_and_customer_meaning():
    with client:
        h=login(); reset(h)
        conflicts={x['conflict_ref']:x for x in client.get('/api/conflicts',headers=h).json()}
        income=conflicts['CF-INCOME-001']['plain_explanation']
        assert 'bank statements' in income['headline'].lower()
        assert 'payslips' in income['headline'].lower()
        assert income['canonical']['source']=='Outlook Approval'
        assert 'bank statements may be accepted' in income['canonical']['message'].lower()
        messages=' '.join(x['message'].lower() for x in income['conflicting_evidence'])
        assert 'payslips' in messages
        assert 'two different answers' in income['why_it_matters'].lower()
        assert 'product owner' in income['why_canonical_wins'].lower()
        assert '27' in income['customer_impact']

        restructure=conflicts['CF-RESTRUCTURE-002']['plain_explanation']
        assert '60' in restructure['headline'] and '70' in restructure['headline']
        assert restructure['canonical']['authority']=='Risk Committee'

        notify=conflicts['CF-NOTIFY-003']['plain_explanation']
        assert 'business days' in notify['headline'].lower()
        assert 'calendar days' in notify['headline'].lower()


def test_twin_recommendation_has_nontechnical_why_best_and_why_not_alternatives():
    with client:
        h=login(); reset(h)
        sim=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        plain=sim['analysis']['plain_language']
        assert sim['recommended_option']=='C'
        assert 'organisation' in plain['headline'].lower()
        assert len(plain['reasons'])==3
        assert 'one document' in plain['why_not_b'].lower()
        assert 'policy, people and workflow' in plain['why_recommended'].lower()
        out=plain['customer_outcome']
        assert out['delay_before_days']==4.2
        assert out['delay_after_days']==1.1
        assert out['complaint_before_pct']>out['complaint_after_pct']
        assert out['alignment_after_pct']>out['alignment_before_pct']
        assert plain['technical_proof_available'] is True


def test_live_judge_challenge_quotes_both_messages_and_explains_which_source_wins():
    with client:
        h=login(); reset(h)
        body='Effective immediately, bank statements are no longer accepted. Gig workers must provide payslips.'
        d=client.post('/api/live/challenge',headers=h,json={
            'source':'Judge Live Input','title':'Unseen policy evidence','body':body,
            'authority':'Judge supplied evidence','authority_level':2,'sensitivity':'internal'
        }).json()
        assert d['verdict']=='CONTRADICTION'
        plain=d['analysis']['plain_language']
        assert plain['what_incoming_says']==body
        assert 'bank statements may be accepted' in plain['what_canonical_says'].lower()
        assert plain['canonical_source']=='Outlook Approval'
        assert 'product owner' in plain['which_source_wins'].lower()
        assert '27' in plain['customer_impact']
        assert plain['why_conflict']


def test_frontend_surfaces_plain_explanations_before_technical_proof():
    root=Path(__file__).resolve().parents[2]
    js=(root/'frontend'/'src'/'sentinel.js').read_text(encoding='utf-8')
    css=(root/'frontend'/'src'/'sentinel.css').read_text(encoding='utf-8')
    required=[
        'WHY IS THIS A CONFLICT?', 'WHICH SOURCE WINS — AND WHY', 'See all',
        'WHY OPTION ${esc(sim.recommended_option||\'C\')} IS THE BEST CHOICE',
        'Why not A?', 'Why not B?', 'Why C?', 'See technical proof',
        'YOUR MESSAGE', 'APPROVED SOURCE', 'WHY THEY CONFLICT', 'CUSTOMER IMPACT',
    ]
    for text in required:
        assert text in js, text
    assert 'showConflictMessages' in js
    assert 'showTwinTechnicalProof' in js
    assert '.conflict-plain' in css
    assert '.recommendation-plain' in css
    assert '.judge-message-compare' in css
