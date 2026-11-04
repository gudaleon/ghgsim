"""Ontario soils from CanSIS for the Lake Erie Brookston site and the Ontario county set (AN_v1).

Sources (all public, read-only):
- Soil Landscapes of Canada v3.2 (SLC), AAFC CanSIS: polygons + component table (ca_all_slc_v3r2*.dbf),
  https://sis.agr.gc.ca/nsdb/ca/cac003/cac003.20110308.v3.2/ca_all_slc_v3r2.zip
- CanSIS Ontario Soil Name and Soil Layer tables v2r20140203 (soil_name_on / soil_layer_on).
  CanSIS notes that the layer table holds modal (representative) values per soil, not measured pedons.
- Ontario municipal boundaries, Land Information Ontario (Open Government Licence - Ontario):
  LIO_OPEN_DATA/LIO_Open03/MapServer/13 (upper tier and district) and /14 (lower and single tier).

Mapping to the SSURGO-shaped fields used by run_apsim_crop_AN_v2.build_soil (no value is invented):
BD -> dbthirdbar_r; KP33, KP1500, KP0 (% vol) -> wthirdbar_r, wfifteenbar_r, wsatiated_r;
KSAT (cm/h) x 10000/3600 -> ksat_r (um/s); ORGCARB x 1.724 -> om_r (build_soil divides by 1.724 again,
so OC is passed through unchanged); PH2 (pH in water) -> ph1to1h2o_r; TSAND/TSILT/TCLAY -> *total_r.
Profiles end at the CanSIS LDEPTH of the last layer (100 cm for Brookston); nothing is extrapolated below.
"""
from __future__ import annotations

import argparse
import gzip
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pyogrio

LIO = "https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer/{}/query"
SLC_URL = "https://sis.agr.gc.ca/nsdb/ca/cac003/cac003.20110308.v3.2/ca_all_slc_v3r2.zip"
LAYER_URL = "https://sis.agr.gc.ca/cansis/nsdb/soil/v2/snt/index.html"


def lio(layer: int, where: str) -> gpd.GeoDataFrame:
    q = urllib.parse.urlencode({"where": where, "outFields": "MUNICIPAL_NAME,MUNICIPAL_TYPE,MUNID", "f": "geojson",
                                "outSR": "4326", "returnGeometry": "true", "maxAllowableOffset": "0.0005"})
    req = urllib.request.Request(LIO.format(layer) + "?" + q, headers={"User-Agent": "ghgsim-research"})
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    gj = json.loads(raw)
    return gpd.GeoDataFrame.from_features(gj["features"], crs="EPSG:4326")


def municipalities() -> gpd.GeoDataFrame:
    up = lio(13, "MUNICIPAL_TYPE = 'Upper Tier Municipality'")
    st = lio(14, "MUNICIPAL_TYPE = 'Single Tier Municipality'")
    return gpd.GeoDataFrame(gpd.pd.concat([up, st], ignore_index=True), crs="EPSG:4326")


