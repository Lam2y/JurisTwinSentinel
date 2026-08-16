from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)


def login():
    r=client.post('/api/auth/login',json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
    assert r.status_code==200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def reset(h):
    assert client.post('/api/demo/reset',headers=h).status_code==200


def publish(h, conflict_ref):
    sim=client.post(f'/api/simulations/conflict/{conflict_ref}/run',headers=h,json={})
    assert sim.status_code==200,sim.text
    sj=sim.json()
    assert sj['recommended_option']=='C'
    assert sj['analysis']['decision_certificate']['status']=='ROBUST'
    gate=client.get(f'/api/assurance/governance-gate/{conflict_ref}',headers=h)
    assert gate.status_code==200 and gate.json()['status']=='PASS' and gate.json()['score']==100
    sub=client.post(f"/api/approvals/simulation/{sj['sim_ref']}/submit",headers=h,json={'selected_option':'C','comments':'v5.4 test'})
    assert sub.status_code==200
    approved=client.post(f"/api/approvals/{sub.json()['approval_ref']}/approve",headers=h,json={'comments':'v5.4 governed publish'})
    assert approved.status_code==200,approved.text
    return sj, approved.json()


def test_hybrid_ai_is_genuinely_learned_measured_and_governed():
    with client:
        h=login();reset(h)
        r=client.get('/api/live/ai-model',headers=h)
        assert r.status_code==200
        d=r.json(); b=d['held_out_development_benchmark']
        assert d['learned_component'] is True
        assert d['training']['samples']>=120
        assert b['domain_macro_f1']>=0.85
        assert b['stance_macro_f1']>=0.85
        assert d['governance']['model_can_publish'] is False
        assert d['governance']['model_can_canonicalise_evidence'] is False
        challenge=client.post('/api/live/challenge',headers=h,json={
            'source':'Unseen Judge Input','title':'Judge policy','body':'Effective immediately, bank statements are prohibited as income evidence and gig workers must submit payslips.','authority':'Judge evidence','authority_level':2,'sensitivity':'internal'
        }).json()
        assert challenge['verdict']=='CONTRADICTION'
        assert challenge['analysis']['hybrid_ai']['learned']['engine']
        assert challenge['analysis']['hybrid_ai']['arbitration']['engine']=='Sentinel Dual-Control Consensus v1'
        assert challenge['analysis']['agent_trace']['engine']=='Sentinel Agentic Resolution Orchestrator v1'
        assert challenge['analysis']['provenance']['canonical_mutated'] is False


def test_post_approval_assurance_never_degrades_on_the_flagship_path():
    with client:
        h=login();reset(h)
        _,approved=publish(h,'CF-INCOME-001')
        assert approved['decision_contract']['decision_ref']=='JT-084'
        inv=client.get('/api/assurance/invariants',headers=h).json()
        ready=client.get('/api/system/readiness',headers=h).json()
        overview=client.get('/api/assurance/overview',headers=h).json()
        attack=client.post('/api/live/red-team',headers=h,json={}).json()
        assert inv['status']=='HEALTHY'
        assert ready['status']=='READY' and ready['score']==100
        assert overview['status']=='OPERATIONAL'
        assert attack['status']=='HARDENED' and attack['score']==100


def test_proof_pack_verifies_live_using_the_exact_emitted_field_name():
    with client:
        h=login();reset(h)
        publish(h,'CF-INCOME-001')
        pack=client.get('/api/assurance/proof-pack?conflict_ref=CF-INCOME-001',headers=h).json()
        proof=pack['proof']
        assert pack['ai_assurance']['learned_component'] is True
        assert pack['ai_assurance']['model_can_publish'] is False
        assert pack['ai_assurance']['domain_macro_f1']>=0.85
        verified=client.post('/api/assurance/verify-proof',headers=h,json={'bundle_digest':proof['bundle_digest'],'signature':proof['signature']})
        assert verified.status_code==200
        assert verified.json()['valid'] is True


def test_all_three_seeded_conflicts_are_full_governed_workflows():
    expected={
        'CF-INCOME-001':('income_document_rule','JT-084',27),
        'CF-RESTRUCTURE-002':('loan_restructure_rule','JT-RESTRUCTURE-002',11),
        'CF-NOTIFY-003':('notification_deadline','JT-NOTIFY-003',6),
    }
    with client:
        h=login();reset(h)
        conflicts={x['conflict_ref']:x for x in client.get('/api/conflicts',headers=h).json()}
        assert set(expected)<=set(conflicts)
        for ref,(rule,decision_ref,count) in expected.items():
            graph=client.get(f'/api/conflicts/{ref}/graph',headers=h).json()
            assert len(graph['nodes'])>=4
            sim,approved=publish(h,ref)
            assert sim['analysis']['scenario_profile']==rule
            assert approved['decision_contract']['decision_ref']==decision_ref
            assert approved['propagation']['cases']==count
            replay=client.get(f'/api/assurance/replay/{decision_ref}',headers=h)
            assert replay.status_code==200 and replay.json()['status']=='REPLAYABLE'
            pack=client.get(f'/api/assurance/proof-pack?conflict_ref={ref}',headers=h).json()
            assert pack['subject']['decision_ref']==decision_ref
            assert pack['status']=='ASSURED'
            assert client.get('/api/assurance/invariants',headers=h).json()['status']=='HEALTHY'
        assert client.get('/api/system/readiness',headers=h).json()['score']==100


def test_frontend_no_longer_hardcodes_flagship_twin_and_has_live_proof_verify():
    root=Path(__file__).resolve().parents[2]
    js=(root/'frontend'/'src'/'sentinel.js').read_text(encoding='utf-8')
    assert '/simulations/conflict/CF-INCOME-001/run' not in js
    assert '/assurance/governance-gate/CF-INCOME-001' not in js
    assert '/assurance/rollout-plan/CF-INCOME-001' not in js
    assert "data-twin-conflict" in js
    assert "Verify this proof" in js
    assert "bundle_digest:proof.bundle_digest" in js
    assert "Hybrid AI Model Card" in js
    # The Overview focus card must read all narrative fields from one flagship object.
    overview=js[js.index('function renderOverview()'):js.index('function metricStrip')]
    assert 'hero.root_cause' not in overview
    assert 'hero.conflict_ref' not in overview
    assert 'flagship.root_cause' in overview


def test_unseen_evidence_generalises_across_all_three_policy_domains():
    samples=[
        ('The restructuring desk may approve loans up to risk score 70 under the legacy guide.','loan_restructure_rule','NUMERIC_THRESHOLD_COLLISION',11),
        ('Adverse decision notices must be sent within three calendar days.','notification_deadline','TEMPORAL_SEMANTICS_COLLISION',6),
        ('Bank statements are prohibited for gig-worker income evidence; payslips are mandatory.','income_document_rule','MODALITY_COLLISION',27),
    ]
    with client:
        h=login();reset(h)
        for text,rule,collision_type,count in samples:
            d=client.post('/api/live/challenge',headers=h,json={'source':'Cross-domain judge probe','title':'Unseen cross-domain policy','body':text,'authority':'External operations evidence','authority_level':2,'sensitivity':'internal'}).json()
            assert d['rule_key']==rule
            assert d['verdict']=='CONTRADICTION'
            assert d['blast_radius']==count
            assert collision_type in {x['type'] for x in d['analysis']['policy_atoms']['reasoning']['collisions']}
            assert d['analysis']['hybrid_ai']['governed_consensus']['engine']=='Sentinel Authority-Weighted Hybrid Consensus v1'


def test_track2_plain_language_answers_are_evidence_bound_role_aware_and_non_hallucinatory():
    with client:
        h=login();reset(h)
        manager=client.post('/api/memory/answer',headers=h,json={
            'question':'Can gig workers use bank statements as income evidence?',
            'preview_role':'manager',
        })
        assert manager.status_code==200
        mj=manager.json()
        assert mj['status']=='CONFLICT_PRESENT'
        assert mj['rule_key']=='income_document_rule'
        assert 'bank statement' in mj['answer'].lower()
        assert mj['authority']=='Product Owner'
        assert len(mj['citations'])>=1
        assert mj['model']['publication_authority']==0

        intern=client.post('/api/memory/answer',headers=h,json={
            'question':'Can gig workers use bank statements as income evidence?',
            'preview_role':'intern',
        }).json()
        assert intern['status']=='RESTRICTED'
        assert 'restricted' in intern['answer'].lower()
        assert '[REDACTED BY SENTINEL SHIELD]' in intern['citations'][0]['body']

        unknown=client.post('/api/memory/answer',headers=h,json={
            'question':'What is the official moon-base cafeteria policy for purple robots?',
            'preview_role':'manager',
        }).json()
        assert unknown['status']=='NEEDS_REVIEW'
        assert unknown['citations']==[]
        assert 'cannot' in unknown['answer'].lower() or 'no active governed evidence' in unknown['answer'].lower()

        publish(h,'CF-INCOME-001')
        post=client.post('/api/memory/answer',headers=h,json={
            'question':'Can gig workers use bank statements as income evidence?',
            'preview_role':'manager',
        }).json()
        assert post['status']=='VERIFIED'
        assert post['decision_ref']=='JT-084'
        assert 'verified bank statements' in post['answer'].lower()


def test_release_has_no_committed_runtime_secret_literals_and_launcher_has_port_failover():
    root=Path(__file__).resolve().parents[2]
    config=(root/'backend'/'app'/'core'/'config.py').read_text(encoding='utf-8')
    assert 'juristwin-finals-local-secret-change-me' not in config
    assert 'juristwin-finals-webhook-secret' not in config
    assert 'juristwin-finals-proof-signing-secret' not in config
    assert 'secrets.token_urlsafe' in config
    assert (root/'tools'/'bootstrap_env.py').exists()
    launcher=(root/'run_finals.bat').read_text(encoding='utf-8')
    assert 'choose_port.py' in launcher
    assert 'JURISTWIN_PORT' in launcher
    ignore=(root/'.gitignore').read_text(encoding='utf-8')
    assert '.env' in ignore and '.juristwin_port' in ignore
