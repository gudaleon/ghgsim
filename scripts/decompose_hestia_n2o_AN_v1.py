"""Term-by-term decomposition of manure and pasture N2O: HESTIA CE v7.1.0 vs ghgsim IPCC 2019 (AN_v1 script).

Consistency check, not validation. For each stylized farm it splits N2O into direct, indirect-volatilisation and
indirect-leaching, and records the N basis and factor each model used.

    python scripts/decompose_hestia_n2o_AN_v1.py fetch   # needs the local HESTIA CE API; writes data/hestia_matched_nflows_AN_v1.csv
    python scripts/decompose_hestia_n2o_AN_v1.py build   # offline; writes data/hestia_matched_vs_ipcc_stylized_AN_v2.csv

Inputs (all in the repo):
- data/hestia_matched_nflows_AN_v1.csv (HESTIA recalculated excreta emissions, draft in hestia_matched_manifest_AN_v1.json)
- data/hestia_n2o_lookups_AN_v1.json (from scripts/hestia_container/dump_n2o_lookups_AN_v1.py)
- data/hestia_matched_activity_AN_v1.csv (excreta N supplied to HESTIA)
- ghgsim IPCC 2019 modules run exactly as in scripts/compare_ipcc_2006_2019_stylized_AN_v2.py
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NFLOWS = DATA / "hestia_matched_nflows_AN_v1.csv"
LOOKUPS = DATA / "hestia_n2o_lookups_AN_v1.json"
ACT = DATA / "hestia_matched_activity_AN_v1.csv"
MANIFEST = DATA / "hestia_matched_manifest_AN_v1.json"
OUT = DATA / "hestia_matched_vs_ipcc_stylized_AN_v2.csv"
API = os.environ.get("HESTIA_API", "http://localhost/api")
N2ON = 44.0 / 28.0
NH3_TO_N = 14.0 / 17.0
NOX_TO_N = 14.0 / 46.0  # HESTIA noxToAirExcreta is kg NOx (as NO2)
EXCRETA_TERMS = ["nh3ToAirExcreta", "noxToAirExcreta", "no3ToGroundwaterExcreta", "n2ToAirExcreta",
                 "n2OToAirExcretaDirect", "n2OToAirExcretaIndirect"]


def fetch() -> None:
    did = json.loads(MANIFEST.read_text(encoding="utf-8"))["draft_id"]
    g = lambda p: json.loads(urllib.request.urlopen(API + p, timeout=300).read())
    rows = []
    for c in [c for c in g("/cycles?limit=200")["results"] if c.get("draftId") == did]:
        full = g(f"/cycles/{c['id']}?dataState=recalculated")
        fid = (full.get("originalId") or c["id"]).replace("cycle-", "", 1)
        for e in full.get("emissions", []) or []:
            tid = e["term"]["@id"]
            if tid in EXCRETA_TERMS:
                rows.append({"farm_id": fid, "hestia_term": tid,
                             "value_kg": sum(float(x) for x in e.get("value", []) if x is not None),
                             "methodModel": e.get("methodModel", {}).get("@id", ""), "methodTier": e.get("methodTier", "")})
    rows.sort(key=lambda r: (r["farm_id"], r["hestia_term"]))
    with NFLOWS.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {NFLOWS} ({len(rows)} rows, draft {did})")


class _Rec:
    """Wrap a ghgsim module and keep its outputs (term split) per call."""

    def __init__(self, mod):
        self.mod, self.parameters, self.calls = mod, mod.parameters, []

    def compute(self, inputs, params):
        out = self.mod.compute(inputs, params)
        self.calls.append((dict(inputs), dict(params), out))
        return out


def ghgsim_terms() -> dict[str, dict]:
    spec_ = importlib.util.spec_from_file_location("cmp", ROOT / "scripts" / "compare_ipcc_2006_2019_stylized_AN_v2.py")
    cmp = importlib.util.module_from_spec(spec_)
    sys.path.insert(0, str(ROOT / "scripts"))
    spec_.loader.exec_module(cmp)
    spec = cmp.load_stylized_spec(cmp.SPEC)
    const = cmp._const(spec)
    reg = cmp.load_parameter_csv(cmp.latest_versioned(DATA, "ipcc_params", ".csv"), allow_unverified=False)
    ent, man, soil = cmp.MODULES["IPCC2019"]
    res = {}
    for farm in spec["farms"]:
        rm, rs = _Rec(man), _Rec(soil)
        cmp.MODULES["IPCC2019"] = (ent, rm, rs)
        cmp.run_version("IPCC2019", spec, farm, reg, const)
        cmp.MODULES["IPCC2019"] = (ent, man, soil)
        t = {"man_direct": 0.0, "man_vol": 0.0, "man_leach": 0.0, "N_managed": 0.0, "N_PRP": 0.0, "systems": set(), "factors": set()}
        for inp, p, o in rm.calls:
            t["man_direct"] += o["N2O_direct"]
            t["man_vol"] += o["N2O_indirect_vol"]
            t["man_leach"] += o["N2O_indirect_leach"]
            t["N_managed"] += o["N_managed_kg"]
            t["N_PRP"] += o["N_PRP_kg"]
            t["systems"].update(k for k, v in inp["systems"].items() if float(v) > 0)
            t["EF4_manure"] = p["EF4"]
            t["EF5_manure"] = p["EF5"]
        if rs.calls:
            inp, p, o = rs.calls[-1]
            t["soil"] = {"direct": o["N2O_direct"], "vol": o["N2O_indirect_vol"], "leach": o["N2O_indirect_leach"],
                         "F_PRP": inp["F_PRP_CPP"], "F_SN": inp["F_SN"], "F_ON": inp["F_ON"], "F_CR": inp["F_CR"],
                         "EF3PRP": p["EF3PRP_CPP_wet"], "EF4": p["EF4_wet"], "EF5": p["EF5"], "FracGASM": p["FracGASM"],
                         "FracLEACH": p["FracLEACH_wet"]}
        res[farm["id"]] = t
    return res


def build() -> None:
    lk = json.loads(LOOKUPS.read_text(encoding="utf-8-sig"))
    flows: dict[str, dict] = {}
    for r in csv.DictReader(NFLOWS.open(encoding="utf-8")):
        flows.setdefault(r["farm_id"], {})[r["hestia_term"]] = (float(r["value_kg"]), r["methodModel"])
    nin: dict[str, float] = {}
    for r in csv.DictReader(ACT.open(encoding="utf-8")):
        if r["excreta_kgN"]:
            nin[r["farm_id"]] = nin.get(r["farm_id"], 0.0) + float(r["excreta_kgN"])
    ef4_wet = float(lk["emission"]["nh3ToAirExcreta"]["IPCC_2019_EF4_FACTORS"].split("wet:")[1].split(";")[0])
    gs = ghgsim_terms()
    rows = []

    def add(fid, source, term, g_kg, h_kg, g_basis, g_factor, h_basis, h_factor, h_model, ref, why):
        d = (h_kg - g_kg) if (h_kg is not None and g_kg is not None) else None
        rows.append({"farm_id": fid, "source": source, "term": term,
                     "ghgsim2019_kg_N2O": None if g_kg is None else round(g_kg, 3),
                     "hestia_kg_N2O": None if h_kg is None else round(h_kg, 3),
                     "hestia_minus_ghgsim_kg": None if d is None else round(d, 3),
                     "ghgsim_N_basis_kg": g_basis, "ghgsim_factor": g_factor,
                     "hestia_N_basis_kg": h_basis, "hestia_factor": h_factor, "hestia_flow_model": h_model,
                     "ipcc2019_reference": ref, "explanation": why})

    for fid, f in sorted(flows.items()):
        if fid not in gs or fid not in nin:
            continue
        t, n_h = gs[fid], nin[fid]
        nh3 = f.get("nh3ToAirExcreta", (0.0, ""))
        nox = f.get("noxToAirExcreta", (0.0, ""))
        no3 = f.get("no3ToGroundwaterExcreta")
        dirv = f.get("n2OToAirExcretaDirect", (None, ""))[0]
        indv = f.get("n2OToAirExcretaIndirect", (None, ""))[0]
        nvol_h = nh3[0] * NH3_TO_N + nox[0] * NOX_TO_N
        if fid == "beef_pasture_field":
            s = t["soil"]
            ef3_h = dirv / N2ON / n_h
            add(fid, "soil_N2O(PRP)", "direct", s["direct"], dirv, round(s["F_PRP"], 2), f"EF3PRP,CPP wet={s['EF3PRP']}",
                round(n_h, 2), f"EF3PRP,CPP wet={ef3_h:.4f} (implied)", "ipcc2019",
                "2019 Vol4 Ch11 Table 11.1 (Updated): EF3PRP,CPP wet 0.006",
                "Same EF; gap is the N basis only: ghgsim 2019 F_PRP uses 2019 Nex, HESTIA was given the 2006-based Nex in the activity CSV.")
            add(fid, "soil_N2O(PRP)", "indirect_volatilisation", s["vol"], 0.0 if indv is None else indv,
                round(s["F_PRP"], 2), f"FracGASM={s['FracGASM']}; EF4 wet={s['EF4']}",
                round(nvol_h, 1), f"NH3 {nh3[1]} + NOx {nox[1]}; EF4 wet={ef4_wet}", "ipcc2019 n2OToAirExcretaIndirect: not run",
                "2019 Vol4 Ch11 Table 11.3 (Updated): FracGASM 0.21, EF4 wet 0.014",
                "HESTIA computed NH3/NOx from grazing but returned no n2OToAirExcretaIndirect: the model requires no3ToGroundwaterExcreta, which was not produced for this PRP cycle (PRP leaching needs site leaching inputs not supplied). Counted as 0.")
            add(fid, "soil_N2O(PRP)", "indirect_leaching", s["leach"], 0.0 if no3 is None else no3[0] * 0,
                round(s["F_PRP"], 2), f"FracLEACH-(H) wet={s['FracLEACH']}; EF5={s['EF5']}",
                None, "no3ToGroundwaterExcreta not returned", "none",
                "2019 Vol4 Ch11 Table 11.3 (Updated): FracLEACH-(H) 0.24, EF5 0.011",
                "Missing in HESTIA output (see above). Counted as 0.")
            continue
        ef_mgmt = lk["excretaManagement_EF_N2O-N"]
        h_ef3 = dirv / N2ON / n_h if dirv is not None and n_h else None
        sysdesc = "+".join(sorted(t["systems"]))
        g_ef3 = t["man_direct"] / N2ON / t["N_managed"] if t["N_managed"] else None
        g_fg = t["man_vol"] / N2ON / t["EF4_manure"] / t["N_managed"] if t["N_managed"] else None
        nbasis_note = ("" if abs(t["N_managed"] - n_h) < 0.5 else
                       f" N basis differs: ghgsim 2019 {t['N_managed']:.0f} kg N vs {n_h:.0f} kg N supplied to HESTIA.")
        add(fid, "manure_N2O", "direct", t["man_direct"], dirv, round(t["N_managed"], 1), f"EF3={g_ef3:.4f} ({sysdesc})",
            round(n_h, 1), f"EF_N2O-N={h_ef3:.4f} (implied)", "ipcc2019", "2019 Vol4 Ch10 Table 10.21 (Updated)",
            ("ghgsim splits the farm's real MMS mix; HESTIA was given one MMS (v1 mapping)." if g_ef3 is not None and h_ef3 is not None and abs(g_ef3 - h_ef3) > 1e-4 else "Same EF3.") + nbasis_note)
        frac_h = nvol_h / n_h if n_h else None
        add(fid, "manure_N2O", "indirect_volatilisation", t["man_vol"], indv, round(t["N_managed"], 1),
            f"FracGasMS={g_fg:.3f}; EF4={t['EF4_manure']}", round(n_h, 1),
            f"(NH3-N+NOx-N)/N={frac_h:.3f}; EF4 wet={ef4_wet}", f"NH3 {nh3[1]}; NOx {nox[1]}",
            "2019 Vol4 Ch10 Table 10.22 (Updated) FracGasMS; Ch11 Table 11.3 (Updated) EF4",
            "HESTIA does not use IPCC FracGasMS: NH3 comes from EMEP/EEA 2019 and NOx from Daemmgen 2009, giving a much smaller volatilised-N fraction; it then applies EF4 wet 0.014." + nbasis_note)
        add(fid, "manure_N2O", "indirect_leaching", t["man_leach"], 0.0 if no3 is None else 0.0,
            round(t["N_managed"], 1), f"FracLeachMS-weighted; EF5={t['EF5_manure']}", round(n_h, 1),
            f"NO3_EF_2019={'0' if no3 is not None and no3[0] == 0 else 'n/a'}; EF5=0.011", "ipcc2019",
            "2019 Vol4 Ch10 Table 10.22 (Updated) FracLeachMS; Ch11 Table 11.3 EF5 0.011",
            "Both 0 for liquid, pit and poultry litter systems (Table 10.22 FracLeachMS = 0); ghgsim is non-zero only where the farm's MMS mix includes solid storage or dry lot.")
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    {"fetch": fetch, "build": build}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
