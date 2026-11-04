"""County annual climate lookup (MAT, annual P/PE, IPCC climate zone).

Reads data/county_climate_annual_AN_v1.csv (NOAA nClimDiv 1991-2020, doi:10.7289/V5M32STR;
PE = Hargreaves-Samani 1985 / FAO-56 Eq 52, summed over 12 months). Built by
scripts/build_county_climate_annual_AN_v1.py. ``GHGSIM_ROOT`` overrides the repo root.
"""

import csv
import os
from functools import lru_cache
from pathlib import Path

_ROOT = Path(os.environ.get("GHGSIM_ROOT", Path(__file__).resolve().parents[3]))
COUNTY_CLIMATE_ANNUAL_FILE = _ROOT / "data" / "county_climate_annual_AN_v1.csv"


@lru_cache(maxsize=4)
def _table(path: str) -> dict:
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["fips"]: r for r in csv.DictReader(fh)}


def county_climate_annual(fips, path: Path | str = COUNTY_CLIMATE_ANNUAL_FILE) -> dict | None:
    """Return {'mean_annual_temp_c', 'moisture_ratio', 'ipcc_zone', ...} or None if absent."""
    s = str(fips).strip()
    if not s.isdigit() or len(s) > 5:
        raise ValueError(f"county_fips must be up to 5 digits, got {fips!r}")
    row = _table(str(path)).get(s.zfill(5))
    if row is None:
        return None
    return {
        "mean_annual_temp_c": float(row["mean_annual_temp_c"]),
        "moisture_ratio": float(row["annual_p_over_pe"]),
        "annual_precip_mm": float(row["annual_precip_mm"]),
        "annual_pe_hargreaves_mm": float(row["annual_pe_hargreaves_mm"]),
        "ipcc_zone": row["ipcc_zone"] or None,
        "period": row["period"],
    }
