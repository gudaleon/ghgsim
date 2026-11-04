"""APSIM Iowa (SSURGO + NASA POWER) consistency-check outputs, AN v1."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def test_manifest_site_and_soil_are_documented():
    m = _load("results/apsim_AN_v2/apsim_crop_manifest_AN_v2.json")
    soil = m["site"]["soil"]
    assert soil["mukey"] == "2835012" and soil["compname"] == "Webster"
    assert soil["areasymbol"] == "IA015"
    assert "SSURGO" in m["site"]["soil_source"]
    assert "NASA POWER" in m["site"]["weather_source"]
    assert m["site"]["met"]["days"] == 10958
    assert "Agricultural Handbook 628" in m["management"]["planting_source"]
    assert "KL" in m["borrowed_from_APSoil_900"]


def test_fertilised_run_exceeds_control():
    rows = {r["run"]: r for r in csv.DictReader(open(ROOT / "results/apsim_crop_pulses_AN_v2.csv", encoding="utf-8"))}
    assert float(rows["iowa"]["total_N2O_N_kgha"]) > float(rows["iowa_0N"]["total_N2O_N_kgha"])
    cmp_rows = list(csv.DictReader(open(ROOT / "results/apsim_vs_ghgsim_hestia_crop_AN_v2.csv", encoding="utf-8")))
    main = [r for r in cmp_rows if r["basis"].startswith("main: Boone County IA")]
    assert len(main) == 1 and 0 < float(main[0]["fertiliser_induced_EF_pct"]) < 5
    assert sum(r["basis"].startswith("sensitivity:") for r in cmp_rows) == 2


def test_fig6_v2_manifest():
    f = _load("figures/paperB_figures_manifest_AN_v7.json")
    assert "results/apsim_vs_ghgsim_hestia_crop_AN_v2.csv" in f["inputs_sha256"]
    assert (ROOT / "figures/fig6_four_way_AN_v2.png").exists()
