from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_passive_session_probe_is_console_clean():
    with client:
        r = client.get('/api/auth/session')
        assert r.status_code == 200
        assert r.json() == {'authenticated': False, 'user': None}

        stale = client.get('/api/auth/session', headers={'Authorization':'Bearer definitely-stale'})
        assert stale.status_code == 200
        assert stale.json()['authenticated'] is False

        login = client.post('/api/auth/login', json={
            'email':'operations@regulatedbank.com',
            'password':'Finals2026!'
        })
        assert login.status_code == 200
        token = login.json()['access_token']
        valid = client.get('/api/auth/session', headers={'Authorization':f'Bearer {token}'})
        assert valid.status_code == 200
        assert valid.json()['authenticated'] is True
        assert valid.json()['user']['email'] == 'operations@regulatedbank.com'


def test_finals_experience_assets_and_favicon_are_served():
    with client:
        finals = client.get('/finals')
        assert finals.status_code == 200
        assert '/static/sentinel.css?v=5.7.0' in finals.text
        assert '/static/sentinel.js?v=5.7.0' in finals.text
        assert '/static/favicon.svg?v=5.7.0' in finals.text

        assert client.get('/static/sentinel.css').status_code == 200
        assert client.get('/static/sentinel.js').status_code == 200
        icon = client.get('/favicon.ico')
        assert icon.status_code == 200
        assert 'image/svg+xml' in icon.headers.get('content-type','')
