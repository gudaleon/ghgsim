"""Run INSIDE the HESTIA CE api container to dump the lookup values the ipcc2019 excreta N2O models read.

    docker exec -i hestia-ce-api python - < scripts/hestia_container/dump_n2o_lookups_AN_v1.py > data/hestia_n2o_lookups_AN_v1.json

Calls HESTIA's public lookup functions only; no HESTIA code is copied.
"""
import json
from hestia_earth.models.utils.term import get_lookup_value
from hestia_earth.utils.lookup import download_lookup, get_table_value

EX = ["excretaDairyCattleKgN", "excretaBeefCattleExceptFeedlotFedKgN", "excretaPoultryKgN", "excretaTurkeysKgN", "excretaPigsKgN"]
MG = ["liquidSlurryWithoutNaturalCrustCover", "poultryManureWithLitter", "poultryManureWithoutLitter",
      "pitStorageBelowAnimalConfinements", "pastureRangePaddockExcretaManagement"]
out = {"excreta": {}, "excretaManagement_EF_N2O-N": {}, "emission": {}, "NO3_EF_2019": {}}
for e in EX:
    t = {"@id": e, "termType": "excreta"}
    out["excreta"][e] = {k: get_lookup_value(t, k) for k in ["IPCC_2019_FRACGASM_NH3-N", "ipcc2019PrpCategory"]}
for m in MG:
    out["excretaManagement_EF_N2O-N"][m] = get_lookup_value({"@id": m, "termType": "excretaManagement"}, "EF_N2O-N")
for em, cols in {"n2OToAirExcretaDirect": ["IPCC_2019_EF3_PRP_CPP_FACTORS"],
                 "nh3ToAirExcreta": ["IPCC_2019_EF4_FACTORS"], "noxToAirExcreta": ["IPCC_2019_EF4_FACTORS"],
                 "no3ToGroundwaterExcreta": ["IPCC_2019_EF5_FACTORS"]}.items():
    out["emission"][em] = {k: get_lookup_value({"@id": em, "termType": "emission"}, k, model="ipcc2019", term=em) for k in cols}
lk = download_lookup("excretaManagement-excreta-NO3_EF_2019.csv")
for m in MG:
    out["NO3_EF_2019"][m] = {e: get_table_value(lk, "term.id", m, e) for e in EX}
print(json.dumps(out, default=str, indent=1))
