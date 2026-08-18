from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"


def test_evidence_lab_select_cannot_overflow_its_card():
    css = (STATIC / "sentinel.css").read_text(encoding="utf-8")
    assert "grid-template-columns:minmax(0,1fr) minmax(0,1fr)" in css
    assert ".form-row>*{min-width:0;max-width:100%}" in css
    assert "select.form-control{" in css
    assert "text-overflow:ellipsis" in css


def test_conflict_graph_keeps_governed_titles_readable_and_selection_visible():
    js = (STATIC / "sentinel.js").read_text(encoding="utf-8")
    assert "function graphTitleLines" in js
    assert "function nodeDims(n)" in js
    assert "title.length>25" not in js
    assert "<title>${esc(title)} — ${esc(meta)}</title>" in js
    assert "selectGraphNode(id,true);" in js
