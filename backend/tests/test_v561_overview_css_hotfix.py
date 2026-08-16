from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"


def test_other_live_conflicts_has_structured_responsive_cards():
    js=(STATIC/"sentinel.js").read_text(encoding="utf-8")
    css=(STATIC/"sentinel.css").read_text(encoding="utf-8")
    assert 'class="priority-grid"' in js
    assert 'class="priority-card"' in js
    assert '.priority-grid{' in css
    assert '.priority-copy>b{' in css
    assert '.priority-impact strong{' in css
    assert '@media(max-width:680px)' in css


def test_decision_integrity_has_non_overlapping_score_and_metrics():
    js=(STATIC/"sentinel.js").read_text(encoding="utf-8")
    css=(STATIC/"sentinel.css").read_text(encoding="utf-8")
    assert 'class="integrity-gauge"' in js
    assert 'class="integrity-gauge-inner"' in js
    assert 'class="integrity-foot"' in js
    assert '.integrity-gauge-inner strong{' in css
    assert '.integrity-bars .bar-top{' in css
    assert '.integrity-foot{' in css
