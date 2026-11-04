"""
IPCC 2019 Refinement manure management (AN_v2 upgrade).

CH4 Eq 10.23, direct N2O Eq 10.25, indirect Eq 10.26-10.29, N available Eq 10.34
(Updated, no bedding). Parameters from the 2019 Refinement, Vol 4 Ch 10:

- MCF: Table 10.17 (Updated), p. 10.68-10.70. Liquid/slurry and pit storage below
  confinements use the storage-time row (``storage_months`` 6 or 12; default 12 by
  project decision, note fn 1 suggests 6 when retention is unknown) for the
  ``climate_zone_2019`` column. Uncovered lagoon uses its 12-month column. Solid
  storage, dry lot and daily spread use the Cool/Temperate/Warm columns
  (cool = cool temperate + boreal, temperate = warm temperate, warm = tropical).
  Liquid with natural crust = liquid MCF x (1 - 0.40), fn 1 (thick dry crust).
  Pasture/range/paddock MCF 0.47 % must be used with B0 = 0.19 (fn 2); because
  Eq 10.23 uses one B0 per animal, the PRP term is scaled by 0.19 / B0_animal.
  Poultry with and without litter 1.5 %.
- B0: Table 10.16A (Updated). Cattle/poultry/swine NA values equal 2006.
- Nrate: Table 10.19 (Updated), North America (dairy 0.59, other cattle 0.40,
  finishing swine 0.46, breeding 0.24, hens 1.13, broilers 1.59, turkeys 0.74).
- FracGasMS / FracLeachMS: Table 10.22 (Updated), per system variation.
- EF3: Table 10.21 (Updated).

If ``climate_zone_2019`` is not given (and cannot be derived from
``mean_annual_temp_c`` + ``moisture_ratio``), MCFs fall back to the 2006 Table 10.17
values for ``mcf_zone`` and ``MCF_basis`` says so. Nothing is invented: a missing
published cell raises KeyError (or NaN in the comparison script).
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.county_climate_annual import county_climate_annual, county_zone_primary
from ghgsim.modules.ipcc2006.manure import SYSTEM_MAP_2006, IPCC2006Manure, _fracgas_ms
from ghgsim.modules.livestock_types import is_poultry, is_swine

N2ON_TO_N2O = 44.0 / 28.0

ZONES_2019 = (
    "cool_temperate_moist",
    "cool_temperate_dry",
    "warm_temperate_moist",
    "warm_temperate_dry",
    # Added in AN_v9 parameters (Table 10.17 (Updated) p. 10.68 boreal and tropical columns).
    "boreal_moist",
    "boreal_dry",
    "tropical_montane",
    "tropical_wet",
    "tropical_moist",
    "tropical_dry",
)
# Table 10.17 (Updated) three-column systems: Cool / Temperate / Warm groups.
ZONE_GROUP_2019 = {
    "cool_temperate_moist": "cool",
    "cool_temperate_dry": "cool",
    "boreal_moist": "cool",
    "boreal_dry": "cool",
    "warm_temperate_moist": "temperate",
    "warm_temperate_dry": "temperate",
    "tropical_montane": "warm",
    "tropical_wet": "warm",
    "tropical_moist": "warm",
    "tropical_dry": "warm",
}
# 2019 system key -> (FracGasMS/FracLeachMS/EF3 key)
SYSTEM_KEY_2019 = {
    "liquid_nocrust": "liquid_nocrust",
    "liquid_crust": "liquid_crust",
    "lagoon": "lagoon",
    "pit": "pit",
    "solid_storage": "solid_storage",
    "dry_lot": "dry_lot",
    "daily_spread": "daily_spread",
    "poultry_with_litter": "poultry_with_litter",
    "poultry_without_litter": "poultry_without_litter",
}

_SYS_FROM_KEY = {v: k for k, v in SYSTEM_KEY_2019.items()}


def climate_zone_2019(mean_annual_temp_c: float, moisture_ratio: float) -> str | None:
    """IPCC climate zone from MAT (deg C) and annual MAP/PET.

    2006 IPCC GL Vol 4 Ch 3 Annex 3A.5 (Figure 3A.5.1), used unchanged by the 2019
    Refinement: boreal MAT <= 0; cool temperate 0 < MAT <= 10; warm temperate
    10 < MAT <= 18; moist when MAP/PET > 1. Tropical (MAT > 18) needs MAP and
    elevation classes and returns None (caller falls back) rather than guessing.
    """
    t, r = float(mean_annual_temp_c), float(moisture_ratio)
    wet = "moist" if r > 1.0 else "dry"
    if t <= 0.0:
        return f"boreal_{wet}"
    if t <= 10.0:
        return f"cool_temperate_{wet}"
    if t <= 18.0:
        return f"warm_temperate_{wet}"
    return None


def _p19(key: str, desc: str) -> ParamRef:
    return ParamRef(f"IPCC2019.{key}", desc)


_MCF_REFS = {}
for _z in ZONES_2019:
    _MCF_REFS[f"MCF19_lagoon_{_z}"] = _p19(f"MCF.lagoon|{_z}", f"2019 MCF lagoon {_z}")
    for _m in (6, 12):
        _MCF_REFS[f"MCF19_liquid_{_m}mo_{_z}"] = _p19(f"MCF.liquid_{_m}mo|{_z}", f"2019 MCF liquid {_m} mo {_z}")
for _s in ("solid_storage", "dry_lot", "daily_spread"):
    for _g in ("cool", "temperate", "warm"):
        _MCF_REFS[f"MCF19_{_s}_{_g}"] = _p19(f"MCF.{_s}|{_g}", f"2019 MCF {_s} {_g}")
_MCF_REFS["MCF19_pasture_all"] = _p19("MCF.pasture|all", "2019 MCF PRP (use with B0 0.19)")
_MCF_REFS["MCF19_poultry_litter_all"] = _p19("MCF.poultry_litter|all", "2019 MCF poultry with/without litter")
_MCF_REFS["MCF19_crust_reduction"] = _p19("MCF.crust_reduction|all", "Table 10.17 fn 1 thick dry crust reduction")
_MCF_REFS["B0_PRP_2019"] = _p19("B0.prp|all", "Table 10.16A all animals PRP B0")

_FRAC_REFS = {}
for _a, _keys in {
    "dairy": ("lagoon", "liquid_crust", "liquid_nocrust", "liquid_cover", "pit", "daily_spread", "solid_storage", "dry_lot"),
    "other_cattle": ("lagoon", "liquid_crust", "liquid_nocrust", "pit", "daily_spread", "solid_storage", "dry_lot"),
    "swine": ("lagoon", "liquid_crust", "liquid_nocrust", "pit", "daily_spread", "solid_storage", "dry_lot"),
    "poultry": ("lagoon", "liquid_nocrust", "pit", "daily_spread", "solid_storage", "poultry_with_litter", "poultry_without_litter"),
}.items():
    for _k in _keys:
        _FRAC_REFS[f"FracGasMS19_{_a}_{_k}"] = _p19(f"FracGasMS.{_a}|{_k}", f"2019 FracGasMS {_a} {_k}")
        _FRAC_REFS[f"FracLeachMS19_{_a}_{_k}"] = _p19(f"FracLeachMS.{_a}|{_k}", f"2019 FracLeachMS {_a} {_k}")

_EF3_REFS = {
    f"EF3_19_{k}": _p19(f"EF3.{k}", f"2019 EF3 {k}")
    for k in ("daily_spread", "solid_storage", "dry_lot", "liquid_crust", "liquid_nocrust", "lagoon", "pit",
              "poultry_with_litter", "poultry_without_litter")
}


class IPCC2019Manure:
    """IPCC 2019 manure CH4 + direct/indirect N2O (2019 MCF, B0, Nrate, FracGasMS, EF3)."""

    id = "ipcc2019.manure"
    version = "2.1.0"

    inputs = {
        **IPCC2006Manure.inputs,
        "include_leach": VarSpec("include_leach", "dimensionless",
                                 "Apply Table 10.22 FracLeachMS (default true for 2019)", "scalar", False),
        "climate_zone_2019": VarSpec("climate_zone_2019", "dimensionless",
                                     "Table 10.17 (Updated) climate zone, e.g. warm_temperate_moist", "scalar", False),
        "mean_annual_temp_c": VarSpec("mean_annual_temp_c", "degC",
                                      "Mean annual temperature (county/farm) to derive the climate zone", "scalar", False),
        "moisture_ratio": VarSpec("moisture_ratio", "dimensionless",
                                  "Annual MAP/PET (county/farm) to derive the climate zone", "scalar", False),
        "county_fips": VarSpec("county_fips", "dimensionless",
                               "US county FIPS; derives MAT + annual P/PE zone from "
                               "data/county_climate_annual_AN_v1.csv (nClimDiv 1991-2020, Hargreaves). "
                               "Explicit climate_zone_2019 or MAT/moisture_ratio win.", "scalar", False),
        "ef4_mode": VarSpec("ef4_mode", "dimensionless",
                            "EF4 for manure volatilisation: 'climate' (default; 2019 Ch11 Table 11.3 (Updated) wet 0.014 / "
                            "dry 0.005 from the climate zone, aggregated 0.010 if no zone) or 'aggregated' (0.010, "
                            "sensitivity; behaviour before DECISIONS_AN_v21)", "scalar", False),
        "storage_months": VarSpec("storage_months", "month",
                                  "Liquid/pit storage time for Table 10.17 (6 or 12; default 12)", "scalar", False),
    }

    parameters = {
        **IPCC2006Manure.parameters,
        "Nrate_dairy_2019": ParamRef("IPCC2019.Nrate.dairy|north_america", "2019 dairy Nrate NA"),
        "Nrate_other_cattle_2019": ParamRef("IPCC2019.Nrate.other_cattle|north_america", "2019 other cattle Nrate NA"),
        "Nrate_market_swine_2019": ParamRef("IPCC2019.Nrate.market_swine|north_america", "2019 finishing swine Nrate NA"),
        "Nrate_breeding_swine_2019": ParamRef("IPCC2019.Nrate.breeding_swine|north_america", "2019 breeding swine Nrate NA"),
        "Nrate_broilers_2019": ParamRef("IPCC2019.Nrate.broilers|north_america", "2019 broiler Nrate NA"),
        "Nrate_layers_2019": ParamRef("IPCC2019.Nrate.layers|north_america", "2019 layer Nrate NA"),
        "Nrate_turkeys_2019": ParamRef("IPCC2019.Nrate.turkeys|north_america", "2019 turkey Nrate"),
        "B0_dairy_2019": ParamRef("IPCC2019.B0.dairy|north_america", "2019 dairy B0 NA"),
        "B0_other_cattle_2019": ParamRef("IPCC2019.B0.other_cattle|north_america", "2019 non-dairy cattle B0 NA"),
        "B0_swine_2019": ParamRef("IPCC2019.B0.swine|north_america", "2019 swine B0 NA"),
        "B0_layers_2019": ParamRef("IPCC2019.B0.layers|north_america", "2019 layer B0"),
        "B0_other_poultry_2019": ParamRef("IPCC2019.B0.other_poultry|north_america", "2019 other poultry B0"),
        "EF5": ParamRef("IPCC2019.EF5.all", "2019 EF5 leaching"),
        "EF4_2019_all": ParamRef("IPCC2019.EF4.all", "2019 EF4 aggregated (Ch11 Table 11.3 Updated)"),
        "EF4_2019_wet": ParamRef("IPCC2019.EF4.wet", "2019 EF4 wet climate (Ch11 Table 11.3 Updated)"),
        "EF4_2019_dry": ParamRef("IPCC2019.EF4.dry", "2019 EF4 dry climate (Ch11 Table 11.3 Updated)"),
        **_MCF_REFS,
        **_FRAC_REFS,
        **_EF3_REFS,
    }

    outputs = {
        **IPCC2006Manure.outputs,
        "N2O_indirect_leach": VarSpec("N2O_indirect_leach", "kg N2O / year", "Indirect N2O from leaching", "scalar", True),
        "N_MMS_Avb_kg": VarSpec("N_MMS_Avb_kg", "kg N / year",
                                "Managed manure N after gas+leach loss (Eq 10.34, no bedding)", "scalar", True),
        "MCF_basis": VarSpec("MCF_basis", "dimensionless", "Which MCF table/zone was used", "scalar", True),
        "EF4_used": VarSpec("EF4_used", "kg N2O-N / kg (NH3-N + NOx-N)", "EF4 applied to manure volatilisation", "scalar", True),
        "EF4_basis": VarSpec("EF4_basis", "dimensionless", "Which EF4 (Table 11.3 Updated) was used", "scalar", True),
    }

    sources = [
        Citation(
            source="2019 Refinement to the 2006 IPCC Guidelines, Volume 4, Chapter 10",
            table="Tables 10.16A, 10.17, 10.19, 10.21, 10.22 (Updated)",
            equation="Eq 10.23, 10.25, 10.26, 10.27, 10.28, 10.29, 10.34",
            page="10.67-10.70, 10.83, 10.91, 10.97-10.98",
        ),
    ]

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _zone(inputs: Mapping[str, Any]) -> str | None:
        z = inputs.get("climate_zone_2019")
        if z not in (None, ""):
            return str(z)
        t, r = inputs.get("mean_annual_temp_c"), inputs.get("moisture_ratio")
        if t not in (None, "") and r not in (None, ""):
            return climate_zone_2019(float(t), float(r))
        fips = inputs.get("county_fips")
        if fips not in (None, ""):
            z = county_zone_primary(fips)
            if z is None:
                c = county_climate_annual(fips)
                if c is None:
                    raise KeyError(f"county_fips {fips!r} not in county climate files")
                z = c["ipcc_zone"]
            # Polar (no Table 10.17 column) or unresolved zones fall back to 2006 Table 10.17.
            return z if z in ZONES_2019 else None
        return None

    @staticmethod
    def _group(animal: str) -> list[str]:
        if is_swine(animal):
            return [animal, "swine"]
        if is_poultry(animal):
            return [animal, "poultry"]
        return [animal]

    def _frac(self, p: Mapping[str, Any], prefix: str, animal: str, key: str) -> float:
        for g in self._group(animal):
            name = f"{prefix}19_{g}_{key}"
            if name in p:
                return float(p[name])
        # Backward compatibility: callers that pass only the 1.x parameter names
        # (2006-keyed FracGasMS_*, 2019 FracLeachMS_*) keep working.
        if prefix == "FracGasMS":
            return _fracgas_ms(p, animal, SYSTEM_MAP_2006[_SYS_FROM_KEY.get(key, key)][2])
        for g in self._group(animal):
            legacy = f"FracLeachMS_{g}_{SYSTEM_MAP_2006[_SYS_FROM_KEY.get(key, key)][2]}"
            if legacy in p:
                return float(p[legacy])
        if is_swine(animal) and key in ("liquid_nocrust", "liquid_crust") and "FracLeachMS_swine_liquid_nocrust" in p:
            return float(p["FracLeachMS_swine_liquid_nocrust"])
        return 0.0

    def _mcf(self, p, system: str, zone: str | None, months: int, mcf_zone: str) -> float:
        if zone is None:  # 2006 Table 10.17 fallback
            mcf_key = SYSTEM_MAP_2006[system][0]
            if system == "pasture":
                return float(p["MCF_pasture_le10C" if mcf_zone == "le10C" else "MCF_pasture_15C"])
            return float(p[f"MCF_{mcf_key}_{mcf_zone}"])
        if system == "pasture":
            return float(p["MCF19_pasture_all"])
        if system.startswith("poultry_"):
            return float(p["MCF19_poultry_litter_all"])
        if system in ("liquid_nocrust", "liquid_crust", "pit"):
            v = float(p[f"MCF19_liquid_{months}mo_{zone}"])
            if system == "liquid_crust":
                v *= 1.0 - float(p["MCF19_crust_reduction"])
            return v
        if system == "lagoon":
            return float(p[f"MCF19_lagoon_{zone}"])
        if system in ("solid_storage", "dry_lot", "daily_spread"):
            return float(p[f"MCF19_{system}_{ZONE_GROUP_2019[zone]}"])
        raise KeyError(f"No 2019 MCF mapping for system '{system}'")

    @staticmethod
    def _ef4(p: Mapping[str, Any], zone: str | None, mode: str) -> tuple[float, str]:
        """EF4 for manure NH3+NOx volatilisation (Eq 10.27), consistent with IPCC2019SoilN2O.

        2019 Refinement Vol 4 Ch11 Table 11.3 (Updated): aggregated 0.010, wet 0.014, dry 0.005. Wet/dry follows
        the climate-zone moisture (moist/wet -> wet, dry -> dry). 'aggregated' keeps 0.010 as a sensitivity case.
        """
        agg = float(p["EF4_2019_all"]) if "EF4_2019_all" in p else float(p["EF4"])
        if mode == "aggregated":
            return agg, "Table 11.3 (Updated) aggregated (sensitivity)"
        if mode != "climate":
            raise ValueError("ef4_mode must be 'climate' or 'aggregated'")
        if zone is None:
            return agg, "Table 11.3 (Updated) aggregated (no climate zone)"
        wet = not zone.endswith("_dry")
        return float(p["EF4_2019_wet" if wet else "EF4_2019_dry"]), f"Table 11.3 (Updated) {'wet' if wet else 'dry'}"

    # ------------------------------------------------------------------ compute
    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        p = dict(params)
        head = float(inputs["head"])
        animal = str(inputs["animal_type"])
        systems = inputs["systems"]
        mcf_zone = inputs.get("mcf_zone", "15C")
        zone = self._zone(inputs)
        months = int(inputs.get("storage_months") or 12)
        if zone is not None and months not in (6, 12):
            raise ValueError("storage_months must be 6 or 12 (registered Table 10.17 rows)")

        vs = float(inputs["VS_kg_day"]) if inputs.get("VS_kg_day") else float(p[f"VS_{animal}"])
        tam = float(inputs["TAM_kg"]) if inputs.get("TAM_kg") else float(p[f"TAM_{animal}"])
        if inputs.get("Nex_kg_yr"):
            nex = float(inputs["Nex_kg_yr"])
        else:
            nrate = p.get(f"Nrate_{animal}_2019", p[f"Nrate_{animal}"])
            nex = float(nrate) * tam / 1000.0 * 365.0

        if animal in ("dairy", "other_cattle"):
            b0 = float(p.get(f"B0_{animal}_2019", p[f"B0_{animal}"]))
        elif is_swine(animal):
            b0 = float(p.get("B0_swine_2019", p[f"B0_{animal}"]))
        elif animal == "layers":
            b0 = float(p.get("B0_layers_2019", p["B0_layers"]))
        else:
            b0 = float(p.get("B0_other_poultry_2019", p[f"B0_{animal}"]))

        include_leach = bool(inputs.get("include_leach", True))
        ef4, ef4_basis = self._ef4(p, zone, str(inputs.get("ef4_mode") or "climate"))
        ef5 = float(p["EF5"]) if include_leach else 0.0
        sum_mcf = n_direct = n_vol = n_leach = n_lost = n_prp = n_managed = 0.0
        for system, frac in systems.items():
            frac = float(frac)
            mcf = self._mcf(p, system, zone, months, mcf_zone)
            if system == "pasture":
                if zone is not None:  # fn 2: PRP MCF is paired with B0 = 0.19
                    mcf *= float(p["B0_PRP_2019"]) / b0
                n_prp += head * nex * frac
                sum_mcf += mcf * frac
                continue
            key = SYSTEM_KEY_2019[system]
            n_sys = head * nex * frac
            n_managed += n_sys
            ef3 = float(p[f"EF3_19_{key}"]) if f"EF3_19_{key}" in p else float(p[f"EF3_{SYSTEM_MAP_2006[system][1]}"])
            fg = self._frac(p, "FracGasMS", animal, key)
            fl = self._frac(p, "FracLeachMS", animal, key) if include_leach else 0.0
            n_direct += n_sys * ef3
            n_vol += n_sys * fg
            n_leach += n_sys * fl
            n_lost += n_sys * (fg + fl)
            sum_mcf += mcf * frac

        ch4 = head * vs * 365.0 * b0 * float(p["CH4_M3_TO_KG"]) * sum_mcf
        n2o_direct = n_direct * N2ON_TO_N2O
        n2o_vol = n_vol * ef4 * N2ON_TO_N2O
        n2o_leach = n_leach * ef5 * N2ON_TO_N2O
        basis = (f"IPCC2019 Table 10.17 (Updated) {zone}, liquid/pit {months} mo" if zone
                 else f"IPCC2006 Table 10.17 {mcf_zone} (no 2019 climate zone given)")
        return {
            "CH4": ch4,
            "N2O_direct": n2o_direct,
            "N2O_indirect_vol": n2o_vol,
            "N2O_indirect_leach": n2o_leach,
            "N2O_total": n2o_direct + n2o_vol + n2o_leach,
            "N_PRP_kg": n_prp,
            "Nex_kg_head": nex,
            "N_managed_kg": n_managed,
            "N_MMS_Avb_kg": n_managed - n_lost,
            "MCF_basis": basis,
            "EF4_used": ef4,
            "EF4_basis": ef4_basis,
        }


errors = validate_module(IPCC2019Manure())
if errors:
    raise ValueError(f"IPCC2019Manure module validation failed: {errors}")
