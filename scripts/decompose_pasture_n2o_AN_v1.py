"""Term-by-term pasture (PRP) N2O: ghgsim soil module vs GLEAM v0.8.0-alpha outputs.

Diagnostic for beef_pasture_field (100% pasture, F_SN = F_SOM = F_CR = F_ON = 0, so ghgsim's
soil N2O is PRP N2O only). ghgsim terms are captured from the IPCC 2006 / 2019 soil modules
exactly as run by compare_ipcc_2006_2019_stylized_AN_v2.run_version; GLEAM terms are read from
the committed results/gleam_stylized_cohort_results_AN_v1.csv (per head per day x 365 x head).
No GLEAM code is used. Writes results/pasture_n2o_terms_gleam_vs_ghgsim_AN_v1.csv (never overwrites).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compare_ipcc_2006_2019_stylized_AN_v2 as cmp  # noqa: E402

FARM = "beef_pasture_field"
OUT = ROOT / "results" / "pasture_n2o_terms_gleam_vs_ghgsim_AN_v1.csv"
GLEAM_COHORT = ROOT / "results" / "gleam_stylized_cohort_results_AN_v1.csv"
GLEAM_INPUTS = ROOT / "results" / "gleam_stylized_inputs_AN_v1.csv"
TERMS = {  # ghgsim soil output key -> GLEAM cohort column
    "direct": ("N2O_direct", "n2o_manure_pasture_direct"),
    "indirect_volatilisation": ("N2O_indirect_vol", "n2o_manure_pasture_vol"),
    "indirect_leaching": ("N2O_indirect_leach", "n2o_manure_pasture_leach"),
    "total": ("N2O_total", "n2o_manure_pasture_total"),
}


def ghgsim_terms() -> dict[str, dict]:
    cap: dict[str, dict] = {}
    spec = cmp.load_stylized_spec(cmp.SPEC)
    const = cmp._const(spec)
    reg = cmp.load_parameter_csv(cmp.latest_versioned(cmp.ROOT / "data", "ipcc_params", ".csv"),
                                 allow_unverified=False)
    farm = next(f for f in spec["farms"] if f["id"] == FARM)
    for version, mods in cmp.MODULES.items():
        soil = mods[2]
        orig = soil.compute

        def wrapped(inp, p, _o=orig, _v=version):
            out = _o(inp, p)
            cap[_v] = {"inputs": dict(inp), "outputs": dict(out), "params": dict(p)}
            return out

        soil.compute = wrapped
        try:
            cmp.run_version(version, spec, farm, reg, const)
        finally:
            soil.compute = orig
    return cap


def gleam_terms() -> dict[str, dict[str, float]]:
    head, mapped = {}, {}
    with GLEAM_INPUTS.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["farm_id"] == FARM and r["mapped"] == "1":
                head[r["herd_id"]] = float(r["head"])
                mapped[r["herd_id"]] = r["cohort_short"]
    out: dict[str, dict[str, float]] = {}
    with GLEAM_COHORT.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            hid = r["herd_id"]
            if mapped.get(hid) != r["cohort_short"]:
                continue  # GLEAM needs 6 cohort rows per herd; only the mapped one is used
            d = out.setdefault(hid.rsplit("|", 1)[1], {t: 0.0 for t in TERMS})
            for t, (_g, col) in TERMS.items():
                d[t] += float(r[col]) * 365.0 * head[hid]
    return out


def build_rows() -> list[dict]:
    g = ghgsim_terms()
    gl = gleam_terms()
    rows = []
    for ver in ("IPCC2006", "IPCC2019"):
        o = g[ver]["outputs"]
        p = g[ver]["params"]
        ef4 = p.get("EF4_wet", p.get("EF4"))
        for t, (gk, _c) in TERMS.items():
            a, b = float(o[gk]), gl[ver][t]
            rows.append({
                "farm_id": FARM, "factor_set": ver, "term": t,
                "ghgsim_kg_N2O": round(a, 4), "gleam_kg_N2O": round(b, 4),
                "ghgsim_minus_gleam_kg": round(a - b, 4),
                "ghgsim_F_PRP_kgN": round(float(g[ver]["inputs"]["F_PRP_CPP"]), 4),
                "ghgsim_EF4_used": ef4,
            })
    return rows


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT} exists; bump the version instead of overwriting")
    rows = build_rows()
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
