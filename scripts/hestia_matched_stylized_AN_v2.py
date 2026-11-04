"""Matched HESTIA CE runs on the ghgsim stylized farms with IPCC 2019 Nex (outputs AN_v3; D20.4).

Consistency check, not validation. Same route, site and mapping as hestia_matched_stylized_AN_v1.py, with two
changes (docs/HESTIA_MATCHED_AN_v3.md):
  * excreta N per herd = head x the Nex that ghgsim's ipcc2019.manure itself uses: 2019 Table 10.19 (Updated)
    Nrate x TAM / 1000 x 365 (TAM = spec mass, cattle: Eq 10.x weight from net_energy), or the spec's EPA
    Nex override where present (as both ghgsim versions). v1 supplied the override-or-2006 Nex.
  * ghgsim comparison columns come from data/ipcc_2006_vs_2019_stylized_AN_v3.csv (climate EF4, DECISIONS_AN_v21).
Usage: python scripts/hestia_matched_stylized_AN_v2.py build|run    (refuses to overwrite)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("hm1", ROOT / "scripts" / "hestia_matched_stylized_AN_v1.py")
v1 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(v1)
cmp19 = v1.cmp19

from ghgsim.modules.ipcc2019.manure import IPCC2019Manure  # noqa: E402

D = v1.DATA
v1.IN_JSON = D / "hestia_matched_inputs_AN_v3.json"
v1.ACT_CSV = D / "hestia_matched_activity_AN_v3.csv"
v1.RAW_CSV = D / "hestia_matched_emissions_raw_AN_v3.csv"
v1.OUT_CSV = D / "hestia_matched_vs_ipcc_stylized_AN_v3.csv"
v1.MANIFEST = D / "hestia_matched_manifest_AN_v3.json"
v1.GHG_CSV = D / "ipcc_2006_vs_2019_stylized_AN_v3.csv"

_REG = cmp19.load_parameter_csv(cmp19.latest_versioned(D, "ipcc_params", ".csv"), allow_unverified=False)
_P19 = cmp19.resolve(IPCC2019Manure(), _REG)
_orig_herd_activity = v1.herd_activity


def nex_2019(spec, farm, a, const) -> float:
    """Nex exactly as ghgsim's 2019 manure run gets it (module output Nex_kg_head)."""
    at = str(a["animal_type"])
    if "Nex_kg_yr_override" in a:
        return float(cmp19.nex_kg_yr(spec, a, const))
    if at in cmp19.MONOGASTRIC:
        animal, tam = at, cmp19.animal_mass_kg(spec, a)
    else:
        diet = spec["diets"][farm["diet_id"]]
        de, _t, _f = cmp19.herd_de_tdn(spec, farm, a, diet)
        animal, tam = cmp19.CATTLE_AT[at], cmp19.net_energy(spec, a, const, de)["weight_kg"]
    systems = dict(spec["manure_variants"][farm["manure_id"]]["systems"]) if farm.get("manure_id") else {"pasture": 1.0}
    out = IPCC2019Manure().compute({"head": 1.0, "animal_type": animal, "region": "north_america", "VS_kg_day": 1.0,
                                    "TAM_kg": tam, "mcf_zone": spec["meta"]["climate_zone"], "systems": systems,
                                    "climate_zone_2019": cmp19.CLIMATE_ZONE_2019,
                                    "storage_months": cmp19.STORAGE_MONTHS}, _P19)
    return float(out["Nex_kg_head"])


def herd_activity(spec, farm, const):
    rows = _orig_herd_activity(spec, farm, const)
    for r in rows:
        nex = nex_2019(spec, farm, spec["animal_classes"][r["herd"]], const)
        r["Nex_kg_head_yr"], r["excreta_kgN"] = nex, float(r["head"]) * nex
    return rows


v1.herd_activity = herd_activity


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    outs = (v1.IN_JSON, v1.ACT_CSV) if mode == "build" else (v1.RAW_CSV, v1.OUT_CSV, v1.MANIFEST)
    for p in outs:
        if p.exists():
            raise SystemExit(f"refusing to overwrite {p}")
    {"build": v1.build, "run": v1.run}[mode]()


if __name__ == "__main__":
    main()
