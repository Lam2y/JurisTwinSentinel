from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'app' / 'static'


def test_juristech_assets_use_native_document_scroll_and_sticky_chrome():
    css=(STATIC/'sentinel.css').read_text(encoding='utf-8')
    html=(STATIC/'finals.html').read_text(encoding='utf-8')
    assert '/static/sentinel.css?v=5.5.0' in html
    assert '/static/sentinel.js?v=5.5.0' in html
    assert 'body{overflow-x:hidden;overflow-y:auto' in css
    assert '.sidebar{position:sticky;top:0;height:100vh' in css
    assert '.topbar{position:sticky;top:0' in css
    assert '.page-scroll{flex:none;min-height:calc(100vh - var(--topbar-h));overflow:visible' in css
    assert '.scroll-progress{' in css


def test_juristech_motion_and_accessibility_controls_are_present():
    css=(STATIC/'sentinel.css').read_text(encoding='utf-8')
    js=(STATIC/'sentinel.js').read_text(encoding='utf-8')
    assert '::view-transition-old(root)' in css
    assert '@media(prefers-reduced-motion:reduce)' in css
    assert 'updateAmbientPointer' in js
    assert 'updateScrollProgress' in js
    assert 'window.scrollTo(0,0)' in js
