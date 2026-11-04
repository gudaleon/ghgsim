"""Run FAO GLEAM (gleam R package, AGPL-3) unmodified as an outside model on the
ghgsim stylized cattle farms, and compare with ghgsim's IPCC 2006 / 2019 results (AN_v1).

Consistency check, not validation. No GLEAM code is copied into ghgsim: this script
only writes plain input CSVs, calls `Rscript scripts/run_gleam_stylized_AN_v1.R`
(our own Apache-2.0 R driver that calls exported gleam functions), and reads the CSV
GLEAM writes back.

Scope: the 9 cattle farms (dairy, beef cow-calf). Swine and poultry farms are not run:
GLEAM's modules need ration intake, digestibility, urinary energy and ash for every
cohort, and the stylized spec gives monogastrics only VS_kg_day, so running them
would need invented diet values (DECISIONS_AN_v13).

Mapping (ghgsim activity data -> GLEAM inputs), per animal class and factor set:
- species_short CTL; dairy_cow -> FA; dairy_heifer, dairy_calf, beef_calf -> FS (all are
  post-weaning, forage-fed classes in the spec); beef_cow -> FA. Each class is its own herd_id.
- ration_gross_energy = 18.45 MJ/kg DM (IPCC 2006 Eq 10.24 default GE density);
  ration_intake = GE / 18.45 with GE from IPCC 2006 Eq 10.16 as in the ghgsim run;
  ration_digestibility_fraction = DE/100; ration_urinary_energy_fraction = UE (0.02/0.04
  switch as in ghgsim); ration_ash = ASH_percent/100.
- nitrogen_excretion = Nex/365: EPA override from the spec when present, otherwise the
  factor-set Nrate (registry) x spec body mass / 1000 x 365, as ghgsim's modules do.
- MMS factors from ghgsim's registry for each factor set (2006: Table 10.17 15C MCF,
  2006 FracGasMS; 2019: Table 10.17 (Updated) warm temperate moist 12-month MCF, Table
  10.22 FracGasMS/FracLeachMS). GLEAM's MCF is in percent, so MCF x 100.
- GLEAM computes its own Ym (9.75 - 0.05 x DE%) and VS (intake x (1 - DE + UE) x (1 - ash)).
- Covers: GLEAM has no cover input; covered variants are run like uncovered (ghgsim's
  covered variants also equal uncovered, see Methods).
- Pasture: GLEAM counts PRP N2O inside manure; ghgsim counts it in soil N2O. Managed
  manure N2O ("other") is compared; GLEAM pasture N2O is reported separately.
- Missing published cell (2006 Table 10.22 has no other-cattle liquid FracGasMS): fracgas
  is passed as 0 only so GLEAM can run, and the farm's 2006 manure N2O is reported blank.

Usage: python scripts/run_gleam_stylized_AN_v1.py
Env: GHGSIM_RSCRIPT (path to Rscript), GHGSIM_R_LIBS (library holding gleam),
     GHGSIM_GLEAM_TARBALL (optional, the installed source tarball, hashed into the manifest).
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import compare_ipcc_2006_2019_stylized_AN_v2 as cmp  # noqa: E402

import ghgsim.modules.holos  # noqa: F401,E402  (import order as in the comparison script)
from ghgsim.core.registry import load_parameter_csv  # noqa: E402
from ghgsim.report.emissions_sankey import (  # noqa: E402
    _const,
    gwp_from_spec,
    herd_de_tdn,
    load_stylized_spec,
    net_energy,
    nex_kg_yr,
)

SPEC = ROOT / "data" / "stylized_farms_AN_v6.yaml"
PARAMS = ROOT / "data" / "ipcc_params_AN_v10.csv"
GHGSIM_RESULTS = ROOT / "data" / "ipcc_2006_vs_2019_stylized_AN_v2.csv"
R_DRIVER = ROOT / "scripts" / "run_gleam_stylized_AN_v1.R"
OUT = ROOT / "results"
TAG = "AN_v1"
F_INPUT = OUT / f"gleam_stylized_inputs_{TAG}.csv"
F_FRAC = OUT / f"gleam_stylized_mms_fraction_{TAG}.csv"
F_FACT = OUT / f"gleam_stylized_mms_factors_{TAG}.csv"
F_RAW = OUT / f"gleam_stylized_cohort_results_{TAG}.csv"
F_CMP = OUT / f"gleam_vs_ghgsim_stylized_{TAG}.csv"
F_MAN = OUT / f"gleam_stylized_manifest_{TAG}.json"
GLEAM_COMMIT = "b0937d260ea8c8022c241275220709c9294bae5f"
GLEAM_TAG = "v0.8.0-alpha"
GE_DENSITY = 18.45
COHORT = {"dairy_cow": "FA", "dairy_heifer": "FS", "dairy_calf": "FS", "beef_cow": "FA", "beef_calf": "FS"}
ALL_COHORTS = ("FA", "FS", "FJ", "MA", "MS", "MJ")
CATTLE_FARMS = {"dairy", "beef_cowcalf"}
SETS = ("IPCC2006", "IPCC2019")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def val(reg, *keys):
    for k in keys:
        try:
            return float(reg.get_value(k)), k
        except Exception:
            continue
    return math.nan, "|".join(keys) + " (not in registry)"


def mms_factors(reg, ver: str, at: str, system: str) -> tuple[dict, list[str]]:
    """GLEAM MMS factor row from ghgsim's registry. at: dairy | other_cattle."""
    y = ver[4:]
    keys = []
    if system == "liquid_nocrust":
        mcf = val(reg, "IPCC2006.MCF.liquid_nocrust|15C") if y == "2006" else \
            val(reg, f"IPCC2019.MCF.liquid_{cmp.STORAGE_MONTHS}mo|{cmp.CLIMATE_ZONE_2019}")
        ef3 = val(reg, f"IPCC{y}.EF3.liquid_nocrust")
        fg = val(reg, f"IPCC2006.FracGasMS.{at}|liquid_slurry") if y == "2006" else \
            val(reg, f"IPCC2019.FracGasMS.{at}|liquid_nocrust")
        fl = (0.0, "2006 manure module: no MMS leaching") if y == "2006" else \
            val(reg, f"IPCC2019.FracLeachMS.{at}|liquid_nocrust")
    elif system == "pasture":
        mcf = val(reg, "IPCC2006.MCF.pasture|15C") if y == "2006" else val(reg, "IPCC2019.MCF.pasture|all")
        ef3 = val(reg, "IPCC2006.EF3PRP_CPP.all") if y == "2006" else \
            val(reg, "IPCC2019.EF3PRP_CPP.wet", "IPCC2019.EF3PRP_CPP.all")
        fg = val(reg, f"IPCC{y}.FracGASM.all")
        fl = val(reg, f"IPCC{y}.FracLEACH.wet", f"IPCC{y}.FracLEACH-(H).wet", f"IPCC{y}.FracLEACH.all",
                 f"IPCC{y}.FracLEACH_H.all", f"IPCC{y}.FracLEACH-(H).all")
    else:
        raise ValueError(f"system {system} not mapped")
    bo = val(reg, f"IPCC{y}.B0.{at}|north_america")
    ef4 = val(reg, f"IPCC{y}.EF4.all")
    ef5 = val(reg, f"IPCC{y}.EF5.all")
    for _, k in (mcf, bo, ef3, ef4, ef5, fg, fl):
        keys.append(k)
    row = {"manure_management_system": f"mms_{system}",
           "methane_conversion_factor_mcf": mcf[0] * 100.0, "ch4_max_producing_capacity_bo": bo[0],
           "n2o_ef3": ef3[0], "n2o_ef4": ef4[0], "n2o_ef5": ef5[0],
           "nitrogen_fracgas": fg[0], "nitrogen_fracleach": fl[0]}
    return row, keys


