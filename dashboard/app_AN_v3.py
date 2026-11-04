"""Paper B living-paper dashboard AN v3: app_AN_v2 tabs plus three FINDINGS (v4-v9) tabs.

Tabs added: Lake Erie Holos CLI vs APSIM (FINDINGS v6), Rain pulses & averaging distortion (v8, v9 s2-3),
Brookston/Webster drainage (v4, v5, v7, v9 s1). Content is read from docs/ at runtime; nothing is
re-stated here. All comparisons are consistency checks, not validation.
Run locally: python dashboard/app_AN_v3.py
"""
from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("GHGSIM_ROOT", Path(__file__).resolve().parents[1]))
DOCS = ROOT / "docs"
FIG = DOCS / "figures"
NOTE = "> All comparisons on this tab are consistency checks, not validation.\n\n"

# tab -> list of (FINDINGS version, section-number filter or None for whole doc)
TABS = {
    "Lake Erie: Holos CLI vs APSIM": [(6, None)],
    "Rain pulses & averaging distortion": [(8, None), (9, ("2", "3"))],
    "Brookston/Webster drainage": [(4, None), (5, None), (7, None), (9, ("1",))],
}
FIGS = {
    "Rain pulses & averaging distortion": [
        "pulse_share_by_group_AN_v1.png", "pulse_share_by_group_thr5_AN_v1.png",
        "pulse_share_by_group_thr20_AN_v1.png", "county_distribution_by_method_AN_v1.png",
        "hotspot_rank_apsim_vs_methods_AN_v1.png", "interannual_sd_apsim_vs_holos_AN_v1.png"],
}


def findings_text(version: int, sections=None) -> str:
    text = (DOCS / f"FINDINGS_AN_v{version}.md").read_text(encoding="utf-8")
    if not sections:
        return text
    parts = re.split(r"(?m)^(?=## )", text)
    keep = [p for p in parts[1:] if re.match(r"## (\d+)\.", p) and re.match(r"## (\d+)\.", p).group(1) in sections]
    return parts[0].split("\n")[0] + " (selected sections)\n\n" + "".join(keep)


def tab_markdown(tab: str) -> str:
    return NOTE + "\n\n---\n\n".join(findings_text(v, s) for v, s in TABS[tab])


def tab_figures(tab: str) -> list[str]:
    return [str(FIG / f) for f in FIGS.get(tab, []) if (FIG / f).is_file()]


def _v2():
    spec = importlib.util.spec_from_file_location("app_AN_v2", Path(__file__).resolve().parent / "app_AN_v2.py")
    if not spec or not (Path(spec.origin).is_file()):
        spec = importlib.util.spec_from_file_location("app_AN_v2", ROOT / "app_AN_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_app():
    import gradio as gr

    core = _v2().build_app()
    with gr.Blocks(title="Paper B living-paper dashboard") as app:
        with gr.Tab("Dashboard"):
            core.render()
        for tab in TABS:
            with gr.Tab(tab):
                figs = tab_figures(tab)
                if figs:
                    gr.Gallery(value=figs, columns=3, height="auto", label="Figures")
                gr.Markdown(tab_markdown(tab))
    return app


if __name__ == "__main__":
    build_app().launch(server_name=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"))