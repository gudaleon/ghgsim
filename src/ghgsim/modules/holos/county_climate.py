"""County May-October P and PE lookup for HOLOS.N2O.ef1 = holos_liang2020.

Reads data/county_p_pe_may_oct_AN_v2.csv (NOAA nClimDiv 1991-2020,
doi:10.7289/V5M32STR; PE = Hargreaves-Samani 1985 / FAO-56 Eq 52). Built by
scripts/build_county_p_pe_AN_v2.py; see docs/COUNTY_P_PE_AN_v2.md.
"""

import csv
from functools import lru_cache
from pathlib import Path

COUNTY_P_PE_FILE = Path(__file__).resolve().parents[3].parent / "data" / "county_p_pe_may_oct_AN_v2.csv"


def normalize_fips(fips) -> str:
    s = str(fips).strip()
    if not s.isdigit() or len(s) > 5:
        raise ValueError(f"county_fips must be up to 5 digits, got {fips!r}")
    return s.zfill(5)


@lru_cache(maxsize=4)
def _table(path: str) -> dict:
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["fips"]: r for r in csv.DictReader(fh)}


def county_p_pe(fips, path: Path | str = COUNTY_P_PE_FILE) -> dict | None:
    """Return {'growing_season_precip_mm', 'growing_season_pe_mm', ...} or None if absent."""
    row = _table(str(path)).get(normalize_fips(fips))
    if row is None:
        return None
    return {
        "growing_season_precip_mm": float(row["growing_season_precip_mm"]),
        "growing_season_pe_mm": float(row["growing_season_pe_mm"]),
        "pe_thornthwaite_mm": float(row["pe_thornthwaite_mm"]),
        "pe_method": row["pe_method"],
        "period": row["period"],
        "n_years": int(row["n_years"]),
    }
