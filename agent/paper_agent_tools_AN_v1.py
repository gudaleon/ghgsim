"""Paper B paper-agent tool functions (AN_v1).

Plain Python functions shared by the MCP server (agent/paper_agent_AN_v1.py) and the
dashboard (dashboard/app_AN_v2.py). Every value returned is read from committed repo
files or computed live by ghgsim; nothing is generated. Each answer carries a
"source" block naming the files (and SHA-256) or code it came from.

Design follows the Paper2Agent idea (Miao et al. 2026, Nature,
doi:10.1038/s41586-026-11044-y): turn a paper's code and data into callable tools.
"""
from __future__ import annotations

import contextlib
import csv
import dataclasses
import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
import threading
from functools import lru_cache
from pathlib import Path

ROOT = Path(os.environ.get("GHGSIM_ROOT", Path(__file__).resolve().parents[1]))
DATA, RESULTS, SCRIPTS = ROOT / "data", ROOT / "results", ROOT / "scripts"
for p in (ROOT / "src", SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

STYLIZED_SCRIPT = SCRIPTS / "compare_ipcc_2006_2019_stylized_AN_v2.py"
STYLIZED_CSV = DATA / "ipcc_2006_vs_2019_stylized_AN_v2.csv"
SPEC_FILE = DATA / "stylized_farms_AN_v6.yaml"
ZONES_CSV = DATA / "county_climate_zones_AN_v1.csv"
COUNTY_CSV = DATA / "us_county_2006_vs_2019_AN_v2.csv.gz"
PPE_CSV = DATA / "county_p_pe_may_oct_AN_v2.csv"
GUIDELINES = ("IPCC2006", "IPCC2019")
_LOCK = threading.Lock()


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _src(*paths: Path, **extra) -> dict:
    return {"files": {str(p.relative_to(ROOT)).replace("\\", "/"): _sha(p) for p in paths}, **extra}


def _clean(x):
    if isinstance(x, float):
        return None if math.isnan(x) else x
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


def _versioned(stem: str, suffix: str, folder: Path = DATA) -> list[Path]:
    def n(p):
        try:
            return int(p.name[len(stem) + 5:-len(suffix)])
        except ValueError:
            return -1
    return sorted(folder.glob(f"{stem}_AN_v*{suffix}"), key=n)


def _params_path(params_file: str | None) -> Path:
    if not params_file or params_file == "latest":
        return _versioned("ipcc_params", ".csv")[-1]
    p = DATA / Path(params_file).name
    if not p.is_file():
        raise ValueError(f"parameter file not found: {params_file}; available: {list_parameter_files()}")
    return p


@lru_cache(maxsize=1)
def _stylized_module():
    spec = importlib.util.spec_from_file_location("stylized_AN_v2", STYLIZED_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ discovery
def list_parameter_files() -> list[str]:
    return [p.name for p in _versioned("ipcc_params", ".csv")]


def list_farms() -> dict:
    """Stylized farms in the committed spec, with the herds and field they use."""
    m = _stylized_module()
    spec = m.load_stylized_spec(SPEC_FILE)
    farms = [{"farm_id": f["id"], "herds": list(f.get("herds") or []), "field_id": f.get("field_id"),
              "manure_id": f.get("manure_id"), "diet_id": f.get("diet_id")} for f in spec["farms"]]
    return {"farms": farms, "source": _src(SPEC_FILE)}


# ------------------------------------------------------------------ tool 1: run a farm
def run_farm(farm_id: str, guideline: str = "both", params_file: str = "latest",
             param_overrides: dict[str, float] | None = None,
             climate_zone_2019: str | None = None, storage_months: int | None = None) -> dict:
    """Run one stylized farm live in ghgsim under IPCC 2006 and/or the 2019 Refinement.

    param_overrides maps registry keys (e.g. "IPCC2006.EF1.all") to user-chosen values;
    overridden keys are listed in the answer so the result is never mistaken for the paper's.
    """
    m = _stylized_module()
    from ghgsim.core.registry import load_parameter_csv

    spec = m.load_stylized_spec(SPEC_FILE)
    farm = next((f for f in spec["farms"] if f["id"] == farm_id), None)
    if farm is None:
        raise ValueError(f"unknown farm_id {farm_id!r}; see list_farms()")
    pfile = _params_path(params_file)
    reg = load_parameter_csv(pfile, allow_unverified=False)
    applied = {}
    if param_overrides:
        ov = {}
        for k, v in param_overrides.items():
            base = reg.get(k)  # raises if the key is not in the registry
            ov[k] = dataclasses.replace(base, value=float(v), notes=f"USER OVERRIDE (was {base.value})")
            applied[k] = {"published": base.value, "used": float(v), "table": base.table, "page": base.page}
        reg.add_overlay(ov)
    const, gwp = m._const(spec), m.gwp_from_spec(spec)
    gas = {"enteric_CH4": "CH4", "manure_CH4": "CH4", "manure_N2O": "N2O", "soil_N2O": "N2O"}
    versions = GUIDELINES if guideline == "both" else (guideline,)
    if any(v not in GUIDELINES for v in versions):
        raise ValueError(f"guideline must be one of {GUIDELINES} or 'both'")
    out = {}
    with _LOCK:
        old = (m.CLIMATE_ZONE_2019, m.STORAGE_MONTHS)
        try:
            if climate_zone_2019:
                m.CLIMATE_ZONE_2019 = climate_zone_2019
            if storage_months:
                m.STORAGE_MONTHS = int(storage_months)
            settings = {"climate_zone_2019": m.CLIMATE_ZONE_2019, "storage_months": m.STORAGE_MONTHS,
                        "mcf_zone_2006": spec["meta"]["climate_zone"]}
            for v in versions:
                res, notes = m.run_version(v, spec, farm, reg, const)
                rows = {s: {"kg": res[s], "tCO2e": res[s] * gwp[gas[s]] / 1000, "gas": gas[s]} for s in gas}
                total = sum(r["tCO2e"] for r in rows.values() if not math.isnan(r["tCO2e"]))
                out[v] = {"sources": rows, "total_tCO2e_excl_missing": total, "notes": sorted(set(notes))}
        finally:
            m.CLIMATE_ZONE_2019, m.STORAGE_MONTHS = old
    if len(versions) == 2:
        a, b = out["IPCC2006"]["total_tCO2e_excl_missing"], out["IPCC2019"]["total_tCO2e_excl_missing"]
        out["change_2019_vs_2006_pct"] = 100 * (b - a) / a if a else None
    return _clean({"farm_id": farm_id, "results": out, "settings": settings, "param_overrides": applied,
                   "gwp": "AR5 GWP100 from spec meta.gwp_ar5",
                   "source": _src(SPEC_FILE, pfile, STYLIZED_SCRIPT, engine="ghgsim ipcc2006/ipcc2019 modules")})


def committed_farm_result(farm_id: str) -> dict:
    """The committed Paper B stylized-farm numbers (data/ipcc_2006_vs_2019_stylized_AN_v2.csv)."""
    with STYLIZED_CSV.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["farm_id"] == farm_id]
    if not rows:
        raise ValueError(f"farm_id {farm_id!r} not in {STYLIZED_CSV.name}")
    return {"rows": rows, "source": _src(STYLIZED_CSV)}


# ------------------------------------------------------------------ tool 2: county results / zones
@lru_cache(maxsize=1)
def _county_df():
    import pandas as pd
    return pd.read_csv(COUNTY_CSV, dtype={"fips": str})


@lru_cache(maxsize=1)
def _zones_df():
    import pandas as pd
    return pd.read_csv(ZONES_CSV, dtype={"fips": str})


def county_climate_zone(fips: str) -> dict:
    fips = str(fips).zfill(5)
    z = _zones_df()
    r = z[z["fips"] == fips]
    if r.empty:
        raise ValueError(f"FIPS {fips} not in {ZONES_CSV.name}")
    return _clean({"fips": fips, **r.iloc[0].to_dict(), "source": _src(ZONES_CSV)})


def county_results(fips: str | None = None, state: str | None = None, variant: str = "disclosed",
                   by: str = "source_gas") -> dict:
    """US county IPCC 2006 vs 2019 results (committed run). Give a FIPS code or a 2-letter state."""
    df = _county_df()
    if variant not in set(df["variant"]):
        raise ValueError(f"variant must be one of {sorted(set(df['variant']))}")
    d = df[df["variant"] == variant]
    if fips:
        d = d[d["fips"] == str(fips).zfill(5)]
    elif state:
        d = d[d["state"] == state.upper()]
    else:
        raise ValueError("give fips or state")
    if d.empty:
        raise ValueError("no rows for that selection")
    keys = {"source_gas": ["source", "gas"], "category": ["source", "category", "gas"], "county": ["fips", "county"]}[by]
    g = d.groupby(keys, as_index=False)[["t_co2e_2006", "t_co2e_2019"]].sum()
    g["pct_change"] = (100 * (g["t_co2e_2019"] - g["t_co2e_2006"]) / g["t_co2e_2006"]).round(2)
    t06, t19 = float(d["t_co2e_2006"].sum()), float(d["t_co2e_2019"].sum())
    out = {"selection": {"fips": fips, "state": state, "variant": variant}, "n_counties": int(d["fips"].nunique()),
           "total_t_co2e_2006": t06, "total_t_co2e_2019": t19,
           "pct_change": 100 * (t19 - t06) / t06 if t06 else None, "rows": g.to_dict("records"),
           "source": _src(COUNTY_CSV)}
    if fips:
        out["climate_zone"] = county_climate_zone(fips)
        out["census_flags"] = str(d["census_flags"].iloc[0])
    return _clean(out)


# ------------------------------------------------------------------ tool 3: explain a parameter
def explain_parameter(key: str, params_file: str = "latest", history: bool = True) -> dict:
    """Value, units, IPCC table/equation/page and source for a registry key (or matching keys)."""
    pfile = _params_path(params_file)
    with pfile.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    hit = [r for r in rows if r["key"] == key] or [r for r in rows if key.lower() in r["key"].lower()]
    if not hit:
        raise ValueError(f"no parameter matching {key!r} in {pfile.name}")
    hit = hit[:25]
    out = {"params_file": pfile.name, "matches": hit, "source": _src(pfile)}
    if history and len(hit) == 1:
        hist = []
        for p in _versioned("ipcc_params", ".csv"):
            with p.open(encoding="utf-8") as f:
                r = next((x for x in csv.DictReader(f) if x["key"] == hit[0]["key"]), None)
            hist.append({"file": p.name, "value": r["value"] if r else None,
                         "table": r["table"] if r else None, "page": r["page"] if r else None})
        out["history"] = hist
    return out


# ------------------------------------------------------------------ tool 4/5: provenance + diff
def list_manifests() -> list[str]:
    return [p.name for p in sorted(RESULTS.glob("*.json"))]


def _manifest(name: str | None) -> Path:
    if not name or name == "latest":
        return _versioned("results_manifest", ".json", RESULTS)[-1]
    p = RESULTS / Path(name).name
    if not p.is_file():
        raise ValueError(f"manifest not found: {name}; available: {list_manifests()}")
    return p


def provenance(manifest: str = "latest", number_prefix: str | None = None) -> dict:
    """Code commit, parameter file, upstream pins, step reproduction status and paper numbers."""
    p = _manifest(manifest)
    m = json.loads(p.read_text(encoding="utf-8"))
    steps = [{"name": s.get("name"), "where": s.get("where"), "status": s.get("status"),
              "outputs_reproduced": {k: v.get("reproduced") for k, v in (s.get("outputs") or {}).items()}}
             for s in m.get("steps", [])]
    nums = m.get("paper_numbers", {})
    if number_prefix:
        nums = {k: v for k, v in nums.items() if k.startswith(number_prefix)}
    return {"manifest": p.name, "generated": m.get("generated"), "profile": m.get("profile"),
            "code": m.get("code"), "parameter_file": m.get("parameter_file"),
            "upstream_sources": m.get("upstream_sources"), "steps": steps, "summary": m.get("summary"),
            "paper_numbers": nums, "n_paper_numbers_total": len(m.get("paper_numbers", {})),
            "source": _src(p)}


def diff_manifests(old: str, new: str, tol: float = 0.005) -> dict:
    """Run scripts/diff_results_AN_v1.py on two committed manifests; returns its markdown report."""
    import diff_results_AN_v1 as dr
    a, b = _manifest(old), _manifest(new)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "diff.md"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dr.main([str(a), str(b), "--out", str(out), "--tol", str(tol)])
        md = out.read_text(encoding="utf-8")
    return {"old": a.name, "new": b.name, "report_markdown": md,
            "source": _src(a, b, SCRIPTS / "diff_results_AN_v1.py")}
