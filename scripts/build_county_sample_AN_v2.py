"""Expanded stratified county sample (AN_v2), research question (d), FINDINGS_AN_v2: same universe, strata and rules as\nbuild_county_pilot_sample_AN_v1, with 10 counties per stratum (5 x 2 x 10 = 100) instead of 2.

Universe: the 1,000 conterminous-US counties with May-Oct P/PE >= 0.3 (drier counties crop mainly under\nirrigation, which the rainfed pilot does not model) with the largest synthetic-fertiliser N input in the ghgsim county run
(data/us_county_2006_vs_2019_AN_v2.csv.gz, variant 'disclosed', soil_n2o_direct / synthetic_N; N input recovered
from the IPCC 2006 row as kg N2O / (0.01 x 44/28)). Strata: quintiles of growing-season (May-Oct) P/PE
(data/county_p_pe_may_oct_AN_v2.csv, Hargreaves) x drainage class of the dominant SSURGO component at the county
internal point (Census Gazetteer, data/county_climate_zones_AN_v1.csv): 'well' (excessively to moderately well
drained) or 'poor' (somewhat poorly to very poorly drained). Within each stratum, counties are taken in descending
N input until 2 have a complete SSURGO horizon record (all mapped fields present, >= 100 cm). (v2: 10 per stratum.)
Soil: SSURGO via Soil Data Access (same queries as fetch_iowa_site_AN_v1). Weather: NASA POWER daily 1991-2020.
Writes data/apsim_county_pilot_AN_v1/ (refuses to overwrite).
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_iowa_site_AN_v1 as f  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apsim_county_v2_AN_v1"
N_UNIVERSE, PER_CELL, NQ = 1000, 10, 5
MIN_PPE = 0.3  # drier counties crop mainly under irrigation; the pilot runs rainfed maize only
WELL = {"Excessively drained", "Somewhat excessively drained", "Well drained", "Moderately well drained"}
POOR = {"Somewhat poorly drained", "Poorly drained", "Very poorly drained"}
NEED = ["hzdept_r", "hzdepb_r", "dbthirdbar_r", "wthirdbar_r", "wfifteenbar_r", "wsatiated_r", "ksat_r", "om_r",
        "ph1to1h2o_r", "claytotal_r", "silttotal_r", "sandtotal_r"]
N2O_PER_N = 44 / 28


def n_input() -> dict[str, float]:
    out = {}
    with gzip.open(ROOT / "data" / "us_county_2006_vs_2019_AN_v2.csv.gz", "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["variant"] == "disclosed" and r["source"] == "soil_n2o_direct" and r["category"] == "synthetic_N":
                out[r["fips"]] = float(r["kg_2006"]) / (0.01 * N2O_PER_N)
    return out


def sda(q: str) -> list[dict]:
    try:
        return f.sda(q)
    except KeyError:  # Soil Data Access returns no "Table" for an empty result
        return []


def soil(lat: float, lon: float) -> dict | None:
    q = f.Q_COMP.replace(f"point({f.LON} {f.LAT})", f"point({lon} {lat})")
    comps = sda(q)
    if not comps:
        return None
    dom = comps[0]
    hz = [h for h in sda(f.Q_HZ.format(cokey=dom["cokey"])) if h["hzdepb_r"] is not None]
    if not hz or any(h[k] in (None, "") for h in hz for k in NEED) or float(hz[-1]["hzdepb_r"]) < 100:
        return None
    return {"source": "USDA-NRCS SSURGO via Soil Data Access", "url": f.SDA, "point_wgs84": [lat, lon],
            "queries": [q, f.Q_HZ], "components": comps, "dominant": dom, "horizons": hz}


def main() -> None:
    if (OUT / "county_sample_AN_v2.csv").exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    nin = n_input()
    with (ROOT / "data" / "county_p_pe_may_oct_AN_v2.csv").open(encoding="utf-8") as fh:
        ppe = {r["fips"]: float(r["p_over_pe_hargreaves"]) for r in csv.DictReader(fh)}
    with (ROOT / "data" / "county_climate_zones_AN_v1.csv").open(encoding="utf-8") as fh:
        cz = {r["fips"]: r for r in csv.DictReader(fh)}
    uni = [k for k in sorted(nin, key=nin.get, reverse=True) if k in ppe and k in cz and cz[k]["state"] not in ("AK", "HI") and ppe[k] >= MIN_PPE][:N_UNIVERSE]
    qs = sorted(ppe[k] for k in uni)
    cuts = [qs[int(len(qs) * i / NQ)] for i in range(1, NQ)]
    quint = {k: sum(ppe[k] >= c for c in cuts) for k in uni}
    got, tried = defaultdict(list), []
    OUT.mkdir(parents=True, exist_ok=True)  # resumable: counties already fetched are reused
    for k in uni:
        q = quint[k]
        if all(len(got[(q, d)]) >= PER_CELL for d in ("well", "poor")):
            continue
        lat, lon = float(cz[k]["lat_intpt"]), float(cz[k]["lon_intpt"])
        d = OUT / k
        if (d / "ssurgo_point_AN_v1.json").exists() and (d / "nasa_power_daily_1991_2020_AN_v1.json.gz").exists():
            s = json.loads((d / "ssurgo_point_AN_v1.json").read_text(encoding="utf-8"))
            got[(q, "well" if s["dominant"]["drainagecl"] in WELL else "poor")].append(k)
            tried.append({"fips": k, "drainagecl": s["dominant"]["drainagecl"], "complete": True, "reused": True})
            continue
        try:
            s = soil(lat, lon)
        except urllib.error.HTTPError as e:  # Soil Data Access rejected the query; record and move on
            tried.append({"fips": k, "drainagecl": None, "complete": False, "error": f"SDA HTTP {e.code}"})
            continue
        dc = s["dominant"]["drainagecl"] if s else None
        cls = "well" if dc in WELL else "poor" if dc in POOR else None
        tried.append({"fips": k, "drainagecl": dc, "complete": s is not None})
        if s is None or cls is None or len(got[(q, cls)]) >= PER_CELL:
            continue
        got[(q, cls)].append(k)
        d.mkdir(exist_ok=True)
        s["retrieved_utc"] = now
        (d / "ssurgo_point_AN_v1.json").write_text(json.dumps(s, indent=1) + "\n", encoding="utf-8")
        url = f.POWER.replace(f"longitude={f.LON}&latitude={f.LAT}", f"longitude={lon}&latitude={lat}")
        raw = urllib.request.urlopen(url, timeout=300).read()
        with gzip.GzipFile(d / "nasa_power_daily_1991_2020_AN_v1.json.gz", "wb", mtime=0) as fo:
            fo.write(raw)
        print(k, cz[k]["state"], cz[k]["county"], q, cls, dc, round(ppe[k], 3), flush=True)
        time.sleep(1)
    sample = [{"fips": k, "state": cz[k]["state"], "county": cz[k]["county"], "ppe_quintile": q, "drainage": cls,
               "p_over_pe_may_oct": ppe[k], "zone_primary": cz[k]["zone_primary"], "synthetic_N_kg": round(nin[k], 1),
               "lat": float(cz[k]["lat_intpt"]), "lon": float(cz[k]["lon_intpt"])}
              for (q, cls), ks in sorted(got.items()) for k in ks]
    with (OUT / "county_sample_AN_v2.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sample[0]))
        w.writeheader()
        w.writerows(sample)
    man = {"retrieved_utc": now, "universe": N_UNIVERSE, "ppe_quintile_cuts": cuts, "tried": tried,
           "sha256": {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob("*")) if p.is_file()}}
    (OUT / "county_sample_manifest_AN_v2.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    print(len(sample), "counties;", len(tried), "points queried")


if __name__ == "__main__":
    main()