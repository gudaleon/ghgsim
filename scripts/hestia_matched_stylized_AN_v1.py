"""Matched HESTIA CE runs on the ghgsim stylized farms (AN_v1).

Consistency check, not validation. HESTIA CE (local Docker, drafts route:
upload -> validate -> calculate) receives the same activity data and site inputs
that ghgsim's IPCC 2006/2019 comparison uses (scripts/compare_ipcc_2006_2019_stylized_AN_v2.py,
data/stylized_farms_AN_v6.yaml). No Earth Engine; site values are supplied and labelled
methodClassification = "regional statistical data" (HESTIA rejects "unsourced assertion").

Shared inputs passed to HESTIA per farm (see docs/HESTIA_MATCHED_AN_v1.md for the mapping):
- head per herd (liveAnimal terms), excreta kg N = head x Nex (ghgsim nex_kg_yr),
  excreta kg VS = head x VS_kg_day x 365 (cattle: IPCC 2006 Eq 10.24 from ghgsim GE;
  monogastrics: spec VS_kg_day), one excretaManagement practice at 100 %.
- site: ecoClimateZone 1 (Warm Temperate Moist) and temperatureAnnual 15 C, the zone
  ghgsim's 2019 run uses (spec meta.climate_zone 15C + wet fields).
- crop_urea_lime: per-ha F_SN (unspecified inorganic N), limestone, dolomite, maize yield.
HESTIA gap-fills everything else with its own models; that is part of what is compared.

Usage:
  python scripts/hestia_matched_stylized_AN_v1.py build   # writes inputs JSON + activity CSV
  python scripts/hestia_matched_stylized_AN_v1.py run     # submits to HESTIA CE, writes outputs
Env: HESTIA_API (default http://localhost/api).
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
_spec = importlib.util.spec_from_file_location("cmp19", ROOT / "scripts" / "compare_ipcc_2006_2019_stylized_AN_v2.py")
cmp19 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmp19)  # type: ignore[union-attr]

SPEC = cmp19.SPEC
GHG_CSV = cmp19.OUT_CSV
DATA = ROOT / "data"
IN_JSON = DATA / "hestia_matched_inputs_AN_v1.json"
ACT_CSV = DATA / "hestia_matched_activity_AN_v1.csv"
RAW_CSV = DATA / "hestia_matched_emissions_raw_AN_v1.csv"
OUT_CSV = DATA / "hestia_matched_vs_ipcc_stylized_AN_v1.csv"
MANIFEST = DATA / "hestia_matched_manifest_AN_v1.json"
API = os.environ.get("HESTIA_API", "http://localhost/api")
RSD = "regional statistical data"
YEAR = "2022"
DMC = "ghgsim stylized-farm activity data (data/stylized_farms_AN_v6.yaml; IPCC/EPA/NRC-cited, some ILLUSTRATIVE)"

LIVE_ANIMAL = {
    "dairy_cow": "dairyCattleCowLactating", "dairy_heifer": "dairyCattleHeifer", "dairy_calf": "dairyCattleCalf",
    "beef_cow": "beefCattleCow", "beef_calf": "beefCattleCalf", "broilers": "broilerChicken",
    "layers": "layerChickenHen", "turkeys": "turkey", "market_swine": "pig", "breeding_swine": "pigSow",
}
EXCRETA = {  # animal_type -> HESTIA excreta term stem
    "dairy": "excretaDairyCattle", "beef": "excretaBeefCattleExceptFeedlotFed", "market_swine": "excretaPigs",
    "breeding_swine": "excretaPigs", "broilers": "excretaPoultry", "layers": "excretaPoultry", "turkeys": "excretaTurkeys",
}
# ghgsim IPCC paths keep MCF liquid_nocrust for covered variants (cover factor is a Holos-only fork),
# so all liquid variants map to the same HESTIA system.
MMS = {
    "liquid_nocrust": "liquidSlurryWithoutNaturalCrustCover", "poultry_with_litter": "poultryManureWithLitter",
    "poultry_without_litter": "poultryManureWithoutLitter", "pit": "pitStorageBelowAnimalConfinements",
    "pasture": "pastureRangePaddockExcretaManagement",
}
PRIMARY = {"dairy": "milkCowRaw", "beef_cowcalf": "meatBeefCattleLiveweight", "poultry_broilers": "meatChickenLiveweight",
           "poultry_layers": "eggsHenInShell", "poultry_turkeys": "meatTurkeyLiveweight", "swine": "meatPigLiveweight"}
SKIP_FIELDS = {"broiler_linked", "swine_linked"}  # linked manure-N fields: not mapped in v1 (see doc)


def term(i, tt=None):
    t = {"@type": "Term", "@id": i}
    if tt:
        t["termType"] = tt
    return t


def meas(i, v, **kw):
    return {"@type": "Measurement", "term": term(i, "measurement"), "value": [v], "methodClassification": RSD, **kw}


def site_node(fid, site_type):
    return {"id": f"site-{fid}", "type": "Site", "siteType": site_type, "defaultSource": {"id": "ghgsim-src", "type": "Source"},
            "country": term("GADM-USA", "region"), "dataPrivate": True,
            "measurements": [meas("ecoClimateZone", 1),
                             meas("temperatureAnnual", 15, startDate=f"{YEAR}-01-01", endDate=f"{YEAR}-12-31")]}


def herd_activity(spec, farm, const):
    rows = []
    for cid in farm.get("herds") or []:
        a = spec["animal_classes"][cid]
        head = float(a["head"]["value"])
        at = str(a["animal_type"])
        nex = cmp19.nex_kg_yr(spec, a, const)
        if at in cmp19.MONOGASTRIC:
            vs, ge = float(a["VS_kg_day"]["value"]), None
        else:
            diet = spec["diets"][farm["diet_id"]]
            de, _t, _f = cmp19.herd_de_tdn(spec, farm, a, diet)
            e = cmp19.net_energy(spec, a, const, de)
            ge = cmp19.ge_eq_10_16(e, de)
            ue = 0.02 if de >= const["ue_ipcc_de_threshold"] else 0.04
            vs = cmp19.vs_eq_10_24(ge, de, const["ASH_percent"], ue)
        milk = float(a.get("milk_lb_cow_yr", {}).get("value", 0.0)) * float(spec["meta"]["lb_to_kg"])
        rows.append({"farm_id": farm["id"], "herd": cid, "animal_type": at, "liveAnimal": LIVE_ANIMAL[cid], "head": head,
                     "Nex_kg_head_yr": nex, "VS_kg_head_day": vs, "GE_MJ_head_day": ge, "milk_kg_head_yr": milk,
                     "excreta_kgN": head * nex, "excreta_kgVS": head * vs * 365.0})
    return rows


def primary_product(farm, herds):
    ft = farm["farm_type"]
    if ft == "dairy":
        return "milkCowRaw", sum(h["head"] * h["milk_kg_head_yr"] for h in herds)
    if ft == "poultry":
        return PRIMARY["poultry_" + herds[0]["animal_type"]], None
    return PRIMARY.get(ft), None


def build():
    spec = cmp19.load_stylized_spec(SPEC)
    const = cmp19._const(spec)
    nodes = [{"id": "actor-alex-neumann", "type": "Actor", "name": "Alex Neumann", "firstName": "Alex", "lastName": "Neumann", "dataPrivate": True},
             {"id": "ghgsim-src", "type": "Source", "name": "ghgsim stylized farms AN_v6 (matched HESTIA run AN_v1)",
              "bibliography": {"type": "Bibliography", "name": "ghgsim stylized farms AN_v6",
                               "title": "ghgsim stylized farms AN_v6, data/stylized_farms_AN_v6.yaml",
                               "authors": [{"id": "actor-alex-neumann", "type": "Actor"}], "outlet": "ghgsim repository (gudaleon/ghgsim)",
                               "year": 2026}}]
    act, mapped = [], []
    for farm in spec["farms"]:
        fid = farm["id"]
        if farm.get("field_id") in SKIP_FIELDS:
            continue
        herds = herd_activity(spec, farm, const)
        if herds:
            msys = list(spec["manure_variants"][farm["manure_id"]]["systems"])
            assert len(msys) == 1, fid
            mms = MMS[msys[0]]
            pasture = msys[0] == "pasture"
            nodes.append(site_node(fid, "permanent pasture" if pasture else "animal housing"))
            stem = EXCRETA[herds[0]["animal_type"]]
            assert all(EXCRETA[h["animal_type"]] == stem for h in herds), fid
            kgn, kgvs = sum(h["excreta_kgN"] for h in herds), sum(h["excreta_kgVS"] for h in herds)
            pid, pval = primary_product(farm, herds)
            prod = {"@type": "Product", "term": term(pid, "animalProduct"), "primary": True}
            # Placeholder 1 kg when ghgsim has no output quantity: only links the Cycle to an
            # ImpactAssessment so HESTIA calculates it; cycle-level emissions are compared, not per-product ones.
            prod["value"] = [round(pval, 3) if pval else 1.0]
            ex_n = {"@type": "Input", "term": term(stem + "KgN", "excreta"), "value": [round(kgn, 4)]}
            ex_vs = {"@type": "Input", "term": term(stem + "KgVs", "excreta"), "value": [round(kgvs, 4)]}
            cyc = {"id": f"cycle-{fid}", "type": "Cycle", "site": {"id": f"site-{fid}", "type": "Site"},
                   "defaultSource": {"id": "ghgsim-src", "type": "Source"}, "functionalUnit": "relative", "startDateDefinition": "start of year",
                   "defaultMethodClassification": "modelled", "defaultMethodClassificationDescription": DMC,
                   "startDate": f"{YEAR}-01-01", "endDate": f"{YEAR}-12-31", "cycleDuration": 365, "dataPrivate": True,
                   "completeness": {"@type": "Completeness", "animalFeed": False, "animalPopulation": True, "cropResidue": True,
                                    "electricityFuel": False, "excreta": True, "fertiliser": True, "freshForage": False,
                                    "ingredient": True, "liveAnimalInput": False, "material": False, "operation": False,
                                    "otherChemical": False, "pesticideVeterinaryDrug": False, "product": False, "seed": True,
                                    "soilAmendment": True, "transport": False, "waste": True, "water": False},
                   "animals": [{"@type": "Animal", "animalId": f"{fid}-{h['herd']}", "term": term(h["liveAnimal"], "liveAnimal"), "value": h["head"],
                                "referencePeriod": "average"} for h in herds],
                   "practices": [{"@type": "Practice", "term": term(mms, "excretaManagement"), "value": [100]}],
                   "inputs": [ex_n, ex_vs], "products": [prod]}
            nodes.append(cyc)
            act += herds
            mapped.append(fid)
        elif farm.get("field_id"):
            f = spec["fields"][farm["field_id"]]
            crops = cmp19._field_crops(f)
            assert len(crops) == 1, fid
            area = float(f["crops"][0]["area_ha"]["value"])
            yld = float(f["crops"][0]["yield_fresh_kg_ha"]["value"])
            fsn = cmp19._yaml_number(f.get("F_SN")) / area
            lime = cmp19._yaml_number(f.get("M_limestone_t")) * 1000 / area
            dolo = cmp19._yaml_number(f.get("M_dolomite_t")) * 1000 / area
            nodes.append(site_node(fid, "cropland"))
            inputs = [{"@type": "Input", "term": term("inorganicNitrogenFertiliserUnspecifiedKgN", "inorganicFertiliser"), "value": [fsn]}]
            if lime:
                inputs.append({"@type": "Input", "term": term("agriculturalLimestone", "soilAmendment"), "value": [lime]})
            if dolo:
                inputs.append({"@type": "Input", "term": term("dolomiticLime", "soilAmendment"), "value": [dolo]})
            nodes.append({"id": f"cycle-{fid}", "type": "Cycle", "site": {"id": f"site-{fid}", "type": "Site"},
                          "defaultSource": {"id": "ghgsim-src", "type": "Source"}, "functionalUnit": "1 ha", "startDateDefinition": "sowing date",
                          "defaultMethodClassification": "modelled", "defaultMethodClassificationDescription": DMC,
                          "startDate": f"{YEAR}-05-01", "endDate": f"{YEAR}-10-15", "cycleDuration": 168, "dataPrivate": True,
                          "completeness": {"@type": "Completeness", "animalFeed": True, "animalPopulation": True, "cropResidue": False,
                                           "electricityFuel": False, "excreta": True, "fertiliser": True, "freshForage": True,
                                           "ingredient": True, "liveAnimalInput": True, "material": False, "operation": False,
                                           "otherChemical": False, "pesticideVeterinaryDrug": False, "product": True, "seed": False,
                                           "soilAmendment": True, "transport": False, "waste": True, "water": True},
                          "inputs": inputs,
                          "products": [{"@type": "Product", "term": term("maizeGrain", "crop"), "value": [yld], "primary": True}]})
            act.append({"farm_id": fid, "herd": "", "animal_type": "crop", "liveAnimal": "", "head": "", "Nex_kg_head_yr": "",
                        "VS_kg_head_day": "", "GE_MJ_head_day": "", "milk_kg_head_yr": "", "excreta_kgN": "", "excreta_kgVS": "",
                        "area_ha": area, "F_SN_kgN_ha": fsn, "limestone_kg_ha": lime, "dolomite_kg_ha": dolo, "maize_kg_ha": yld})
            mapped.append(fid)
    IN_JSON.write_text(json.dumps({"nodes": nodes}, indent=1), encoding="utf-8")
    keys = ["farm_id", "herd", "animal_type", "liveAnimal", "head", "Nex_kg_head_yr", "VS_kg_head_day", "GE_MJ_head_day",
            "milk_kg_head_yr", "excreta_kgN", "excreta_kgVS", "area_ha", "F_SN_kgN_ha", "limestone_kg_ha", "dolomite_kg_ha", "maize_kg_ha"]
    with ACT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        for r in act:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    print(f"wrote {IN_JSON.name} ({len(nodes)} nodes, {len(mapped)} farms) and {ACT_CSV.name}")


def req(meth, path, data=None, headers=None):
    r = urllib.request.Request(API + path, data=data, method=meth, headers=headers or {})
    try:
        with urllib.request.urlopen(r, timeout=900) as f:
            return f.status, json.loads(f.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:2000]


# HESTIA emission term -> ghgsim source. Background (InputsProduction) terms are excluded.
SOURCE_RULES = [
    ("enteric_CH4", re.compile(r"^ch4ToAirEntericFermentation$")),
    ("manure_CH4", re.compile(r"^ch4ToAirExcreta$")),
    ("manure_N2O", re.compile(r"^n2OToAirExcreta(Direct|Indirect)$")),
    ("soil_N2O", re.compile(r"^n2OToAir(InorganicFertiliser|OrganicFertiliser|CropResidueDecomposition|SoilFlux|ExcretaOnPasture|NaturalVegetationBurning)?(Direct|Indirect)?$|^n2OToAir(InorganicFertiliser|OrganicFertiliser|CropResidueDecomposition)(Direct|Indirect)$")),
]


def classify(tid, site_type):
    for src, rx in SOURCE_RULES:
        if rx.match(tid):
            if src == "manure_N2O" and site_type == "permanent pasture":
                return "soil_N2O"  # PRP excreta N2O is soil N2O (F_PRP) in ghgsim
            return src
    return None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run():
    body = IN_JSON.read_bytes()
    s, ver = req("GET", "/version")
    bd = "----b" + uuid.uuid4().hex
    name = f"ghgsim-matched-AN-v1-{uuid.uuid4().hex[:6]}"
    mp = (f'--{bd}\r\nContent-Disposition: form-data; name="file"; filename="{name}.json"\r\n'
          "Content-Type: application/json\r\n\r\n").encode() + body + f"\r\n--{bd}--\r\n".encode()
    s, r = req("POST", "/drafts/upload", mp, {"Content-Type": "multipart/form-data; boundary=" + bd})
    print("upload", s, r)
    did = r["id"]
    for _ in range(120):
        s, d = req("GET", f"/drafts/{did}")
        if d.get("uploadStatus") in ("completed", "error"):
            break
        time.sleep(3)
    print("uploadStatus", d.get("uploadStatus"), d.get("uploadError"))
    print("validate", *req("PATCH", f"/drafts/{did}/validate"))
    for _ in range(120):
        s, d = req("GET", f"/drafts/{did}")
        if d.get("validationStatus") not in ("started", "pending", "running", "queued"):
            break
        time.sleep(3)
    print("validationStatus", d.get("validationStatus"))
    (DATA.parent / "_hestia_validation_last.json").write_text(json.dumps(d.get("validation"), indent=1), encoding="utf-8")
    print("calculate", *req("POST", f"/drafts/{did}/calculate"))
    for _ in range(360):
        s, d = req("GET", f"/drafts/{did}")
        cs = d.get("calculationStatus")
        if cs and cs not in ("started", "pending", "running", "queued", "in_progress", "idle"):
            break
        time.sleep(5)
    print("calculationStatus", cs)
    s, cy = req("GET", "/cycles?limit=200")
    mine = [c for c in cy["results"] if c.get("draftId") == did]
    status = {c["originalId"] if c.get("originalId") else c["id"]: c for c in mine}
    spec_nodes = {n["id"]: n for n in json.loads(body)["nodes"]}
    raw, agg = [], {}
    for c in mine:
        s, full = req("GET", f"/cycles/{c['id']}?dataState=recalculated")
        oid = full.get("originalId") or c["id"]
        fid = oid.replace("cycle-", "", 1)
        stype = spec_nodes[f"site-{fid}"]["siteType"]
        mult = 1.0
        if full.get("functionalUnit") == "1 ha":  # crop cycles are per ha; ghgsim totals over field area
            for row in csv.DictReader(ACT_CSV.open(encoding="utf-8")):
                if row["farm_id"] == fid and row["area_ha"]:
                    mult = float(row["area_ha"])
        if c["status"] != "completed":
            print("cycle", fid, c["status"], c.get("error"))
        for e in full.get("emissions", []) or []:
            tid = e["term"]["@id"]
            if "InputsProduction" in tid:
                continue
            if not re.match(r"^(ch4|n2O)ToAir", tid):
                continue
            v = sum(float(x) for x in e.get("value", []) if x is not None)
            src = classify(tid, stype)
            raw.append({"farm_id": fid, "hestia_term": tid, "value_kg": v * mult, "methodModel": e.get("methodModel", {}).get("@id", ""),
                        "methodTier": e.get("methodTier", ""), "ghgsim_source": src or "", "cycle_status": c["status"]})
            if src:
                agg[(fid, src)] = agg.get((fid, src), 0.0) + v * mult
    with RAW_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(raw[0]) if raw else ["farm_id"])
        w.writeheader()
        w.writerows(raw)
    gwp = {"CH4": 28.0, "N2O": 265.0}
    out = []
    mapped = {n["id"].replace("cycle-", "", 1) for n in spec_nodes.values() if n["type"] == "Cycle"}
    for g in csv.DictReader(GHG_CSV.open(encoding="utf-8")):
        if g["farm_id"] not in mapped:
            continue
        key = (g["farm_id"], g["source"])
        hv = agg.get(key)
        models = sorted({f"{r['methodModel']}({r['methodTier']})" for r in raw if (r["farm_id"], r["ghgsim_source"]) == key})
        def pct(a, b):
            try:
                a, b = float(a), float(b)
                return round(100 * (a - b) / b, 2) if b else ""
            except (TypeError, ValueError):
                return ""
        out.append({"farm_id": g["farm_id"], "source": g["source"], "gas": g["gas"], "ipcc2006_kg": g["ipcc2006_kg"],
                    "ipcc2019_kg": g["ipcc2019_kg"], "hestia_kg": "" if hv is None else round(hv, 4),
                    "hestia_tCO2e": "" if hv is None else round(hv * gwp[g["gas"]] / 1000, 4),
                    "pct_hestia_vs_2006": pct(hv, g["ipcc2006_kg"]), "pct_hestia_vs_2019": pct(hv, g["ipcc2019_kg"]),
                    "hestia_models": ";".join(models), "hestia_cycle_status": status.get(f"cycle-{g['farm_id']}", {}).get("status", "")})
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(out[0]))
        w.writeheader()
        w.writerows(out)
    s, data = req("GET", "/system/data")
    MANIFEST.write_text(json.dumps({
        "version": "AN_v1", "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "hestia_api": API, "draft_id": did,
        "hestia_version": ver, "glossary_pinned": data.get("pinned") if isinstance(data, dict) else None,
        "route": "drafts: /drafts/upload -> PATCH /drafts/{id}/validate -> POST /drafts/{id}/calculate (not /recalculate)",
        "earth_engine": "not configured (empty ee folder); site inputs supplied, methodClassification='regional statistical data'",
        "gwp_ar5": gwp, "framing": "consistency check, not validation",
        "inputs_sha256": {p.name: sha(p) for p in (SPEC, GHG_CSV, IN_JSON, ACT_CSV, ROOT / 'scripts' / 'compare_ipcc_2006_2019_stylized_AN_v2.py')},
        "outputs_sha256": {p.name: sha(p) for p in (RAW_CSV, OUT_CSV)},
        "skipped_farms": sorted(f["id"] for f in cmp19.load_stylized_spec(SPEC)["farms"] if f.get("field_id") in SKIP_FIELDS),
    }, indent=1), encoding="utf-8")
    print(f"wrote {OUT_CSV.name}, {RAW_CSV.name}, {MANIFEST.name}")


if __name__ == "__main__":
    {"build": build, "run": run}[sys.argv[1] if len(sys.argv) > 1 else "build"]()



