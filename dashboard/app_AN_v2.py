#!/usr/bin/env python3
"""Paper B living-paper dashboard (Gradio), AN_v2 (adds the "Ask the paper" tab; AN_v1 unchanged).

Every number shown is read from ghgsim itself: the committed county CSV,
a live ghgsim run, or a hash computed at load time. Nothing is typed in.

Tabs
  1. County P/PE  - data/county_p_pe_may_oct_AN_v2.csv (May-Oct, 1991-2020),
                    Hargreaves vs Thornthwaite potential evapotranspiration (PE).
  2. Version diff - runs ghgsim.compat.FarmModel live on a stylized example farm
                    under the IPCC 2006 guidelines and the 2019 Refinement.
  3. Ask the paper - the paper-agent tools (agent/paper_agent_tools_AN_v1.py), no LLM.
  4. Provenance   - ghgsim version, git commit SHA, library versions, external
                    engine notes, dataset manifests and live SHA-256 checks.

Run locally (repo root):  python dashboard/app_AN_v1.py
Set GHGSIM_ROOT to point at a ghgsim checkout if the app is moved elsewhere.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("GHGSIM_ROOT", Path(__file__).resolve().parents[1]))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from ghgsim.compat.farm import FarmModel  # noqa: E402
from ghgsim.core.registry import load_parameter_csv  # noqa: E402
from ghgsim.report.fork_diagram import latest_versioned  # noqa: E402

sys.path.insert(0, str(ROOT / "agent"))
import paper_agent_tools_AN_v1 as PA  # noqa: E402

DATA = ROOT / "data"
COUNTY_CSV = DATA / "county_p_pe_may_oct_AN_v2.csv"
EXAMPLES = ROOT / "legacy" / "livingghg_AN_v3" / "examples"
GUIDELINES = ("IPCC2006", "IPCC2019")
OUTPUTS = ("N2O_kg", "CH4_kg", "CH4_manure_kg", "N2O_manure_kg", "CO2e_t")


# ---------------------------------------------------------------- tab 1
def load_county() -> pd.DataFrame:
    df = pd.read_csv(COUNTY_CSV, dtype={"fips": str})
    df["fips"] = df["fips"].str.zfill(5)
    return df


def state_summary(df: pd.DataFrame, method: str) -> pd.DataFrame:
    col = f"p_over_pe_{method}"
    return (
        df.groupby("state", as_index=False)
        .agg(counties=("fips", "size"), median_p_over_pe=(col, "median"))
        .sort_values("state")
    )


def county_view(method: str, state: str):
    import plotly.express as px

    df = load_county()
    s = state_summary(df, method)
    fig = px.choropleth(
        s, locations="state", locationmode="USA-states", scope="usa",
        color="median_p_over_pe", color_continuous_scale="RdYlBu",
        hover_data=["counties"],
        title=f"Median county May-Oct P/PE by state ({method}, 1991-2020)",
    )
    sub = df if state == "All" else df[df["state"] == state]
    cols = ["fips", "state", "county", "growing_season_precip_mm",
            "pe_hargreaves_mm", "pe_thornthwaite_mm",
            "p_over_pe_hargreaves", "p_over_pe_thornthwaite"]
    return fig, sub[cols]


def method_compare() -> pd.DataFrame:
    df = load_county()
    out = []
    for m in ("hargreaves", "thornthwaite"):
        r = df[f"p_over_pe_{m}"]
        out.append({"PE method": m, "counties": int(r.notna().sum()),
                    "P/PE < 1 (drier)": int((r < 1).sum()),
                    "P/PE >= 1": int((r >= 1).sum()),
                    "median P/PE": round(float(r.median()), 3)})
    return pd.DataFrame(out)


# ---------------------------------------------------------------- tab 2
def example_farms() -> dict[str, Path]:
    return {p.stem: p for p in sorted(EXAMPLES.glob("example_farm_AN_v*.json"))}


def run_version_diff(farm_name: str, params_name: str) -> tuple[pd.DataFrame, str]:
    farm = json.loads(example_farms()[farm_name].read_text(encoding="utf-8"))
    reg = load_parameter_csv(DATA / params_name, allow_unverified=False)
    res, notes = {}, []
    for g in GUIDELINES:
        try:
            res[g] = FarmModel(g).run_farm(farm, reg)
        except Exception as exc:  # show the real ghgsim error, never a filler number
            notes.append(f"**{g} not computable:** `{exc}`")
    rows = []
    for k in OUTPUTS:
        a = res.get("IPCC2006", {}).get(k)
        b = res.get("IPCC2019", {}).get(k)
        d = None if a is None or b is None else b - a
        pct = None if d is None or a == 0 else 100 * d / a
        rows.append({"output": k, "IPCC 2006": a, "IPCC 2019": b,
                     "2019 - 2006": d, "change %": pct})
    note = (f"Live ghgsim run: `FarmModel.run_farm` on `{farm_name}.json` with "
            f"`{params_name}`. GWP100 = AR5 (CH4 28, N2O 265). "
            f"Label from file: _{farm.get('_label', '')}_")
    return pd.DataFrame(rows), "\n\n".join([note, *notes])


# ---------------------------------------------------------------- tab 3
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return os.environ.get("GHGSIM_COMMIT", "unknown (not a git checkout)")


def versions() -> pd.DataFrame:
    rows = [("ghgsim commit", git_sha()), ("python", platform.python_version())]
    for pkg in ("ghgsim", "gradio", "pandas", "numpy", "plotly"):
        try:
            rows.append((pkg, metadata.version(pkg)))
        except metadata.PackageNotFoundError:
            rows.append((pkg, "not installed as a distribution"))
    rows.append(("IPCC parameter registry (latest)", latest_versioned(DATA, "ipcc_params", ".csv").name))
    return pd.DataFrame(rows, columns=["item", "value"])


def engines_md() -> str:
    """External engines as recorded in the newest docs/BUBBLE_SETUP_AN_vN.md."""
    try:
        doc = latest_versioned(ROOT / "docs", "BUBBLE_SETUP", ".md")
    except Exception:
        return "No BUBBLE_SETUP doc found."
    keep = [ln for ln in doc.read_text(encoding="utf-8").splitlines()
            if ln.startswith("#") or any(k in ln for k in ("Version", "version", "Tag", "commit", "Install path"))]
    return f"From `docs/{doc.name}`:\n\n" + "\n".join(keep)


def _walk(node):
    if isinstance(node, dict):
        if isinstance(node.get("sha256"), str):
            yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def manifest_checks() -> pd.DataFrame:
    """Every manifest entry with a sha256 whose file is in the repo is re-hashed now."""
    rows = []
    for mf in sorted(DATA.glob("*manifest_AN_v*.json")):
        doc = json.loads(mf.read_text(encoding="utf-8"))
        for entry in _walk(doc):
            rel = entry.get("path") or entry.get("name")
            local = ROOT / rel if rel and (ROOT / rel).is_file() else None
            live = sha256(local) if local else None
            status = ("match" if live == entry["sha256"] else "MISMATCH") if live else "not in repo (external dataset)"
            rows.append({"manifest": mf.name, "file": rel,
                         "sha256 (manifest)": entry["sha256"], "live check": status})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- tab: ask the paper
def ask_paper(tool: str, farm: str, guideline: str, override_key: str, override_value: str,
              fips: str, state: str, key: str, m_old: str, m_new: str, prefix: str):
    """Call one paper-agent tool and return (json, markdown). Same functions the MCP server exposes."""
    try:
        if tool == "run_farm":
            ov = {override_key: float(override_value)} if override_key and override_value else None
            return PA.run_farm(farm, guideline, param_overrides=ov), ""
        if tool == "committed_farm_result":
            return PA.committed_farm_result(farm), ""
        if tool == "county_results":
            return PA.county_results(fips=fips or None, state=None if fips else state), ""
        if tool == "county_climate_zone":
            return PA.county_climate_zone(fips), ""
        if tool == "explain_parameter":
            return PA.explain_parameter(key), ""
        if tool == "provenance":
            return PA.provenance(m_new or "latest", prefix or None), ""
        if tool == "diff_manifests":
            r = PA.diff_manifests(m_old, m_new)
            return r["source"], r["report_markdown"]
    except Exception as exc:  # show the real error, never a filler number
        return {"error": str(exc)}, ""
    return {"error": f"unknown tool {tool}"}, ""


# ---------------------------------------------------------------- UI
def build_app():
    import gradio as gr

    states = ["All", *sorted(load_county()["state"].unique())]
    farms = list(example_farms())
    params = sorted(p.name for p in DATA.glob("ipcc_params_AN_v*.csv"))
    with gr.Blocks(title="Paper B living-paper dashboard") as app:
        gr.Markdown("# Paper B living-paper dashboard (AN_v2)\nAll values come from ghgsim "
                    "data files or live ghgsim runs. Field-data comparisons are consistency checks, not validation.")
        with gr.Tab("County P/PE"):
            gr.Markdown("Growing-season (May-Oct) precipitation (P) over potential evapotranspiration (PE), "
                        "1991-2020 NOAA nClimDiv. PE by Hargreaves-Samani (ghgsim default) or Thornthwaite. "
                        "P/PE below 1 means drier.")
            with gr.Row():
                method = gr.Radio(["hargreaves", "thornthwaite"], value="hargreaves", label="PE method")
                state = gr.Dropdown(states, value="All", label="State")
            plot = gr.Plot()
            gr.Dataframe(method_compare(), label="Method comparison (all counties)")
            table = gr.Dataframe(label="Counties")
            for c in (method, state):
                c.change(county_view, [method, state], [plot, table])
            app.load(county_view, [method, state], [plot, table])
        with gr.Tab("Version diff"):
            gr.Markdown("Recompute a stylized example farm under IPCC 2006 vs the 2019 Refinement, live in ghgsim.")
            with gr.Row():
                farm = gr.Dropdown(farms, value=farms[0], label="Stylized farm")
                prm = gr.Dropdown(params, value=params[-1], label="Parameter registry")
            btn = gr.Button("Run ghgsim")
            out = gr.Dataframe(label="Result")
            note = gr.Markdown()
            btn.click(run_version_diff, [farm, prm], [out, note])
        with gr.Tab("Ask the paper"):
            gr.Markdown("The paper-agent tools (also served over MCP by `agent/paper_agent_AN_v1.py`). "
                        "Every answer comes from ghgsim or committed files and lists its source files with SHA-256. "
                        "A parameter override is a what-if, not a Paper B number.")
            sfarms = [f["farm_id"] for f in PA.list_farms()["farms"]]
            mans = PA.list_manifests()
            tool = gr.Radio(["run_farm", "committed_farm_result", "county_results", "county_climate_zone",
                             "explain_parameter", "provenance", "diff_manifests"], value="run_farm", label="Tool")
            with gr.Row():
                a_farm = gr.Dropdown(sfarms, value=sfarms[0], label="Stylized farm")
                a_g = gr.Radio(["both", "IPCC2006", "IPCC2019"], value="both", label="Guideline")
                a_ok = gr.Textbox(label="Override key (optional)", placeholder="IPCC2006.EF1.all")
                a_ov = gr.Textbox(label="Override value")
            with gr.Row():
                a_fips = gr.Textbox(label="County FIPS", value="06019")
                a_state = gr.Textbox(label="State (if no FIPS)", value="IA")
                a_key = gr.Textbox(label="Parameter key", value="IPCC2006.EF1.all")
            with gr.Row():
                a_old = gr.Dropdown(mans, value=mans[0], label="Old manifest")
                a_new = gr.Dropdown(mans, value=mans[-1], label="New / provenance manifest")
                a_pre = gr.Textbox(label="Paper-number prefix", value="us_county")
            a_btn = gr.Button("Ask")
            a_json = gr.JSON(label="Tool result")
            a_md = gr.Markdown()
            a_btn.click(ask_paper, [tool, a_farm, a_g, a_ok, a_ov, a_fips, a_state, a_key, a_old, a_new, a_pre],
                        [a_json, a_md])
        with gr.Tab("Provenance"):
            gr.Dataframe(versions(), label="Versions")
            gr.Markdown(engines_md())
            gr.Dataframe(manifest_checks(), label="Dataset manifests (SHA-256 re-checked at load)")
    return app


if __name__ == "__main__":
    build_app().launch(server_name=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"))