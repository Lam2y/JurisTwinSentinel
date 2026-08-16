import os
import subprocess
import sys
from pathlib import Path

import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.services.red_team import _mutate_jwt_signature

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]


def auth():
    r = client.post('/api/auth/login', json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
    assert r.status_code == 200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def test_jwt_tamper_probe_is_secret_independent():
    # Regression for the base64url-padding bug found on the actual finals Windows machine.
    for i in range(64):
        secret = f"machine-secret-{i:02d}-" + ("x" * (16 + i % 11))
        good = jwt.encode({'sub':'1','role':'manager'}, secret, algorithm='HS256')
        forged = _mutate_jwt_signature(good)
        assert forged != good
        try:
            jwt.decode(forged, secret, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            pass
        else:
            raise AssertionError(f'forged token unexpectedly verified for secret index {i}')


def test_preflight_survives_cp1252_console_mode():
    env = os.environ.copy()
    env['PYTHONPATH'] = str(BACKEND)
    env['PYTHONIOENCODING'] = 'cp1252'
    # The script reconfigures stdout/stderr to UTF-8 itself, so Windows' default console encoding
    # cannot crash on arrows/middle dots.
    r = subprocess.run(
        [sys.executable, str(BACKEND/'scripts'/'industry_preflight.py'), '--ci'],
        cwd=str(BACKEND), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=120,
    )
    assert r.returncode == 0, r.stdout.decode('utf-8', errors='replace')


def test_track2_answer_exposes_measured_ai_verification_one_click_deep():
    with client:
        h = auth(); client.post('/api/demo/reset', headers=h)
        d = client.post('/api/memory/answer', headers=h, json={
            'question':'Can gig workers use bank statements as income evidence?',
            'preview_role':'manager',
        }).json()
        proof = d['ai_verification']
        assert proof['learned_component'] is True
        assert proof['domain_macro_f1'] >= 0.8
        assert proof['stance_macro_f1'] >= 0.8
        assert proof['publication_authority'] == 0
        assert proof['internet_required'] is False
        js = client.get('/static/sentinel.js?v=5.7.0').text
        assert 'How AI verified this' in js
        assert 'Learned AI generalises. Symbolic reasoning verifies. Humans publish.' in js


def test_vendor_fixtures_never_fake_sync_counts_and_live_gateway_is_visible():
    with client:
        h = auth(); client.post('/api/demo/reset', headers=h)
        integrations = client.get('/api/integrations', headers=h).json()
        outlook = next(x for x in integrations if x['key']=='outlook')
        before = outlook['object_count']
        r = client.post('/api/integrations/outlook/sync', headers=h)
        assert r.status_code == 200
        after = r.json()
        assert after['object_count'] == before
        assert after['operation']['mode'] == 'fixture_no_mutation'
        assert after['operation']['live_network_call'] is False
        gateway = next(x for x in integrations if x['key']=='webhook')
        assert gateway['details']['adapter_mode'] == 'live_http_ingress'
        assert gateway['details']['auth'] == 'HMAC-SHA256'


def test_windows_launcher_uses_venv_and_prints_startup_heartbeat():
    bat = (ROOT/'run_finals.bat').read_text(encoding='utf-8')
    launcher = (BACKEND/'scripts'/'finals_launcher.py').read_text(encoding='utf-8')
    setup = (ROOT/'setup_windows.bat').read_text(encoding='utf-8')
    assert '.venv\\Scripts\\python.exe' in bat
    assert 'finals_launcher.py' in bat
    assert '[STARTING' in launcher and '[READY]' in launcher
    assert 'Port 8000 is busy' in launcher
    assert '3.14' in setup and '3.12' in setup
    assert 'industry_preflight.py' in (ROOT/'run_preflight.bat').read_text(encoding='utf-8')