def build_inputs(spec, reg, const):
    inputs, fracs, facts, notes = [], [], [], []
    for farm in spec["farms"]:
        if farm.get("farm_type") not in CATTLE_FARMS:
            continue
        systems = spec["manure_variants"][farm["manure_id"]]["systems"]
        diet = spec["diets"][farm["diet_id"]]
        for ver in SETS:
            for cid in farm["herds"]:
                a = spec["animal_classes"][cid]
                at = cmp.CATTLE_AT[str(a["animal_type"])]
                de, _t, _f = herd_de_tdn(spec, farm, a, diet)
                e = net_energy(spec, a, const, de)
                ge = cmp.ge_eq_10_16(e, de)
                ue = 0.02 if de >= const["ue_ipcc_de_threshold"] else 0.04
                if "Nex_kg_yr_override" in a:
                    nex, nsrc = nex_kg_yr(spec, a, const), "spec Nex_kg_yr_override"
                else:
                    nr, nsrc = val(reg, f"IPCC{ver[4:]}.Nrate.{at}|north_america")
                    nex = nr * e["weight_kg"] / 1000.0 * 365.0
                hid = f"{farm['id']}|{cid}|{ver}"
                base = {"herd_id": hid, "farm_id": farm["id"], "animal_class": cid, "factor_set": ver,
                               "species_short": "CTL",
                               "head": float(a["head"]["value"]),
                               "ration_digestibility_fraction": de / 100.0,
                               "ration_gross_energy": GE_DENSITY, "ration_intake": ge / GE_DENSITY,
                               "ration_urinary_energy_fraction": ue,
                               "ration_ash": float(const["ASH_percent"]) / 100.0,
                               "nitrogen_excretion": nex / 365.0, "GE_MJ_day_ghgsim": ge, "nex_source": nsrc}
                # GLEAM requires all six cohorts per herd_id; the mapped class sits in its
                # cohort and the other five are copies of it, flagged mapped=0 and discarded.
                for co in ALL_COHORTS:
                    inputs.append({**base, "cohort_short": co, "mapped": int(co == COHORT[cid])})
                    for sname, f in systems.items():
                        fracs.append({"herd_id": hid, "cohort_short": co,
                                      "manure_management_system": f"mms_{sname}",
                                      "manure_management_system_fraction": float(f)})
                for sname in systems:
                    row, keys = mms_factors(reg, ver, at, sname)
                    if math.isnan(row["nitrogen_fracgas"]):
                        notes.append(f"{farm['id']} {ver}: FracGasMS not published for {at} {sname};"
                                     " GLEAM run with 0 and manure N2O reported blank")
                        row["nitrogen_fracgas"] = 0.0
                        row["_n2o_missing"] = True
                    bad = [k for k, v in row.items() if isinstance(v, float) and math.isnan(v)]
                    if bad:
                        raise SystemExit(f"missing registry value for {hid} {sname}: {bad} ({keys})")
                    if not any(r["herd_id"] == hid and r["manure_management_system"] == row["manure_management_system"]
                               for r in facts):
                        facts.append({"herd_id": hid, **row, "registry_keys": ";".join(keys)})
    return inputs, fracs, facts, sorted(set(notes))


