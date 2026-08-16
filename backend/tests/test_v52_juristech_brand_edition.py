from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"


def test_v52_brand_hierarchy_and_large_type_are_shipped():
    css=(STATIC/"sentinel.css").read_text(encoding="utf-8")
    html=(STATIC/"finals.html").read_text(encoding="utf-8")
    assert "v=5.5.0" in html
    assert "--jt-red:#ef2334" in css
    assert "font-size:clamp(46px,4.3vw,70px)" in css
    assert "font-size:17px;line-height:1.6" in css
    assert "body{overflow-x:hidden;overflow-y:auto" in css


def test_v52_keeps_pitch_deck_capabilities_progressively_disclosed():
    js=(STATIC/"sentinel.js").read_text(encoding="utf-8")
    for feature in [
        "Secure Enterprise Memory",
        "Living Decision Digital Twin",
        "White-Box Future Simulator",
        "AI Bodyguard",
        "Decision Ledger",
        "Enterprise Connectors",
        "Policy Reasoner",
    ]:
        assert feature in js
    assert "platformMenu" in js
    assert "openMemoryCapability" in js
    assert "openLedgerCapability" in js
    assert "openBodyguardCapability" in js
    assert "openIntegrationsCapability" in js


def test_v52_presentation_mode_exists_for_projector_readability():
    css=(STATIC/"sentinel.css").read_text(encoding="utf-8")
    js=(STATIC/"sentinel.js").read_text(encoding="utf-8")
    assert "presentation-mode" in css
    assert "togglePresentation" in js
    assert "Alt + P" in js
    assert "jt_presentation" in js
