"""Gradio-free checks for dashboard/app_AN_v3.py FINDINGS tabs."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mod():
    spec = importlib.util.spec_from_file_location("app_AN_v3", ROOT / "dashboard" / "app_AN_v3.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_tabs_have_content_and_figures():
    m = _mod()
    assert len(m.TABS) == 3
    for tab in m.TABS:
        md = m.tab_markdown(tab)
        assert "consistency check" in md and len(md) > 500
        for bad in ("Ratna", "MS2"):
            assert bad not in md
    assert len(m.tab_figures("Rain pulses & averaging distortion")) == 6
    s1 = m.findings_text(9, ("1",))
    assert "## 1." in s1 and "## 2." not in s1