def horizons(soil_id: str, layers) -> list[dict]:
    out = []
    for _, r in layers[layers.SOIL_ID == soil_id].sort_values("LAYER_NO").iterrows():
        vals = [r.BD, r.KP33, r.KP1500, r.KP0, r.KSAT, r.ORGCARB, r.PH2, r.TSAND, r.TSILT, r.TCLAY]
        if any(v is None or float(v) < 0 for v in vals):
            return []
        hzn = "".join(str(x) for x in (r.HZN_MAS, r.HZN_SUF) if isinstance(x, str))
        out.append({"hzname": hzn, "hzdept_r": str(int(r.UDEPTH)), "hzdepb_r": str(int(r.LDEPTH)),
                    "dbthirdbar_r": str(r.BD), "wthirdbar_r": str(r.KP33), "wfifteenbar_r": str(r.KP1500),
                    "wsatiated_r": str(r.KP0), "ksat_r": str(round(float(r.KSAT) * 10000 / 3600, 4)),
                    "om_r": str(round(float(r.ORGCARB) * 1.724, 4)), "ph1to1h2o_r": str(r.PH2),
                    "sandtotal_r": str(r.TSAND), "silttotal_r": str(r.TSILT), "claytotal_r": str(r.TCLAY),
                    "cansis_ksat_cm_h": float(r.KSAT), "cansis_orgcarb_pct": float(r.ORGCARB)})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="D:/cache_AN/cansis")
    ap.add_argument("--out", default="data/ontario_soils_AN_v1")
    a = ap.parse_args()
    c = Path(a.cache)
    names = pyogrio.read_dataframe(c / "soil_name_on_v2r20140203.dbf", read_geometry=False)
    layers = pyogrio.read_dataframe(c / "soil_layer_on_v2r20140203.dbf", read_geometry=False)
    cmp_ = pyogrio.read_dataframe(c / "slc/ca_all_slc_v3r2_cmp.dbf", read_geometry=False)
    cmp_ = cmp_[cmp_.PROVINCE == "ON"]
    slc = gpd.read_file(c / "slc/ca_all_slc_v3r2.shp")
    slc = slc[slc.POLY_ID.isin(cmp_.POLY_ID)].to_crs("EPSG:4326")
    mun = municipalities()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = {"retrieved_utc": now, "slc": SLC_URL, "soil_tables": "soil_name_on / soil_layer_on v2r20140203", "soil_tables_index": LAYER_URL,
            "boundaries": LIO.format("13|14"), "caveat": "CanSIS soil layer values are modal estimates for a named soil, not measured pedons."}

    # Essex County (Windsor area): area-weighted SLC composition (polygon area in Essex x component PERCENT).
    ek = mun[mun.MUNICIPAL_NAME.str.contains("ESSEX", case=False)]
    dom = cmp_.sort_values(["POLY_ID", "PERCENT"], ascending=[True, False]).drop_duplicates("POLY_ID")
    ov = gpd.overlay(slc, ek[["MUNICIPAL_NAME", "geometry"]], how="intersection")
    ov["area_km2"] = ov.to_crs("EPSG:3347").area / 1e6
    comp = ov[["POLY_ID", "area_km2", "geometry"]].merge(cmp_, on="POLY_ID")
    comp["cmp_km2"] = comp.area_km2 * comp.PERCENT / 100
    rank = comp.groupby("SOIL_ID").cmp_km2.sum().sort_values(ascending=False)
    total = float(ov.area_km2.sum())
    table = []
    for sid, km2 in rank.head(15).items():
        nmr = names[names.SOIL_ID == sid]
        table.append({"soil_id": sid, "soilname": nmr.SOILNAME.iloc[0] if len(nmr) else None,
                      "drainage": nmr.DRAINAGE.iloc[0] if len(nmr) else None, "kind": nmr.KIND.iloc[0] if len(nmr) else None,
                      "pmtex1": nmr.PMTEX1.iloc[0] if len(nmr) else None, "area_km2": round(float(km2), 1),
                      "share_pct": round(100 * float(km2) / total, 1), "n_layers": len(horizons(sid, layers))})
        print(table[-1])
    sites = {}
    for sid in [t["soil_id"] for t in table if t["n_layers"]][:6]:
        sub = comp[comp.SOIL_ID == sid].sort_values("cmp_km2", ascending=False).iloc[0]
        pt = sub.geometry.representative_point()
        nm = names[names.SOIL_ID == sid].iloc[0]
        sites[sid] = {**meta, "county": "Essex", "slc_poly_id": int(sub.POLY_ID), "component_percent": int(sub.PERCENT),
                      "soil_id": sid, "soilname": nm.SOILNAME, "drainage": nm.DRAINAGE, "watertbl": nm.WATERTBL,
                      "parent_material": [nm.PMTEX1, nm.MDEP1], "classification": [nm.ORDER3, nm.G_GROUP3, nm.S_GROUP3],
                      "point_wgs84": [round(pt.y, 4), round(pt.x, 4)], "horizons": horizons(sid, layers)}
    (out / "cansis_essex_composition_AN_v1.json").write_text(json.dumps({**meta, "essex_area_km2": round(total, 1), "ranking": table}, indent=1))
    (out / "cansis_essex_sites_AN_v1.json").write_text(json.dumps(sites, indent=1))

    # Ontario counties: every upper/single-tier municipality south of 45.5 N; soil = dominant component of the SLC
    # polygon holding the municipality's representative point; skipped (and recorded) when CanSIS layers are missing.
    rows = []
    for _, m in mun.iterrows():
        p = m.geometry.representative_point()
        if p.y > 45.5:
            continue
        hit = slc[slc.contains(p)]
        rec = {"municipality": m.MUNICIPAL_NAME, "type": m.MUNICIPAL_TYPE, "munid": m.MUNID, "point_wgs84": [round(p.y, 4), round(p.x, 4)]}
        if hit.empty:
            rows.append({**rec, "skip": "no SLC polygon at point"})
            continue
        d = dom[dom.POLY_ID == hit.iloc[0].POLY_ID].iloc[0]
        nmr = names[names.SOIL_ID == d.SOIL_ID]
        hz = horizons(d.SOIL_ID, layers)
        rec.update({"slc_poly_id": int(d.POLY_ID), "soil_id": d.SOIL_ID, "component_percent": int(d.PERCENT),
                    "soilname": nmr.SOILNAME.iloc[0] if len(nmr) else None, "drainage": nmr.DRAINAGE.iloc[0] if len(nmr) else None,
                    "kind": nmr.KIND.iloc[0] if len(nmr) else None, "horizons": hz})
        if not hz or (len(nmr) and nmr.KIND.iloc[0] != "M"):
            rec["skip"] = "no complete CanSIS mineral layer data"
        rows.append(rec)
    (out / "cansis_ontario_counties_AN_v1.json").write_text(json.dumps({**meta, "counties": rows}, indent=1))
    print("ontario", len(rows), "usable", sum("skip" not in r for r in rows))


if __name__ == "__main__":
    main()