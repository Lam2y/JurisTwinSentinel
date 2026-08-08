from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def login():
    r=client.post('/api/auth/login',json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
    assert r.status_code==200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}

def publish(h):
    s=client.get('/api/simulations/conflict/CF-INCOME-001',headers=h).json()
    a=client.post(f"/api/approvals/simulation/{s['sim_ref']}/submit",headers=h,json={'selected_option':'C'}).json()
    r=client.post(f"/api/approvals/{a['approval_ref']}/approve",headers=h,json={'comments':'test'})
    assert r.status_code==200
    return r.json()

def test_v16_dynamic_twin_memory_and_admin_controls():
    with client:
        h=login();client.post('/api/demo/reset',headers=h)
        base=client.get('/api/simulations/conflict/CF-INCOME-001',headers=h).json()
        tuned=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={'weights':{'delay':90,'complaint':5,'alignment':5}}).json()
        assert tuned['weights']['delay']>.85
        assert tuned['options'][2]['predicted_delay_days'] != base['options'][2]['predicted_delay_days']

        m1=client.post('/api/memory/search',headers=h,json={'query':'','limit':10,'filters':{'project':'Sentinel'}}).json()
        m2=client.post('/api/memory/search',headers=h,json={'query':'','limit':10,'filters':{'project':'Credit Operations'}}).json()
        assert m1['results'] and m2['results']
        assert {x['evidence_ref'] for x in m1['results']} != {x['evidence_ref'] for x in m2['results']}

        gmail=next(x for x in client.get('/api/integrations',headers=h).json() if x['key']=='gmail')
        assert gmail['status']=='inactive'
        con=client.post('/api/integrations/gmail/connect',headers=h,json={'config':{'tenant':'finals-demo'}}).json()
        assert con['status']=='connected' and con['object_count']>0
        synced=client.post('/api/integrations/gmail/sync',headers=h).json()
        assert synced['object_count']>con['object_count']
        paused=client.post('/api/integrations/gmail/pause',headers=h).json()
        assert paused['status']=='inactive'

        cfg=client.get('/api/system/config',headers=h).json();mask=next(x for x in cfg['shields'] if x['key']=='data_masking')
        changed=client.patch('/api/system/shields/data_masking',headers=h,json={'enabled':not mask['enabled']}).json()
        assert changed['enabled'] != mask['enabled']

        role=client.patch('/api/system/roles/manager',headers=h,json={'can_modify_twin':False}).json()
        assert role['can_modify_twin'] is False
        denied=client.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={'weights':{'delay':1,'complaint':1,'alignment':1}})
        assert denied.status_code==403
        client.patch('/api/system/roles/manager',headers=h,json={'can_modify_twin':True})


def test_v16_bodyguard_actions_change_real_state_and_ledger_versions():
    with client:
        h=login();client.post('/api/demo/reset',headers=h);publish(h)
        a=client.post('/api/bodyguard/simulate-attack',headers=h).json()
        reviewed=client.post(f"/api/bodyguard/alerts/{a['alert_ref']}/review",headers=h).json();assert reviewed['status']=='reviewed'
        exp=client.post(f"/api/bodyguard/alerts/{a['alert_ref']}/explain",headers=h).json();assert exp['reasons'] and exp['decision_version']=='v4.1'
        revoked=client.post(f"/api/bodyguard/alerts/{a['alert_ref']}/revoke-access",headers=h).json();assert revoked['user']['active'] is False
        escalated=client.post(f"/api/bodyguard/alerts/{a['alert_ref']}/escalate",headers=h).json();assert escalated['status']=='escalated'
        override=client.post(f"/api/bodyguard/alerts/{a['alert_ref']}/authorize-overwrite",headers=h,json={'comments':'test override'}).json();assert override['decision_version']=='v4.2'
        dash=client.get('/api/dashboard',headers=h).json();assert dash['metrics']['customers_at_risk']==27
        led=client.get('/api/ledger/decisions/JT-084',headers=h).json();assert led['decision']['version']=='v4.2' and led['versions'][0]['version']=='v4.2'
        restored=client.post(f"/api/bodyguard/alerts/{a['alert_ref']}/restore",headers=h).json();assert restored['status']=='restored'
        dash2=client.get('/api/dashboard',headers=h).json();assert dash2['metrics']['customers_at_risk']==0
        led2=client.get('/api/ledger/decisions/JT-084',headers=h).json();assert led2['decision']['version']=='v4.3' and led2['versions'][0]['version']=='v4.3'
        assert client.get('/api/ledger/verify',headers=h).json()['ok'] is True
