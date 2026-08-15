from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'app' / 'static'


def login():
    r=client.post('/api/auth/login',json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
    assert r.status_code==200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def test_latest_pitch_deck_core_features_and_exact_final_flow_are_in_ui():
    js=(STATIC/'sentinel.js').read_text(encoding='utf-8')
    required=[
        'Secure Enterprise Memory','Living Decision Digital Twin','White-Box Future Simulator',
        'AI Bodyguard + Decision Ledger','Manager · Full evidence','Officer · Assigned cases','Intern · Redacted',
        'Take No Action','Update the FSD Only','Align the Complete Process',
        'Review activity','Revoke access','Restore version',
        'Connect','Expose','Simulate','Recommend','Approve','Protect',
        'Chatbots','Sentinel','PILOT TARGETS','COMMERCIAL PATH'
    ]
    for text in required:
        assert text in js
    for v4 in ['Progressive Rollout','Decision Replay','HMAC-SHA256','Attack Sentinel','Decision Assurance']:
        assert v4 in js


def test_demo_story_and_propagation_match_latest_pitch_operating_model():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        story=client.get('/api/demo/story',headers=h).json()
        assert [x['key'] for x in story['steps']] == ['CONNECT','EXPOSE','SIMULATE','RECOMMEND','APPROVE','PROTECT']
        assert story['operating_impact']=={
            'applications_affected':27,'rejected_cases_flagged':1,'qa_tests_updated':8,
            'documents_superseded':3,'officers_notified':4,
        }
        sim=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        approval=client.post(f"/api/approvals/simulation/{sim['sim_ref']}/submit",headers=h,json={'selected_option':'C'}).json()
        result=client.post(f"/api/approvals/{approval['approval_ref']}/approve",headers=h,json={'comments':'pitch alignment test'}).json()
        assert result['decision_contract']['affected']['applications']==27
        assert result['decision_contract']['affected']['rejected_cases']==1
        # Decision contract directly tracks two policy documents; operating propagation supersedes three total docs including training guidance.
        assert result['decision_contract']['affected']['documents']==2
        assert result['propagation']=={'cases':27,'rejected_cases':1,'qa_tests':8,'documents':3,'officers_notified':4}


def test_role_preview_and_v4_assurance_endpoints_remain_live():
    with client:
        h=login(); client.post('/api/demo/reset',headers=h)
        manager=client.post('/api/memory/search',headers=h,json={'query':'bank statement','limit':8,'filters':{},'preview_role':'manager'}).json()
        intern=client.post('/api/memory/search',headers=h,json={'query':'bank statement','limit':8,'filters':{},'preview_role':'intern'}).json()
        assert manager['role']=='manager' and intern['role']=='intern'
        assert any(x.get('body')=='[REDACTED BY SENTINEL SHIELD]' for x in intern['results'])
        rollout=client.get('/api/assurance/rollout-plan/CF-INCOME-001',headers=h).json()
        assert [w['name'] for w in rollout['waves']]==['CANARY','CONTROLLED','FULL']
        pack=client.get('/api/assurance/proof-pack',headers=h).json()
        assert pack['proof']['signature_algorithm']=='HMAC-SHA256'
        assert pack['ledger']['verified'] is True
