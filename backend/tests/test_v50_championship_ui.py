from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_championship_ui_serves_only_current_runtime_assets():
    with client:
        finals = client.get('/finals')
        assert finals.status_code == 200
        assert '/static/sentinel.css?v=5.4.0' in finals.text
        assert '/static/sentinel.js?v=5.4.0' in finals.text
        assert 'experience.css' not in finals.text
        assert 'prototype.css' not in finals.text
        assert client.get('/static/sentinel.css').status_code == 200
        assert client.get('/static/sentinel.js').status_code == 200


def test_ui_contract_includes_bounded_graph_and_consistent_sheet_controls():
    with client:
        js = client.get('/static/sentinel.js').text
        css = client.get('/static/sentinel.css').text
        assert 'document.startViewTransition' in js
        assert 'setPointerCapture' in js
        assert 'releasePointerCapture' in js
        assert 'data-close-sheet' in js
        assert "['overview','Overview'" in js
        assert "['conflict','Conflict Map'" in js
        assert "['twin','Digital Twin'" in js
        assert "['assurance','Assurance'" in js
        assert "['evidence','Evidence Lab'" in js
        assert 'touch-action:none' in css
        assert '.status-capsule' in css
