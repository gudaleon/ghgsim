"""Living-paper automatic recompute (AN_v1): one command regenerates every Paper B result.

    python scripts/recompute_all_AN_v1.py --profile full      # Bubble PC: all steps (needs C:/ghgsim-data)
    python scripts/recompute_all_AN_v1.py --profile light     # CI: steps whose inputs are in the repo

Steps run in an isolated staging copy of the repository (build/recompute_stage_<stamp>/), so committed files are
never overwritten and the existing "refuse to overwrite" guards in each script still hold. Every step's outputs are
hashed and compared with the committed file of the same name ("reproduced": true/false).

The results manifest records: code commit (+ dirty flag), Python/package versions, parameter-file version and hash,
SHA-256 of every input (repo files and raw downloads), SHA-256 of every output, the upstream-source pins
(data/upstream_sources_AN_v*.json) and the paper numbers extracted from the outputs. Default destination is the next
free results/results_manifest_AN_vN.json (never overwritten); CI passes --out build/....
Steps marked bubble_only need raw data outside the repo (nClimDiv ~123 MB, NASS Census ~1 GB, CRT zips, EPA PDFs);
under --profile light they are recorded as "skipped: bubble_only" with the hashes of the committed outputs.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import importlib.metadata as md
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKGS = ["numpy", "pandas", "scipy", "pint", "pyyaml", "matplotlib", "lxml", "geopandas", "pyogrio", "pyproj",
        "shapely", "rasterio", "pymupdf", "requests"]
NCD = "climate/nclimdiv"
NCV = "20261006"
NCLIMDIV = [f"{NCD}/climdiv-pcpncy-v1.0.0-{NCV}", f"{NCD}/climdiv-tmaxcy-v1.0.0-{NCV}",
            f"{NCD}/climdiv-tmincy-v1.0.0-{NCV}", f"{NCD}/county-to-climdivs.txt", f"{NCD}/2020_Gaz_counties_national.zip"]
CRT = ["CAN-CRT-2026-V2.0.zip", "GBRJ-CRT-2026-V1.0.zip", "NZL-CRT-2026-V1.0_.zip", "IRL-CRT-2026-V1.0.zip",
       "DEU-CRT-2026-V1.0.zip", "AUS-CRT-2026-V1.0.zip"]
INV = [f"data/inventories_AN_v1/{iso}_{k}_AN_v1.csv" for iso in ("AUS", "CAN", "DEU", "GBR", "IRL", "NZL")
       for k in ("recalc", "summary3", "table3", "table8")] + ["data/inventories_AN_v1/run_manifest_AN_v1.json"]

# name, where, command (after python), repo inputs, raw inputs (relative to --raw), outputs, paper-number extractor
STEPS = [
    dict(name="county_p_pe", where="bubble_only", script="scripts/build_county_p_pe_AN_v2.py",
         args=["--raw", "{RAW}/" + NCD, "--version-date", NCV, "--start", "1991", "--end", "2020"],
         repo_inputs=[], raw_inputs=NCLIMDIV,
         outputs=["data/county_p_pe_may_oct_AN_v2.csv", "data/county_p_pe_manifest_AN_v2.json"], extract="p_pe"),
    dict(name="county_climate_annual", where="bubble_only", script="scripts/build_county_climate_annual_AN_v1.py",
         args=["--raw", "{RAW}/" + NCD, "--version-date", NCV, "--start", "1991", "--end", "2020"],
         repo_inputs=[], raw_inputs=NCLIMDIV,
         outputs=["data/county_climate_annual_AN_v1.csv", "data/county_climate_annual_manifest_AN_v1.json"], extract=None),
    dict(name="county_climate_zones", where="bubble_only", script="scripts/build_county_climate_zones_AN_v1.py",
         args=["--raw", "{RAW}/climate", "--version-date", NCV], repo_inputs=[],
         raw_inputs=NCLIMDIV + ["climate/ipcc_zones_zenodo7303808/IPCC_Climate_Zones_ts_3.25.tif"],
         outputs=["data/county_climate_zones_AN_v1.csv", "data/county_climate_zones_manifest_AN_v1.json"], extract="zones"),
    dict(name="stylized_2006_vs_2019", where="ci", script="scripts/compare_ipcc_2006_2019_stylized_AN_v2.py", args=[],
         repo_inputs=["data/stylized_farms_AN_v6.yaml", "{PARAMS}"], raw_inputs=[],
         outputs=["data/ipcc_2006_vs_2019_stylized_AN_v2.csv"], extract="stylized"),
    dict(name="fig_stylized", where="ci", script="scripts/plot_ipcc_2006_vs_2019_stylized_AN_v2.py", args=[],
         repo_inputs=["data/ipcc_2006_vs_2019_stylized_AN_v2.csv"], raw_inputs=[],
         outputs=["docs/figures/ipcc_2006_vs_2019_stylized_AN_v2.png"], extract=None),
    dict(name="us_county_run", where="bubble_only", script="scripts/run_us_county_2006_vs_2019_AN_v2.py",
         args=["--nass", "{RAW}/nass/qs.census2022.txt.gz",
               "--fert", "{RAW}/fert/epa_commercial_fertilizer_purchased_20261103.html",
               "--shp", "{RAW}/nass/cb_2021_us_county_20m.zip"],
         repo_inputs=["data/ipcc_params_AN_v10.csv", "data/mms_north_america_ipcc2006_AN_v1.csv",
                      "data/county_climate_zones_AN_v1.csv"],
         raw_inputs=["nass/qs.census2022.txt.gz", "fert/epa_commercial_fertilizer_purchased_20261103.html",
                     "nass/cb_2021_us_county_20m.zip"],
         outputs=["data/us_county_2006_vs_2019_AN_v2.csv.gz", "data/us_national_2006_vs_2019_vs_epa_AN_v2.csv",
                  "data/us_county_run_manifest_AN_v2.json", "docs/figures/us_county_pct_change_2006_2019_AN_v2.png"],
         extract="us_county"),
    dict(name="inventories_crt2026", where="bubble_only", script="scripts/fetch_inventories_AN_v1.py",
         args=["--zip-dir", "{RAW}/crt2026", "--out", "data/inventories_AN_v1"], repo_inputs=[],
         raw_inputs=[f"crt2026/{z}" for z in CRT], outputs=INV, extract="inventories"),
    dict(name="inventories_us_epa", where="bubble_only", script="scripts/fetch_epa_ghgi_AN_v1.py",
         args=["--pdf-dir", "{RAW}/epa_ghgi", "--out", "data/inventories_US_AN_v1"], repo_inputs=[],
         raw_inputs=["epa_ghgi/ghgi_2024_main.pdf", "epa_ghgi/ghgi_2025_nepis.pdf"],
         outputs=["data/inventories_US_AN_v1/EPA2024_table5-1_AN_v1.csv", "data/inventories_US_AN_v1/EPA2025_table5-1_AN_v1.csv",
                  "data/inventories_US_AN_v1/EPA2025_table9-2_agriculture_AN_v1.csv",
                  "data/inventories_US_AN_v1/US_recalc_2024to2025_AN_v1.csv", "data/inventories_US_manifest_AN_v1.json"],
         extract="inventories_us"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def latest_versioned(folder: Path, stem: str, suffix: str) -> Path:
    best = None
    for p in folder.glob(f"{stem}_AN_v*{suffix}"):
        v = p.name[len(stem) + 5:-len(suffix)]
        if v.isdigit() and (best is None or int(v) > best[0]):
            best = (int(v), p)
    return best[1] if best else None


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def next_free(folder: Path, stem: str) -> Path:
    n = 1
    while (folder / f"{stem}_AN_v{n}.json").exists():
        n += 1
    return folder / f"{stem}_AN_v{n}.json"


def read_csv(p: Path):
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- paper-number extractors (pure functions of outputs)
def ex_p_pe(d: Path) -> dict:
    r = read_csv(d / "data/county_p_pe_may_oct_AN_v2.csv")
    h = [float(x["p_over_pe_hargreaves"]) for x in r if x["p_over_pe_hargreaves"]]
    t = [float(x["p_over_pe_thornthwaite"]) for x in r if x["p_over_pe_thornthwaite"]]
    return {"county_p_pe.n_counties": len(r), "county_p_pe.n_dry_hargreaves": sum(v < 1 for v in h),
            "county_p_pe.n_dry_thornthwaite": sum(v < 1 for v in t),
            "county_p_pe.median_p_over_pe_hargreaves": round(statistics.median(h), 3)}


def ex_zones(d: Path) -> dict:
    c = Counter(x["zone_primary"] for x in read_csv(d / "data/county_climate_zones_AN_v1.csv"))
    return {f"climate_zones.n_counties.{k or 'none'}": v for k, v in sorted(c.items())}


def ex_stylized(d: Path) -> dict:
    t6, t9 = defaultdict(float), defaultdict(float)
    for x in read_csv(d / "data/ipcc_2006_vs_2019_stylized_AN_v2.csv"):
        try:
            a, b = float(x["ipcc2006_tCO2e"]), float(x["ipcc2019_tCO2e"])
        except ValueError:
            continue
        if a == a and b == b:
            t6[x["farm_id"]] += a
            t9[x["farm_id"]] += b
    return {f"stylized.{f}.pct_change_total": round(100 * (t9[f] - t6[f]) / t6[f], 2) for f in sorted(t6) if t6[f]}


def us_county_numbers(nat: dict) -> dict:
    """nat: {'variant|category|year': MMT CO2e}; adds totals and % change."""
    out, var = {}, defaultdict(lambda: defaultdict(float))
    for k, v in nat.items():
        vv, cat, yr = k.split("|")
        out[f"us_county.{vv}.{cat}.{yr}_MMT"] = round(v, 3)
        var[(vv, yr)]["total"] += v
        var[(vv, cat)][yr] = v
    for (vv, x), dd in sorted(var.items()):
        if x in ("2006", "2019"):
            out[f"us_county.{vv}.total_in_scope.{x}_MMT"] = round(dd["total"], 3)
        elif dd.get("2006"):
            out[f"us_county.{vv}.{x}.pct_change"] = round(100 * (dd["2019"] - dd["2006"]) / dd["2006"], 2)
    for vv in {k.split("|")[0] for k in nat}:
        a, b = var[(vv, "2006")]["total"], var[(vv, "2019")]["total"]
        if a:
            out[f"us_county.{vv}.total_in_scope.pct_change"] = round(100 * (b - a) / a, 2)
    return dict(sorted(out.items()))


def county_distribution(path: Path, variant: str | None, label: str) -> dict:
    """Counties up/down and the spread of county % change (CH4+N2O, CO2e) from a county CSV."""
    t = defaultdict(lambda: [0.0, 0.0])
    for x in read_csv(path):
        if variant and x.get("variant") != variant:
            continue
        t[x["fips"]][0] += float(x["t_co2e_2006"] or 0)
        t[x["fips"]][1] += float(x["t_co2e_2019"] or 0)
    pc = sorted(100 * (b - a) / a for a, b in t.values() if a > 0)
    q = statistics.quantiles(pc, n=100)
    k = f"us_county.{label}.county_pct_change"
    return {f"{k}.n_counties": len(pc), f"{k}.n_up": sum(v > 0 for v in pc), f"{k}.n_down": sum(v < 0 for v in pc),
            f"{k}.median": round(statistics.median(pc), 2), f"{k}.p05": round(q[4], 2), f"{k}.p95": round(q[94], 2)}


def ex_us_county(d: Path) -> dict:
    out = us_county_numbers(json.loads((d / "data/us_county_run_manifest_AN_v2.json").read_text(encoding="utf-8"))
                            ["national_MMT_CO2e"])
    gz = d / "data/us_county_2006_vs_2019_AN_v2.csv.gz"
    if gz.exists():  # gitignored (large); present on Bubble
        out.update(county_distribution(gz, "D_allocated", "D_allocated"))
        out.update(county_distribution(gz, "disclosed", "disclosed"))
    return out


def ex_inventories(d: Path) -> dict:
    out = {}
    for p in sorted((d / "data/inventories_AN_v1").glob("*_recalc_AN_v1.csv")):
        for x in read_csv(p):
            if x["category"].strip().lower().startswith("3. agriculture"):
                out[f"inventory.{x['iso']}.agriculture.{x['year']}.recalc_pct"] = float(x["difference_pct"])
    return out


def ex_inventories_us(d: Path) -> dict:
    return {f"inventory.USA.{x['key']}.{x['year']}.recalc_MMT": float(x["diff_mmt"])
            for x in read_csv(d / "data/inventories_US_AN_v1/US_recalc_2024to2025_AN_v1.csv") if x["year"] == "2022"}


EXTRACT = {"p_pe": ex_p_pe, "zones": ex_zones, "stylized": ex_stylized, "us_county": ex_us_county,
           "inventories": ex_inventories, "inventories_us": ex_inventories_us}


def csv_diff(new: Path, old: Path) -> dict:
    """Cell-level summary of why a regenerated CSV differs from the committed one."""
    try:
        n, o = read_csv(new), read_csv(old)
    except Exception as e:
        return {"error": repr(e)}
    cols = Counter()
    for rn, ro in zip(n, o):
        for k in rn:
            if rn.get(k) != ro.get(k):
                cols[k] += 1
    return {"rows_new": len(n), "rows_committed": len(o), "cells_differing_by_column": dict(cols.most_common(12)),
            "example": next(({k: [ro.get(k), rn.get(k)] for k in rn if rn.get(k) != ro.get(k)}
                             for rn, ro in zip(n, o) if rn != ro), None)}


VOLATILE_KEYS = {"created", "generated", "path"}  # run timestamp / how a raw path was spelled; not results


def content_sha256(p: Path) -> str:
    """Hash of the decompressed bytes of a .gz (the gzip header carries a timestamp)."""
    with gzip.open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def json_diff(new: Path, old: Path, prefix: str = "") -> list:
    def walk(a, b, k):
        if isinstance(a, dict) and isinstance(b, dict):
            for x in sorted(a.keys() | b.keys()):
                yield from walk(a.get(x), b.get(x), f"{k}.{x}" if k else x)
        elif a != b:
            yield k
    try:
        return list(walk(json.loads(new.read_text(encoding="utf-8")), json.loads(old.read_text(encoding="utf-8")), prefix))[:20]
    except Exception as e:
        return [repr(e)]


# ---------------------------------------------------------------- runner
def stage_copy(dst: Path) -> None:
    ign = shutil.ignore_patterns(".git", ".venv", "build", "__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache",
                                 "legacy", "node_modules", "results")
    shutil.copytree(ROOT, dst, ignore=ign)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", choices=["light", "full"], default="light")
    ap.add_argument("--raw", default=os.environ.get("GHGSIM_DATA", "C:/ghgsim-data"))
    ap.add_argument("--only", nargs="*", help="run only these step names")
    ap.add_argument("--out", help="manifest path (default: next free results/results_manifest_AN_vN.json)")
    ap.add_argument("--keep-stage", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any output does not reproduce the committed file")
    a = ap.parse_args(argv)
    raw = Path(a.raw)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    stage = ROOT / "build" / f"recompute_stage_{stamp}"
    stage_copy(stage)
    params = latest_versioned(ROOT / "data", "ipcc_params", ".csv")
    env = dict(os.environ, PYTHONPATH=str(stage / "src") + os.pathsep + os.environ.get("PYTHONPATH", ""),
               MPLBACKEND="Agg", PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8")
    steps_out, numbers, failed, mism = [], {}, [], []
    for s in STEPS:
        if a.only and s["name"] not in a.only:
            continue
        rec = {"name": s["name"], "where": s["where"], "script": s["script"],
               "script_sha256": sha256(ROOT / s["script"]), "args": [x.replace("{RAW}", str(raw)) for x in s["args"]]}
        ins = {}
        for p in s["repo_inputs"]:
            p = str(params.relative_to(ROOT)).replace("\\", "/") if p == "{PARAMS}" else p
            ins[p] = sha256(stage / p) if (stage / p).exists() else None
        run = a.profile == "full" or s["where"] == "ci"
        missing = [p for p in s["raw_inputs"] if not (raw / p).exists()]
        rec["inputs_sha256"] = ins
        if run and not missing:
            for o in s["outputs"]:
                (stage / o).unlink(missing_ok=True)
            t0 = time.time()
            cp = subprocess.run([sys.executable, s["script"], *rec["args"]], cwd=stage, env=env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
            rec.update(status="ok" if cp.returncode == 0 else f"error({cp.returncode})", seconds=round(time.time() - t0, 1),
                       log_tail=(cp.stdout + cp.stderr)[-1500:])
            base = stage
        else:
            rec.update(status="skipped: bubble_only (committed outputs hashed instead)")
            base = ROOT
        if run and missing:  # never half-run a step; CRT zips must be fetched by hand (unfccc.int bot challenge)
            rec.update(status="skipped: raw input missing (committed outputs hashed instead)", missing_raw=missing)
            base = ROOT
        for p in s["raw_inputs"]:  # after the run: a step may download into its raw cache
            ins["RAW:" + p] = sha256(raw / p) if (raw / p).exists() else None
        outs = {}
        for o in s["outputs"]:
            p, ref = base / o, ROOT / o
            outs[o] = {"sha256": sha256(p) if p.exists() else None,
                       "committed_sha256": sha256(ref) if ref.exists() else None}
            outs[o]["reproduced"] = outs[o]["sha256"] is not None and outs[o]["sha256"] == outs[o]["committed_sha256"]
            if o.endswith(".gz") and p.exists() and ref.exists() and not outs[o]["reproduced"]:
                outs[o]["content_sha256"], outs[o]["committed_content_sha256"] = content_sha256(p), content_sha256(ref)
                outs[o]["reproduced"] = outs[o]["content_sha256"] == outs[o]["committed_content_sha256"]
                outs[o]["reproduced_basis"] = "decompressed content (gzip header timestamp differs)"
            if o.endswith(".json") and run and p.exists() and ref.exists() and not outs[o]["reproduced"]:
                outs[o]["json_keys_differing"] = jd = json_diff(p, ref)
                if jd and all(k.rsplit(".", 1)[-1] in VOLATILE_KEYS for k in jd):
                    outs[o]["reproduced"] = True
                    outs[o]["reproduced_basis"] = "all content equal except run metadata: " + ", ".join(jd)
            if run and not missing and not outs[o]["reproduced"]:
                mism.append(o)
                if ref.exists() and p.exists() and (o.endswith(".csv") or o.endswith(".csv.gz")):
                    outs[o]["diff_vs_committed"] = csv_diff(p, ref)
        rec["outputs"] = outs
        if rec["status"].startswith("error"):
            failed.append(s["name"])
        elif s["extract"]:
            try:
                nums = EXTRACT[s["extract"]](base)
                numbers.update(nums)
                rec["paper_numbers"] = sorted(nums)
            except Exception as e:  # missing committed output under light profile
                rec["extract_error"] = repr(e)
        print(f"[{rec['status'][:40]:40}] {s['name']}", flush=True)
        steps_out.append(rec)
    up = latest_versioned(ROOT / "data", "upstream_sources", ".json")
    vers = {}
    for k in PKGS:
        try:
            vers[k] = md.version(k)
        except md.PackageNotFoundError:
            vers[k] = None
    man = {
        "schema": "ghgsim.results_manifest/1",
        "generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "profile": a.profile, "host": platform.node(), "platform": platform.platform(),
        "python": sys.version.split()[0], "packages": vers,
        "code": {"commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                 "dirty": bool(git("status", "--porcelain", "--untracked-files=no"))},
        "parameter_file": {"path": str(params.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(params)},
        "upstream_sources": {"path": str(up.relative_to(ROOT)).replace("\\", "/"),
                             "pins": json.loads(up.read_text(encoding="utf-8"))} if up else None,
        "steps": steps_out, "paper_numbers": dict(sorted(numbers.items())),
        "summary": {"failed": failed, "not_reproduced": mism},
    }
    out = Path(a.out) if a.out else next_free(ROOT / "results", "results_manifest")
    if out.exists():
        sys.exit(f"refusing to overwrite {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(man, indent=2), encoding="utf-8")
    print("wrote", out, "| failed:", failed or "none", "| not reproduced:", mism or "none")
    if not a.keep_stage:
        shutil.rmtree(stage, ignore_errors=True)
    return 1 if failed or (a.strict and mism) else 0


if __name__ == "__main__":
    sys.exit(main())