"""Webster tile vs no-tile with an impeding till boundary (AN_v1), FINDINGS_AN_v9. Consistency check, not validation.

Diagnosis of v3 (results/apsim_AN_v3): webster_tile and webster_seep are identical because the seepage lower
boundary lets the 2 m profile drain at its base as soon as the base node saturates (Cg ksat_r 9.17 um/s,
792 mm/d), so WaterTable stays at 2000 mm on every day and the drain at 1200 mm never runs (TileDrain = 0).
Webster (cokey 28627783) has no SSURGO corestrictions record, and no Iowa Webster major component has one.
Fix: replace the seepage face with SWIM's gradient boundary (q = (1 + gr) K, as run_apsim_lake_erie_AN_v3) with
gr = K_till / K_Cg - 1 from cited till conductivities below the profile, SpaceWeightingFactor 0.5 (as Lake Erie v3):
- weathered: oxidized Wisconsin (Des Moines Lobe) till in Iowa, pumping/bail-test mean bulk K 3e-4 cm/s = 3 um/s
  (Results of two pumping tests in Wisconsin age weathered till in Iowa, Ground Water 1992,
  doi:10.1111/j.1745-6584.1992.tb01529.x).
- unfractured: typical Ksat of till 1e-9 m/s = 0.001 um/s (Minnesota Stormwater Manual, Aquifer hydraulic
  properties, https://stormwater.pca.state.mn.us/aquifer_hydraulic_properties); a lower-bound sensitivity, flagged
  because the till below 2 m at the Boone site is oxidized and fractured (Young et al. 2019, doi:10.1007/s10040-019-02076-y).
Tile geometry unchanged (Malone et al. 2007). Usage: run_apsim_webster_drains_AN_v1.py weathered|unfractured [--tile-only]
Writes results/apsim_webster_drains_<case>_AN_v1/ (refuses to overwrite).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_apsim_crop_AN_v3 as r3  # noqa: E402

K_CG = 9.17
K_TILL = {"weathered": 3.0, "unfractured": 0.001}


def main() -> None:
    case = sys.argv[1]
    gr = K_TILL[case] / K_CG - 1.0
    r3.OUT = r3.ROOT / "results" / f"apsim_webster_drains_{case}_AN_v1"
    r3.CASES = {"webster_gr": {"soil": "webster", "swim": True, "tile": False, "seepage": True},
                "webster_gr_tile": {"soil": "webster", "swim": True, "tile": True, "seepage": True}}
    fs, fseep = r3.find_swim, r3.find_seepage

    def swim(apsim):
        t = fs(apsim)
        t["SpaceWeightingFactor"] = 0.5
        return t

    def grad(apsim):
        bc = copy.deepcopy(fseep(apsim))
        bc["Name"] = "SWIM3_SetLowerBC_gradient"
        for p in bc["Parameters"]:
            p["Value"] = {"LowerBCType": "gradient", "LowerBCValue": repr(gr)}[p["Key"]]
        j = next(k for k, ln in enumerate(bc["CodeArray"]) if "SetLowerBCForGradient(bbcGradient: 0.0)" in ln)
        bc["CodeArray"][j] = bc["CodeArray"][j].replace("bbcGradient: 0.0", "bbcGradient: LowerBCValue")
        return bc
    if "--tile-only" in sys.argv:  # undrained twin fails (SWIM saturates to the surface); keep the drained case
        r3.OUT = r3.OUT.with_name(r3.OUT.name.replace("_AN_v1", "_tileonly_AN_v1"))
        r3.CASES = {"webster_gr_tile": r3.CASES["webster_gr_tile"]}
    r3.find_swim, r3.find_seepage = swim, grad
    print("gr", gr)
    r3.main()


if __name__ == "__main__":
    main()