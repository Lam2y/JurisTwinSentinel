from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def auth():
    r = client.post('/api/auth/login', json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
    assert r.status_code == 200, r.text
    return {'Authorization': f"Bearer {r.json()['access_token']}"}


def test_finals_sidebar_story_and_management_control_plane_are_first_class():
    js=(ROOT/'frontend'/'src'/'sentinel.js').read_text(encoding='utf-8')
    assert "['overview','Ask JurisTwin'" in js
    assert "['controls','Management Controls'" in js
    assert "['conflict','Why Sources Disagree'" in js
    assert "['twin','Compare Solutions'" in js
    assert "['assurance','Safe to Publish?'" in js
    assert "['evidence','Test New Evidence'" in js
    assert "['governance','Privacy & Security'" in js
    assert 'Who controls what JurisTwin is allowed to trust?' in js
    assert 'MANAGEMENT · NOT THE AI' in js
    assert '10 informal messages cannot outvote 1 approved decision.' in js
    assert 'LIVE EVIDENCE BOUNDARY' in js


def test_safe_to_publish_has_visible_human_authority_boundary():
    js=(ROOT/'frontend'/'src'/'sentinel.js').read_text(encoding='utf-8')
    assert 'AI PUBLISH AUTHORITY · 0' in js
    assert 'Approve & publish' in js
    assert 'PUBLISHED BY HUMAN' in js
    assert 'Verify decision record' in js
    assert "state.page='assurance'" in js


def test_live_source_policy_still_changes_next_answer():
    with client:
        h=auth()
        assert client.post('/api/demo/reset',headers=h).status_code==200
        before=client.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        assert any(str(x.get('source','')).lower()=='fsd' for x in before.get('source_mix',[]))
        r=client.patch('/api/integrations/sharepoint/policy',headers=h,json={'config':{'retrieval_enabled':False}})
        assert r.status_code==200,r.text
        after=client.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        assert all(str(x.get('source','')).lower()!='fsd' for x in after.get('source_mix',[]))
        assert after['primary_source']['source']=='Outlook Approval'
        assert client.post('/api/demo/reset',headers=h).status_code==200