def write_csv(path: Path, rows: list[dict], cols: list[str] | None = None) -> None:
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path}")
    cols = cols or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def find_rscript() -> str | None:
    return os.environ.get("GHGSIM_RSCRIPT") or shutil.which("Rscript")


def main() -> None:
    rscript = find_rscript()
    if not rscript:
        raise SystemExit("Rscript not found: set GHGSIM_RSCRIPT")
    for p in (F_INPUT, F_FRAC, F_FACT, F_RAW, F_CMP, F_MAN):
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    spec = load_stylized_spec(SPEC)
    const = _const(spec)
    gwp = gwp_from_spec(spec)
    reg = load_parameter_csv(PARAMS, allow_unverified=False)
    inputs, fracs, facts, notes = build_inputs(spec, reg, const)
    OUT.mkdir(exist_ok=True)
    write_csv(F_INPUT, inputs)
    write_csv(F_FRAC, fracs)
    fact_cols = ["herd_id", "manure_management_system", "methane_conversion_factor_mcf",
                 "ch4_max_producing_capacity_bo", "n2o_ef3", "n2o_ef4", "n2o_ef5",
                 "nitrogen_fracgas", "nitrogen_fracleach", "registry_keys"]
    write_csv(F_FACT, facts, fact_cols)
    env = dict(os.environ)
    if os.environ.get("GHGSIM_R_LIBS"):
        env["R_LIBS"] = os.environ["GHGSIM_R_LIBS"]
    meta_json = OUT / f"_gleam_r_session_{TAG}.json"
    proc = subprocess.run([rscript, "--vanilla", str(R_DRIVER), str(F_INPUT), str(F_FRAC), str(F_FACT),
                           str(F_RAW), str(meta_json)], env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"GLEAM run failed:\n{proc.stdout}\n{proc.stderr}")
    rsess = json.loads(meta_json.read_text(encoding="utf-8"))
    meta_json.unlink()
    if rsess.get("gleam_version") != "0.8.0":
        raise SystemExit(f"unexpected gleam version {rsess.get('gleam_version')}")

    head = {r["herd_id"]: (r["farm_id"], r["factor_set"], r["head"]) for r in inputs if r["mapped"]}
    mapped = {(r["herd_id"], r["cohort_short"]) for r in inputs if r["mapped"]}
    n2o_missing = {(r["herd_id"]) for r in facts if r.get("_n2o_missing")}
    agg: dict[tuple[str, str], dict[str, float]] = {}
    with F_RAW.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r["herd_id"], r["cohort_short"]) not in mapped:
                continue
            fid, ver, n = head[r["herd_id"]]
            d = agg.setdefault((fid, ver), {"enteric_CH4": 0.0, "manure_CH4": 0.0, "manure_N2O": 0.0,
                                            "pasture_N2O": 0.0})
            k = 365.0 * n
            d["enteric_CH4"] += float(r["ch4_enteric"]) * k
            d["manure_CH4"] += (float(r["ch4_manure_other"]) + float(r["ch4_manure_pasture"])) * k
            d["manure_N2O"] += math.nan if r["herd_id"] in n2o_missing else float(r["n2o_manure_other_total"]) * k
            d["pasture_N2O"] += float(r["n2o_manure_pasture_total"]) * k
    ref = {}
    with GHGSIM_RESULTS.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ref[(r["farm_id"], r["source"])] = r
    rows = []
    for (fid, ver), d in agg.items():
        for src, gas in (("enteric_CH4", "CH4"), ("manure_CH4", "CH4"), ("manure_N2O", "N2O")):
            rr = ref[(fid, src)]
            gh = rr["ipcc2006_kg" if ver == "IPCC2006" else "ipcc2019_kg"]
            gh = float(gh) if gh not in ("", "nan", "NaN") else math.nan
            gl = d[src]
            ratio = gl / gh if gh and not math.isnan(gh) and not math.isnan(gl) else math.nan
            rows.append({"farm_id": fid, "factor_set": ver, "source": src, "gas": gas,
                         "gleam_kg": "" if math.isnan(gl) else round(gl, 4),
                         "ghgsim_kg": "" if math.isnan(gh) else round(gh, 4),
                         "gleam_over_ghgsim": "" if math.isnan(ratio) else round(ratio, 4),
                         "gleam_tCO2e": "" if math.isnan(gl) else round(gl * gwp[gas] / 1000, 4),
                         "gleam_pasture_N2O_kg": round(d["pasture_N2O"], 4) if src == "manure_N2O" else "",
                         "note": "consistency check, not validation"})
    write_csv(F_CMP, rows)
    manifest = {
        "version": TAG, "purpose": "GLEAM run unmodified as an outside model; consistency check, not validation",
        "gleam": {"package": "gleam", "version": rsess.get("gleam_version"), "tag": GLEAM_TAG,
                  "commit": GLEAM_COMMIT, "licence": "AGPL-3",
                  "source": f"https://codeload.github.com/un-fao/GLEAM/tar.gz/{GLEAM_COMMIT}",
                  "tarball_sha256": sha256(Path(os.environ["GHGSIM_GLEAM_TARBALL"]))
                  if os.environ.get("GHGSIM_GLEAM_TARBALL") else None,
                  "modified": False},
        "r": rsess, "python": platform.python_version(),
        "inputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p)
                   for p in (SPEC, PARAMS, GHGSIM_RESULTS, Path(cmp.__file__), Path(__file__), R_DRIVER)},
        "outputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p)
                    for p in (F_INPUT, F_FRAC, F_FACT, F_RAW, F_CMP)},
        "notes": notes,
        "not_run": "swine and poultry farms (no ration inputs in the spec); see DECISIONS_AN_v13",
    }
    F_MAN.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {F_CMP} ({len(rows)} rows) and {F_MAN}")


if __name__ == "__main__":
    main()
