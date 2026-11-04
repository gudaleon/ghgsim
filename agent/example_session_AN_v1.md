# Paper B paper agent: example session (AN_v1)

Produced by `agent/record_session_AN_v1.py`, which starts `agent/paper_agent_AN_v1.py` as an MCP
stdio server and calls its tools through the official `mcp` client. Outputs are verbatim tool
results (long ones truncated here only). No language model was involved in producing the numbers.

## Tools advertised

- `list_farms`: List the stylized farms (data/stylized_farms_AN_v6.yaml) that run_farm can simulate.
- `list_parameter_files`: List the versioned IPCC parameter registries (data/ipcc_params_AN_v*.csv).
- `run_farm`: Run a stylized farm live in ghgsim under IPCC2006, IPCC2019 or both.
- `committed_farm_result`: The committed Paper B numbers for a stylized farm (data/ipcc_2006_vs_2019_stylized_AN_v2.csv).
- `county_results`: US county IPCC 2006 vs 2019 results from the committed full run. Pass a 5-digit FIPS or a
- `county_climate_zone`: IPCC climate zone (2019 map, Hargreaves and Thornthwaite variants) and climate normals for a county.
- `explain_parameter`: Value, units, IPCC table, equation, page and source for a parameter key (exact or substring),
- `list_manifests`: List the committed results manifests (results/*.json).
- `provenance`: Provenance of a results manifest: commit, parameter file, upstream pins, which outputs
- `diff_manifests`: Which Paper B numbers moved between two results manifests, and why (scripts/diff_results_AN_v1.py).

## Q: What farms can I run?

`list_farms({})`

```json
{
 "farms": [
  {
   "farm_id": "dairy_forage_uncovered",
   "herds": [
    "dairy_cow",
    "dairy_heifer",
    "dairy_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_uncovered",
   "diet_id": "dairy_forage"
  },
  {
   "farm_id": "dairy_forage_covered_crust",
   "herds": [
    "dairy_cow",
    "dairy_heifer",
    "dairy_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_covered_crust",
   "diet_id": "dairy_forage"
  },
  {
   "farm_id": "dairy_forage_covered_solid",
   "herds": [
    "dairy_cow",
    "dairy_heifer",
    "dairy_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_covered_solid",
   "diet_id": "dairy_forage"
  },
  {
   "farm_id": "dairy_high_grain_uncovered",
   "herds": [
    "dairy_cow",
    "dairy_heifer",
    "dairy_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_uncovered",
   "diet_id": "dairy_high_grain"
  },
  {
   "farm_id": "dairy_high_grain_covered_crust",
   "herds": [
    "dairy_cow",
    "dairy_heifer",
    "dairy_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_covered_crust",
   "diet_id": "dairy_high_grain"
  },
  {
   "farm_id": "beef_cowcalf_uncovered",
   "herds": [
    "beef_cow",
    "beef_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_uncovered",
   "diet_id": "beef_forage"
  },
  {
   "farm_id": "beef_cowcalf_covered_crust",
   "herds": [
    "beef_cow",
    "beef_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_covered_crust",
   "diet_id": "beef_forage"
  },
  {
   "farm_id": "beef_cowcalf_covered_solid",
   "herds": [
    "beef_cow",
    "beef_calf"
   ],
   "field_id": null,
   "manure_id": "liquid_covered_solid",
   "diet_id": "beef_forage"
  },
  {
   "farm_id": "broiler_litter",
   "herds": [
    "broilers"
   ],
   "field_id": null,
   "manure_id": "poultry_with_litter",
   "diet_id": null
  },
  {
   "farm_id": "layer_litter",
   "herds": [
    "layers"
   ],
   "field_id": null,
   "manure_id": "poultry_with_litter",
   "diet_id": null
  },
  {
   "farm_id": "layer_highrise",
   "herds": [
    "layers"
   ],
   "field_id": null,
   "manure_id": "poultry_without_litter",
   "diet_id": null
  },
  {
   "farm_id": "turkey_litter",
   "herds": [
    "turkeys"
   ],
   "field_id": null,
   "manure_id": "poultry_with_litter",
   "diet_id": null
  },
  {
   "farm_id": "market_swine_liquid",
   "herds": [
    "market_swine"
   ],
   "field_id": null,
   "manure_id": "swine_liquid_uncovered",
   "diet_id": null
  },
  {
   "farm_id": "breeding_swine_liquid",
   "herds": [
    "breeding_swine"
   ],
   "field_id": null,
   "manure_id": "swine_liquid_uncovered",
   "diet_id": null
  },
  {
   "farm_id": "farrow_to_finish",
   "herds": [
    "breeding_swine",
    "market_swine"
   ],
   "field_id": null,
   "manure_id": "swine_pit",
   "diet_id": null
  },
  {
   "farm_id": "broiler_litter_field",
   "herds": [
    "broilers"
   ],
   "field_id": "broiler_linked",
   "manure_id": "poultry_with_litter",
   "diet_id": null
  },
  {
   "farm_id": "market_swine_field",
   "herds": [
    "market_swine"
   ],
   "field_id": "swine_linked",
   "manure_id": "swine_liquid_uncovered",
   "diet_id": null
  },
  {
   "farm_id": "beef_pasture_field",
   "herds": [
    "beef_cow",
    "beef_calf"
   ],
   "field_id": "prp_only",
   "manure_id": "cattle_pasture",
   "diet_id": "beef_forage"
  },
  {
   "farm_id": "crop_urea_lime",
   "herds": [],
   "field_id": "crop_urea_lime",
   "manure_id": null,
   "diet_id": null
  }
 ],
 "source": {
  "files": {
   "da
... [106 more characters truncated in this transcript only]
```

## Q: Run the forage dairy farm under both guidelines (parameter file used for the committed Paper B CSV).

`run_farm({"farm_id": "dairy_forage_uncovered", "params_file": "ipcc_params_AN_v8.csv"})`

```json
{
 "farm_id": "dairy_forage_uncovered",
 "results": {
  "IPCC2006": {
   "sources": {
    "enteric_CH4": {
     "kg": 18905.765313846572,
     "tCO2e": 529.361428787704,
     "gas": "CH4"
    },
    "manure_CH4": {
     "kg": 13173.39848996652,
     "tCO2e": 368.8551577190625,
     "gas": "CH4"
    },
    "manure_N2O": {
     "kg": 115.1191244007097,
     "tCO2e": 30.50656796618807,
     "gas": "N2O"
    },
    "soil_N2O": {
     "kg": 0.0,
     "tCO2e": 0.0,
     "gas": "N2O"
    }
   },
   "total_tCO2e_excl_missing": 928.7231544729545,
   "notes": []
  },
  "IPCC2019": {
   "sources": {
    "enteric_CH4": {
     "kg": 17536.78528306512,
     "tCO2e": 491.0299879258234,
     "gas": "CH4"
    },
    "manure_CH4": {
     "kg": 26834.700627709582,
     "tCO2e": 751.3716175758683,
     "gas": "CH4"
    },
    "manure_N2O": {
     "kg": 145.89427939283027,
     "tCO2e": 38.66198403910003,
     "gas": "N2O"
    },
    "soil_N2O": {
     "kg": 0.0,
     "tCO2e": 0.0,
     "gas": "N2O"
    }
   },
   "total_tCO2e_excl_missing": 1281.0635895407918,
   "notes": [
    "dairy_calf: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo",
    "dairy_cow: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo",
    "dairy_heifer: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo"
   ]
  },
  "change_2019_vs_2006_pct": 37.93815556023136
 },
 "settings": {
  "climate_zone_2019": "warm_temperate_moist",
  "storage_months": 12,
  "mcf_zone_2006": "15C"
 },
 "param_overrides": {},
 "gwp": "AR5 GWP100 from spec meta.gwp_ar5",
 "source": {
  "files": {
   "data/stylized_farms_AN_v6.yaml": "e4cedd9ee179e65252b5e72e7c78f3f427765ae0c596f63340c9774397074c3c",
   "data/ipcc_params_AN_v8.csv": "0e5180b19a069c9ded3db4eeed3764b2df405dff8799f91d34b6f775bf006792",
   "scripts/compare_ipcc_2006_2019_stylized_AN_v2.py": "482db7797eb647deccf050a817a328d8112854b988c6cb60eddc8a2f372a103c"
  },
  "engine": "ghgsim ipcc2006/ipcc2019 modules"
 }
}
```

## Q: Do those match the committed Paper B numbers?

`committed_farm_result({"farm_id": "dairy_forage_uncovered"})`

```json
{
 "rows": [
  {
   "farm_id": "dairy_forage_uncovered",
   "source": "enteric_CH4",
   "gas": "CH4",
   "ipcc2006_kg": "18905.7653",
   "ipcc2019_kg": "17536.7853",
   "ipcc2006_tCO2e": "529.3614",
   "ipcc2019_tCO2e": "491.03",
   "diff_tCO2e_2019_minus_2006": "-38.3314",
   "pct_change": "-7.24",
   "gwp_ar5": "28.0",
   "params_file": "ipcc_params_AN_v8.csv",
   "spec_file": "stylized_farms_AN_v6.yaml",
   "notes": "dairy_calf: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_cow: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_heifer: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo"
  },
  {
   "farm_id": "dairy_forage_uncovered",
   "source": "manure_CH4",
   "gas": "CH4",
   "ipcc2006_kg": "13173.3985",
   "ipcc2019_kg": "26834.7006",
   "ipcc2006_tCO2e": "368.8552",
   "ipcc2019_tCO2e": "751.3716",
   "diff_tCO2e_2019_minus_2006": "382.5165",
   "pct_change": "103.7",
   "gwp_ar5": "28.0",
   "params_file": "ipcc_params_AN_v8.csv",
   "spec_file": "stylized_farms_AN_v6.yaml",
   "notes": "dairy_calf: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_cow: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_heifer: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo"
  },
  {
   "farm_id": "dairy_forage_uncovered",
   "source": "manure_N2O",
   "gas": "N2O",
   "ipcc2006_kg": "115.1191",
   "ipcc2019_kg": "145.8943",
   "ipcc2006_tCO2e": "30.5066",
   "ipcc2019_tCO2e": "38.662",
   "diff_tCO2e_2019_minus_2006": "8.1554",
   "pct_change": "26.73",
   "gwp_ar5": "265.0",
   "params_file": "ipcc_params_AN_v8.csv",
   "spec_file": "stylized_farms_AN_v6.yaml",
   "notes": "dairy_calf: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_cow: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_heifer: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo"
  },
  {
   "farm_id": "dairy_forage_uncovered",
   "source": "soil_N2O",
   "gas": "N2O",
   "ipcc2006_kg": "0.0",
   "ipcc2019_kg": "0.0",
   "ipcc2006_tCO2e": "0.0",
   "ipcc2019_tCO2e": "0.0",
   "diff_tCO2e_2019_minus_2006": "0.0",
   "pct_change": "",
   "gwp_ar5": "265.0",
   "params_file": "ipcc_params_AN_v8.csv",
   "spec_file": "stylized_farms_AN_v6.yaml",
   "notes": "dairy_calf: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_cow: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo; dairy_heifer: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 12 mo"
  }
 ],
 "source": {
  "files": {
   "data/ipcc_2006_vs_2019_stylized_AN_v2.csv": "486ae898fc76f59faaf00f7373cfbbbe203aa70c92cca067cfb3c23a2c53ea09"
  }
 }
}
```

## Q: What if storage were 6 months instead of 12 (Table 10.17 fn 1 default)?

`run_farm({"farm_id": "dairy_forage_uncovered", "guideline": "IPCC2019", "storage_months": 6})`

```json
{
 "farm_id": "dairy_forage_uncovered",
 "results": {
  "IPCC2019": {
   "sources": {
    "enteric_CH4": {
     "kg": 17536.78528306512,
     "tCO2e": 491.0299879258234,
     "gas": "CH4"
    },
    "manure_CH4": {
     "kg": 18052.434967731897,
     "tCO2e": 505.4681790964931,
     "gas": "CH4"
    },
    "manure_N2O": {
     "kg": 145.89427939283027,
     "tCO2e": 38.66198403910003,
     "gas": "N2O"
    },
    "soil_N2O": {
     "kg": 0.0,
     "tCO2e": 0.0,
     "gas": "N2O"
    }
   },
   "total_tCO2e_excl_missing": 1035.1601510614164,
   "notes": [
    "dairy_calf: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 6 mo",
    "dairy_cow: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 6 mo",
    "dairy_heifer: MCF IPCC2019 Table 10.17 (Updated) warm_temperate_moist, liquid/pit 6 mo"
   ]
  }
 },
 "settings": {
  "climate_zone_2019": "warm_temperate_moist",
  "storage_months": 6,
  "mcf_zone_2006": "15C"
 },
 "param_overrides": {},
 "gwp": "AR5 GWP100 from spec meta.gwp_ar5",
 "source": {
  "files": {
   "data/stylized_farms_AN_v6.yaml": "e4cedd9ee179e65252b5e72e7c78f3f427765ae0c596f63340c9774397074c3c",
   "data/ipcc_params_AN_v10.csv": "fd7d6952505f2a925ad5800ad12803d31d7b6ca0672501f87376e760f7988e97",
   "scripts/compare_ipcc_2006_2019_stylized_AN_v2.py": "482db7797eb647deccf050a817a328d8112854b988c6cb60eddc8a2f372a103c"
  },
  "engine": "ghgsim ipcc2006/ipcc2019 modules"
 }
}
```

## Q: Where does EF1 come from?

`explain_parameter({"key": "IPCC2006.EF1.all"})`

```json
{
 "params_file": "ipcc_params_AN_v10.csv",
 "matches": [
  {
   "key": "IPCC2006.EF1.all",
   "value": "0.01",
   "units": "kg N2O-N/kg N",
   "dist": "uniform",
   "dist_lower": "0.003",
   "dist_upper": "0.03",
   "source_doi_or_url": "2006 IPCC GL Vol4 Ch11",
   "table": "Table 11.1",
   "equation": "",
   "page": "11.11",
   "region": "all",
   "status": "VERIFIED",
   "verified_by": "",
   "verified_date": "",
   "notes": "as published"
  }
 ],
 "source": {
  "files": {
   "data/ipcc_params_AN_v10.csv": "fd7d6952505f2a925ad5800ad12803d31d7b6ca0672501f87376e760f7988e97"
  }
 },
 "history": [
  {
   "file": "ipcc_params_AN_v4.csv",
   "value": "0.01",
   "table": "Table 11.1",
   "page": "11.11"
  },
  {
   "file": "ipcc_params_AN_v5.csv",
   "value": "0.01",
   "table": "Table 11.1",
   "page": "11.11"
  },
  {
   "file": "ipcc_params_AN_v6.csv",
   "value": "0.01",
   "table": "Table 11.1",
   "page": "11.11"
  },
  {
   "file": "ipcc_params_AN_v7.csv",
   "value": "0.01",
   "table": "Table 11.1",
   "page": "11.11"
  },
  {
   "file": "ipcc_params_AN_v8.csv",
   "value": "0.01",
   "table": "Table 11.1",
   "page": "11.11"
  },
  {
   "file": "ipcc_params_AN_v9.csv",
   "value": "0.01",
   "table": "Table 11.1",
   "page": "11.11"
  },
  {
   "file": "ipcc_params_AN_v10.csv",
   "value": "0.01",
   "table": "Table 11.1",
   "page": "11.11"
  }
 ]
}
```

## Q: What-if: EF1 = 0.005 on the crop farm.

`run_farm({"farm_id": "broiler_litter_field", "guideline": "IPCC2006", "param_overrides": {"IPCC2006.EF1.all": 0.005}})`

```json
{
 "farm_id": "broiler_litter_field",
 "results": {
  "IPCC2006": {
   "sources": {
    "enteric_CH4": {
     "kg": 0.0,
     "tCO2e": 0.0,
     "gas": "CH4"
    },
    "manure_CH4": {
     "kg": 528.2280000000001,
     "tCO2e": 14.790384000000001,
     "gas": "CH4"
    },
    "manure_N2O": {
     "kg": 56.783571428571435,
     "tCO2e": 15.04764642857143,
     "gas": "N2O"
    },
    "soil_N2O": {
     "kg": 54.68477991428571,
     "tCO2e": 14.491466677285715,
     "gas": "N2O"
    }
   },
   "total_tCO2e_excl_missing": 44.32949710585714,
   "notes": []
  }
 },
 "settings": {
  "climate_zone_2019": "warm_temperate_moist",
  "storage_months": 12,
  "mcf_zone_2006": "15C"
 },
 "param_overrides": {
  "IPCC2006.EF1.all": {
   "published": 0.01,
   "used": 0.005,
   "table": "Table 11.1",
   "page": "11.11"
  }
 },
 "gwp": "AR5 GWP100 from spec meta.gwp_ar5",
 "source": {
  "files": {
   "data/stylized_farms_AN_v6.yaml": "e4cedd9ee179e65252b5e72e7c78f3f427765ae0c596f63340c9774397074c3c",
   "data/ipcc_params_AN_v10.csv": "fd7d6952505f2a925ad5800ad12803d31d7b6ca0672501f87376e760f7988e97",
   "scripts/compare_ipcc_2006_2019_stylized_AN_v2.py": "482db7797eb647deccf050a817a328d8112854b988c6cb60eddc8a2f372a103c"
  },
  "engine": "ghgsim ipcc2006/ipcc2019 modules"
 }
}
```

## Q: Fresno County: climate zone?

`county_climate_zone({"fips": "06019"})`

```json
{
 "fips": "06019",
 "state": "CA",
 "county": "Fresno County",
 "lat_intpt": 36.761006,
 "lon_intpt": -119.655019,
 "mean_annual_temp_c": 13.37,
 "annual_precip_mm": 493.9,
 "annual_pe_hargreaves_mm": 1281.7,
 "annual_pe_thornthwaite_mm": 725.3,
 "p_over_pe_hargreaves": 0.385,
 "p_over_pe_thornthwaite": 0.681,
 "zone_hargreaves": "warm_temperate_dry",
 "zone_thornthwaite": "warm_temperate_dry",
 "zone_ipcc2019_map": "warm_temperate_dry",
 "ipcc_map_sample": "internal_point_cell",
 "zone_primary": "warm_temperate_dry",
 "zone_primary_basis": "ipcc2019_map",
 "source": {
  "files": {
   "data/county_climate_zones_AN_v1.csv": "4fa15553b1869303f2d111387c23041480f5e865501935fa14f4bc9833da2a6c"
  }
 }
}
```

## Q: Fresno County: 2006 vs 2019 by source.

`county_results({"fips": "06019"})`

```json
{
 "selection": {
  "fips": "06019",
  "state": null,
  "variant": "disclosed"
 },
 "n_counties": 1,
 "total_t_co2e_2006": 1575095.288,
 "total_t_co2e_2019": 1703223.2121999997,
 "pct_change": 8.134614151674091,
 "rows": [
  {
   "source": "enteric",
   "gas": "CH4",
   "t_co2e_2006": 940575.678,
   "t_co2e_2019": 1082944.1139999998,
   "pct_change": 15.14
  },
  {
   "source": "manure_ch4",
   "gas": "CH4",
   "t_co2e_2006": 202358.8632,
   "t_co2e_2019": 374986.40469999996,
   "pct_change": 85.31
  },
  {
   "source": "manure_n2o_direct",
   "gas": "N2O",
   "t_co2e_2006": 32557.9807,
   "t_co2e_2019": 55230.772600000004,
   "pct_change": 69.64
  },
  {
   "source": "manure_n2o_indirect_leach",
   "gas": "N2O",
   "t_co2e_2006": 0.0,
   "t_co2e_2019": 1001.3465999999999,
   "pct_change": Infinity
  },
  {
   "source": "manure_n2o_indirect_vol",
   "gas": "N2O",
   "t_co2e_2006": 24832.9605,
   "t_co2e_2019": 22294.333,
   "pct_change": -10.22
  },
  {
   "source": "soil_n2o_direct",
   "gas": "N2O",
   "t_co2e_2006": 336053.891,
   "t_co2e_2019": 140638.3773,
   "pct_change": -58.15
  },
  {
   "source": "soil_n2o_indirect_vol",
   "gas": "N2O",
   "t_co2e_2006": 38715.914600000004,
   "t_co2e_2019": 26127.863999999998,
   "pct_change": -32.51
  }
 ],
 "source": {
  "files": {
   "data/us_county_2006_vs_2019_AN_v2.csv.gz": "0beb435fea4cdd0985e3dd0afc4e9c937384b55fa31c1eadcd5ef7c44ed5f425"
  }
 },
 "climate_zone": {
  "fips": "06019",
  "state": "CA",
  "county": "Fresno County",
  "lat_intpt": 36.761006,
  "lon_intpt": -119.655019,
  "mean_annual_temp_c": 13.37,
  "annual_precip_mm": 493.9,
  "annual_pe_hargreaves_mm": 1281.7,
  "annual_pe_thornthwaite_mm": 725.3,
  "p_over_pe_hargreaves": 0.385,
  "p_over_pe_thornthwaite": 0.681,
  "zone_hargreaves": "warm_temperate_dry",
  "zone_thornthwaite": "warm_temperate_dry",
  "zone_ipcc2019_map": "warm_temperate_dry",
  "ipcc_map_sample": "internal_point_cell",
  "zone_primary": "warm_temperate_dry",
  "zone_primary_basis": "ipcc2019_map",
  "source": {
   "files": {
    "data/county_climate_zones_AN_v1.csv": "4fa15553b1869303f2d111387c23041480f5e865501935fa14f4bc9833da2a6c"
   }
  }
 },
 "census_flags": "peanuts_ac(D);potatoes:no_yield;rice_ac(D);roosters(D);sorghum_grain:state_yield;sorghum_grain_prod(D);turkeys(D)"
}
```

## Q: Iowa totals.

`county_results({"state": "IA"})`

```json
{
 "selection": {
  "fips": null,
  "state": "IA",
  "variant": "disclosed"
 },
 "n_counties": 99,
 "total_t_co2e_2006": 23475954.487800002,
 "total_t_co2e_2019": 22671041.1481,
 "pct_change": -3.4286714097963515,
 "rows": [
  {
   "source": "enteric",
   "gas": "CH4",
   "t_co2e_2006": 5462027.34,
   "t_co2e_2019": 6299200.712,
   "pct_change": 15.33
  },
  {
   "source": "manure_ch4",
   "gas": "CH4",
   "t_co2e_2006": 7071825.2154,
   "t_co2e_2019": 9600299.7529,
   "pct_change": 35.75
  },
  {
   "source": "manure_n2o_direct",
   "gas": "N2O",
   "t_co2e_2006": 311487.6224,
   "t_co2e_2019": 469008.7435,
   "pct_change": 50.57
  },
  {
   "source": "manure_n2o_indirect_leach",
   "gas": "N2O",
   "t_co2e_2006": 0.0,
   "t_co2e_2019": 7519.2712,
   "pct_change": Infinity
  },
  {
   "source": "manure_n2o_indirect_vol",
   "gas": "N2O",
   "t_co2e_2006": 307222.1307,
   "t_co2e_2019": 266896.4221,
   "pct_change": -13.13
  },
  {
   "source": "soil_n2o_direct",
   "gas": "N2O",
   "t_co2e_2006": 9422632.2168,
   "t_co2e_2019": 5280940.9359,
   "pct_change": -43.95
  },
  {
   "source": "soil_n2o_indirect_leach",
   "gas": "N2O",
   "t_co2e_2006": 200829.1001,
   "t_co2e_2019": 251217.4927,
   "pct_change": 25.09
  },
  {
   "source": "soil_n2o_indirect_vol",
   "gas": "N2O",
   "t_co2e_2006": 699930.8624,
   "t_co2e_2019": 495957.8178,
   "pct_change": -29.14
  }
 ],
 "source": {
  "files": {
   "data/us_county_2006_vs_2019_AN_v2.csv.gz": "0beb435fea4cdd0985e3dd0afc4e9c937384b55fa31c1eadcd5ef7c44ed5f425"
  }
 }
}
```

## Q: Provenance of the latest results manifest (US county numbers).

`provenance({"number_prefix": "us_county"})`

```json
{
 "manifest": "results_manifest_AN_v2.json",
 "generated": "2026-11-03T20:08:19-05:00",
 "profile": "full",
 "code": {
  "commit": "faf608e9324b6644423d3db20c1ca2287f0fd684",
  "branch": "living-recompute-AN-v1",
  "dirty": false
 },
 "parameter_file": {
  "path": "data/ipcc_params_AN_v10.csv",
  "sha256": "fd7d6952505f2a925ad5800ad12803d31d7b6ca0672501f87376e760f7988e97"
 },
 "upstream_sources": {
  "path": "data/upstream_sources_AN_v1.json",
  "pins": {
   "created": "2026-11-03T19:59:14-05:00",
   "note": "Fingerprints of upstream sources behind Paper B numbers; compared weekly by scripts/check_upstream_AN_v1.py (.github/workflows/upstream_check_AN_v1.yml).",
   "urls": {
    "ipcc_2006_v4_ch10": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_10_Ch10_Livestock.pdf",
    "ipcc_2006_v4_ch11": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O%26CO2.pdf",
    "ipcc_2019r_v4_ch10": "https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch10_Livestock.pdf",
    "ipcc_2019r_v4_ch11": "https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch11_Soils_N2O_CO2.pdf",
    "epa_ghgi_editions": "https://www.epa.gov/ghgemissions/inventory-us-greenhouse-gas-emissions-and-sinks",
    "nass_census2022": "https://www.nass.usda.gov/datasets/qs.census2022.txt.gz",
    "nclimdiv": "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/",
    "unfccc_crt_2026": "https://unfccc.int/ghg-inventories-annex-i-parties/2026",
    "gleam_release": "https://api.github.com/repos/un-fao/GLEAM/tags"
   },
   "sources": {
    "ipcc_2006_v4_ch10": {
     "sha256": "b8dd649b7858ae63462e5e47ddf2ebb36722c1058c28f0655ae6fb8b4a8de053",
     "bytes": 1249922
    },
    "ipcc_2006_v4_ch11": {
     "sha256": "9e621e34d3515d76a4c7531ac04fab8c23f149ce7cbdc50a5c5eef3c95e1905b",
     "bytes": 961809
    },
    "ipcc_2019r_v4_ch10": {
     "sha256": "915ca99a248262c530a39083cf835deb01a12988fedca7e3f0675931276865a1",
     "bytes": 3373054
    },
    "ipcc_2019r_v4_ch11": {
     "sha256": "337f18ceb618a858526ec01b5abed289843e1e8a69c957f0f62d22fa2a5761b3",
     "bytes": 944749
    },
    "epa_ghgi_editions": {
     "time_series_end_years_listed": [
      "2022",
      "2023"
     ],
     "latest": "2023"
    },
    "nass_census2022": {
     "content_length": "309188711",
     "last_modified": "Wed, 14 Feb 2024 19:25:51 GMT"
    },
    "nclimdiv": {
     "latest": "v1.0.0-20261006"
    },
    "unfccc_crt_2026": null,
    "gleam_release": {
     "latest_tag": "v0.8.0-alpha",
     "sha": "b0937d2",
     "n_tags": 1
    }
   }
  }
 },
 "steps": [
  {
   "name": "county_p_pe",
   "where": "bubble_only",
   "status": "ok",
   "outputs_reproduced": {
    "data/county_p_pe_may_oct_AN_v2.csv": true,
    "data/county_p_pe_manifest_AN_v2.json": true
   }
  },
  {
   "name": "county_climate_annual",
   "where": "bubble_only",
   "status": "ok",
   "outputs_reproduced": {
    "data/county_climate_annual_AN_v1.csv": true,
    "data/county_climate_annual_manifest_AN_v1.json": true
   }
  },
  {
   "name": "county_climate_zones",
   "where": "bubble_only",
   "status": "ok",
   "outputs_reproduced": {
    "data/county_climate_zones_AN_v1.csv": true,
    "data/county_climate_zones_manifest_AN_v1.json": true
   }
  },
  {
   "name": "stylized_2006_vs_2019",
   "where": "ci",
   "status": "ok",
   "outputs_reproduced": {
    "data/ipcc_2006_vs_2019_stylized_AN_v2.csv": false
   }
  },
  {
   "name": "fig_stylized",
   "where": "ci",
 
... [6050 more characters truncated in this transcript only]
```

## Q: What moved between results manifest v1 and v2?

`diff_manifests({"old": "results_manifest_AN_v1.json", "new": "results_manifest_AN_v2.json"})`

```json
{
 "old": "results_manifest_AN_v1.json",
 "new": "results_manifest_AN_v2.json",
 "report_markdown": "# Results diff: `results_manifest_AN_v1.json` -> `results_manifest_AN_v2.json`\n\nGenerated by `scripts/diff_results_AN_v1.py`. Causes below are taken from recorded hashes, commits and\nparameter files only. Comparisons with EPA or field data are consistency checks, not validation.\n\n\n## Why: what changed between the two runs\n\n- **Code commit:** `eb04c8e` (2026-11-03T20:04:05-05:00) -> `faf608e` (2026-11-03T20:08:19-05:00)\n- **Parameter file:** unchanged (`data/ipcc_params_AN_v10.csv`)\n- **Packages:** unchanged / not recorded\n- **Upstream pins:** unchanged / not recorded\n\n### Per step\n\n- **county_p_pe**: no input or script change\n- **county_climate_annual**: no input or script change\n- **county_climate_zones**: no input or script change\n- **stylized_2006_vs_2019**: no input or script change\n- **fig_stylized**: no input or script change\n- **us_county_run**: no input or script change\n- **inventories_crt2026**: no input or script change\n- **inventories_us_epa**: no input or script change\n\n## Paper numbers that moved (0 moved or new/removed; 121 unchanged within 0.005)\n\n| number | old | new | change | % | step |\n|---|---|---|---|---|---|\n\nStep causes are listed under *Per step* above; every number in a step inherits them.\n",
 "source": {
  "files": {
   "results/results_manifest_AN_v1.json": "8a9dcb6bf8cd9ff7201e3088edc4095bb4d57d96d6a75cfb659d58b44c7ee817",
   "results/results_manifest_AN_v2.json": "7ffc1951590b512770eb22682f5f4131159de9c8ec3195fbcdb6374edad6cdf6",
   "scripts/diff_results_AN_v1.py": "8c7238d6175e7f5a350f2900b320ddd5779a6d29e509f1ba8b09324a6928536b"
  }
 }
}
```
