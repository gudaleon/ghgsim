"""Fill NASA POWER missing-value flags (-999) before writing APSIM .met files (AN_v1).

NASA POWER marks days without a value with -999 (found: ALLSKY_SFC_SW_DWN on isolated days, e.g. 1992-12-30
at 41.22 N 83.76 W). Passed through unchanged, -999 MJ/m2 radiation drives APSIM's soil-temperature solver out
of range ("newTemps(1) is outside range"), which was the cause of the AN_v1 Lake Erie 0 N failures on
1992-12-29 (FINDINGS_AN_v2). Each flagged value is replaced by the linear interpolation of the nearest valid
days before and after (the nearest valid day at a series end); every fill is returned so it can be recorded.
"""
from __future__ import annotations

import copy

MISSING = -999.0


def fill_power(power: dict) -> tuple[dict, list[dict]]:
    out = copy.deepcopy(power)
    fills = []
    for name, series in out["properties"]["parameter"].items():
        days = sorted(series)
        vals = [float(series[d]) for d in days]
        ok = [i for i, v in enumerate(vals) if v != MISSING]
        if not ok:
            continue
        for i, v in enumerate(vals):
            if v != MISSING:
                continue
            lo = max((j for j in ok if j < i), default=None)
            hi = min((j for j in ok if j > i), default=None)
            if lo is None or hi is None:
                new = vals[hi if lo is None else lo]
            else:
                new = vals[lo] + (vals[hi] - vals[lo]) * (i - lo) / (hi - lo)
            series[days[i]] = round(new, 2)
            fills.append({"parameter": name, "day": days[i], "filled": round(new, 2)})
    return out, fills