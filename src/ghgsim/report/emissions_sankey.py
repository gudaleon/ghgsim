"""
Per-farm Sankey diagrams of Holos emission flows.

Every number is computed by ghgsim Holos modules (enteric, VS, manure CH4,
manure N2O, optional soil N2O). No invented fluxes. Three views:

- source_correct: registered fork defaults
- holos_as_coded: every registered non-default option (same stack as COMBINED)
- fork_delta: each single-fork CO2e change as an added or removed band

Writes versioned docs/figures/sankey_<farm>_AN_vN.{html,json} and, when
kaleido is installed, a static SVG/PNG. Never overwrites an existing AN_vN.
"""

from __future__ import annotations

import importlib.util
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ghgsim import __version__ as ENGINE_VERSION
from ghgsim.modules.holos import (
    HolosEnteric,
    HolosFieldN,
    HolosLimeUreaCO2,
    HolosManure,
    HolosManureCH4,
    HolosSoilN2O,
    HolosVolatileSolids,
)
from ghgsim.modules.holos.forks import get_holos_fork_registry
from ghgsim.modules.livestock_types import is_monogastric
from ghgsim.report.fork_diagram import latest_versioned, next_an_version, repo_root

SCHEMA = "ghgsim.emissions_sankey.v1"
VALUE_DECIMALS = 9
MASS_TOL_KG_CO2E = 1e-6
ZERO_KG = 1e-12

ANIMAL_LABELS = {
    "dairy_cow": "dairy cows",
    "dairy_heifer": "heifers",
    "dairy_calf": "calves",
    "beef_cow": "beef cows",
    "beef_calf": "beef calves",
    "dairy": "dairy cows",
    "beef": "beef cows",
    "broilers": "broilers",
    "layers": "layers",
    "turkeys": "turkeys",
    "market_swine": "market swine",
    "breeding_swine": "breeding swine",
}

SYSTEM_LABELS = {
    "liquid_nocrust": "liquid, no crust",
    "liquid_crust": "liquid, crust",
    "lagoon": "lagoon",
    "solid_storage": "solid storage",
    "dry_lot": "dry lot",
    "daily_spread": "daily spread",
    "pasture": "pasture",
    "poultry_with_litter": "poultry with litter",
    "poultry_without_litter": "poultry without litter",
    "pit": "pit storage",
}

NODE_COLORS = {
    "animal": "#1565C0",
    "process": "#00838F",
    "gas_CH4": "#EF6C00",
    "gas_N2O": "#6A1B9A",
    "sink": "#37474F",
    "source_total": "#455A64",
    "fork_added": "#C62828",
    "fork_removed": "#2E7D32",
    "soil": "#6D4C41",
    "amendment": "#5D4037",
    "gas_CO2": "#546E7A",
    "field": "#558B2F",
    "crop": "#827717",
}

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
SANKEY_VIEWS = ("source_correct", "holos_as_coded", "fork_delta")
PAYLOAD_JSON_RE = re.compile(r"^sankey_(.+)_AN_v(\d+)\.json$")


def _round(value: float) -> float:
    return round(float(value), VALUE_DECIMALS)


def _slug(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", str(name).strip())
    return cleaned.strip("_") or "farm"


def _load_runner(root: Path) -> Any:
    path = root / "scripts" / "holos_vt_de_runner_AN_v1.py"
    spec = importlib.util.spec_from_file_location("ghgsim_sankey_vt_de_runner", path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_stylized_spec(path: Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or "farms" not in data:
        raise ValueError(f"{path} is not a stylized-farms YAML")
    return data


def gwp_from_spec(spec: Mapping[str, Any]) -> dict[str, float]:
    raw = spec.get("meta", {}).get("gwp_ar5") or {}
    ch4 = float(raw.get("CH4", 28.0))
    n2o = float(raw.get("N2O", 265.0))
    return {"CH4": ch4, "N2O": n2o, "CO2": float(raw.get("CO2", 1.0))}


def _const(spec: Mapping[str, Any]) -> dict[str, float]:
    return {name: float(row["value"]) for name, row in spec["constants"].items() if "value" in row}


def rem_eq_10_14(de_percent: float) -> float:
    """IPCC 2006 Vol 4 Ch 10 Equation 10.14 p. 10.20."""
    de = float(de_percent)
    return 1.123 - (4.092e-3 * de) + (1.126e-5 * (de**2)) - (25.4 / de)


def weight_kg(spec: Mapping[str, Any], animal: Mapping[str, Any]) -> float:
    return float(animal["mass_lb"]["value"]) * float(spec["meta"]["lb_to_kg"])


def nex_kg_yr(spec: Mapping[str, Any], animal: Mapping[str, Any], constants: Mapping[str, float]) -> float:
    if "Nex_kg_yr_override" in animal:
        return float(animal["Nex_kg_yr_override"]["value"])
    animal_type = str(animal["animal_type"])
    nrate_key = {
        "dairy": "Nrate_dairy_na",
        "beef": "Nrate_other_cattle_na",
        "market_swine": "Nrate_market_swine_na",
        "breeding_swine": "Nrate_breeding_swine_na",
        "broilers": "Nrate_broilers_na",
        "layers": "Nrate_layers_na",
        "turkeys": "Nrate_turkeys_na",
    }.get(animal_type)
    if nrate_key is None:
        nrate_key = "Nrate_dairy_na" if animal_type == "dairy" else "Nrate_other_cattle_na"
    mass = animal_mass_kg(spec, animal)
    return constants[nrate_key] * mass / 1000.0 * 365.0


def animal_mass_kg(spec: Mapping[str, Any], animal: Mapping[str, Any]) -> float:
    if "mass_kg" in animal:
        return float(animal["mass_kg"]["value"])
    return weight_kg(spec, animal)


def milk_kg_day(spec: Mapping[str, Any], animal: Mapping[str, Any]) -> float:
    milk = animal.get("milk_lb_cow_yr")
    if not milk:
        return 0.0
    return float(milk["value"]) * float(spec["meta"]["lb_to_kg"]) / 365.0


def net_energy(
    spec: Mapping[str, Any],
    animal: Mapping[str, Any],
    constants: Mapping[str, float],
    de_percent: float,
) -> dict[str, float]:
    """NE_m / NE_a / NE_l / NE_p / RE_m from IPCC 2006 Eq 10.3, 10.4, 10.8, 10.13, 10.14."""
    cfi = constants[animal["Cfi_key"]]
    ca = constants[animal["Ca_key"]]
    mass = weight_kg(spec, animal)
    ne_m = cfi * (mass**0.75)
    ne_a = ca * ne_m
    ne_l = 0.0
    if animal.get("apply_lactation"):
        ne_l = milk_kg_day(spec, animal) * (1.47 + 0.40 * constants["milk_fat_pct"])
    ne_p = 0.0
    if animal.get("apply_pregnancy"):
        ne_p = constants["Cpregnancy_cattle"] * ne_m * constants["pregnant_fraction_na_dairy"]
    return {
        "NE_m": ne_m,
        "NE_a": ne_a,
        "NE_l": ne_l,
        "NE_work": 0.0,
        "NE_p": ne_p,
        "NE_g": 0.0,
        "RE_m": rem_eq_10_14(de_percent),
        "RE_g": 0.0,
        "weight_kg": mass,
    }


def herd_de_tdn(
    spec: Mapping[str, Any],
    farm: Mapping[str, Any],
    animal: Mapping[str, Any],
    diet: Mapping[str, Any],
) -> tuple[float, float, float]:
    tdn = float(diet["TDN_percent"]["value"])
    forage = float(diet["forage_percent"]["value"])
    if farm.get("diet_overrides_class_DE"):
        return float(diet["DE_percent"]["value"]), tdn, forage
    if "DE_percent" in animal and "value" in animal["DE_percent"]:
        return float(animal["DE_percent"]["value"]), tdn, forage
    return float(diet["DE_percent"]["value"]), tdn, forage


def fork_catalog() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for fork in get_holos_fork_registry().list_forks(sort_by="id"):
        others = [name for name in fork.options if name != fork.default]
        if len(others) != 1:
            raise ValueError(f"Fork {fork.id} does not have exactly one non-default option")
        rows.append(
            {
                "fork_id": fork.id,
                "default": fork.default,
                "alt": others[0],
                "label": fork.label,
                "issue_ref": fork.issue_ref,
            }
        )
    return rows


def combined_forks() -> dict[str, str]:
    return {row["fork_id"]: row["alt"] for row in fork_catalog()}


def co2e_kg(
    ch4_kg: float,
    n2o_kg: float,
    gwp: Mapping[str, float],
    co2_kg: float = 0.0,
) -> float:
    return (
        float(ch4_kg) * float(gwp["CH4"])
        + float(n2o_kg) * float(gwp["N2O"])
        + float(co2_kg) * float(gwp.get("CO2", 1.0))
    )


@dataclass
class GroupFlows:
    group_id: str
    label: str
    head: float
    enteric_ch4_kg: float
    manure_ch4_by_system_kg: dict[str, float]
    n2o_direct_kg: float
    n2o_indirect_kg: float
    n_mms_avb_kg: float = 0.0
    n_prp_kg: float = 0.0

    @property
    def manure_ch4_kg(self) -> float:
        return sum(self.manure_ch4_by_system_kg.values())

    @property
    def ch4_kg(self) -> float:
        return self.enteric_ch4_kg + self.manure_ch4_kg

    @property
    def n2o_kg(self) -> float:
        return self.n2o_direct_kg + self.n2o_indirect_kg


@dataclass
class FarmFlows:
    farm_id: str
    run: str
    forks: dict[str, str]
    groups: list[GroupFlows]
    soil_n2o_kg: float = 0.0
    lime_co2_kg: float = 0.0
    urea_co2_kg: float = 0.0
    gwp: dict[str, float] = field(default_factory=lambda: {"CH4": 28.0, "N2O": 265.0, "CO2": 1.0})
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def co2_kg(self) -> float:
        return self.lime_co2_kg + self.urea_co2_kg

    @property
    def ch4_enteric_kg(self) -> float:
        return sum(group.enteric_ch4_kg for group in self.groups)

    @property
    def ch4_manure_kg(self) -> float:
        return sum(group.manure_ch4_kg for group in self.groups)

    @property
    def ch4_kg(self) -> float:
        return self.ch4_enteric_kg + self.ch4_manure_kg

    @property
    def n2o_direct_kg(self) -> float:
        return sum(group.n2o_direct_kg for group in self.groups)

    @property
    def n2o_indirect_kg(self) -> float:
        return sum(group.n2o_indirect_kg for group in self.groups)

    @property
    def n2o_kg(self) -> float:
        return self.n2o_direct_kg + self.n2o_indirect_kg + self.soil_n2o_kg

    @property
    def co2e_kg(self) -> float:
        return co2e_kg(self.ch4_kg, self.n2o_kg, self.gwp, self.co2_kg)

    @property
    def co2e_t(self) -> float:
        return self.co2e_kg / 1000.0

    def totals(self) -> dict[str, float]:
        return {
            "CH4_enteric_kg": _round(self.ch4_enteric_kg),
            "CH4_manure_kg": _round(self.ch4_manure_kg),
            "CH4_kg": _round(self.ch4_kg),
            "N2O_direct_kg": _round(self.n2o_direct_kg),
            "N2O_indirect_kg": _round(self.n2o_indirect_kg),
            "N2O_soil_kg": _round(self.soil_n2o_kg),
            "N2O_kg": _round(self.n2o_kg),
            "CO2_lime_kg": _round(self.lime_co2_kg),
            "CO2_urea_kg": _round(self.urea_co2_kg),
            "CO2_kg": _round(self.co2_kg),
            "CO2e_kg": _round(self.co2e_kg),
            "CO2e_t": _round(self.co2e_t),
        }


def _manure_ch4_by_system(
    manure_ch4: HolosManureCH4,
    manure_in: Mapping[str, Any],
    params: Mapping[str, Any],
) -> dict[str, float]:
    """Per-storage-system manure CH4 from the same HolosManureCH4 engine."""
    systems = {str(name): float(frac) for name, frac in dict(manure_in["systems"]).items()}
    by_system: dict[str, float] = {}
    for system, fraction in systems.items():
        if abs(fraction) <= ZERO_KG:
            continue
        piece = manure_ch4.compute({**manure_in, "systems": {system: fraction}}, params)
        by_system[system] = float(piece["CH4"])
    return by_system


def _yaml_number(node: Any, default: float = 0.0) -> float:
    if node in (None, ""):
        return default
    if isinstance(node, Mapping) and "value" in node:
        return float(node["value"])
    return float(node)


def _field_crops(field: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Collect Eq 11.6 crop specs from a stylized field (area/yield may be ILLUSTRATIVE)."""
    crops: list[dict[str, Any]] = []
    for row in field.get("crops") or []:
        crops.append(
            {
                "crop": row["crop"],
                "area_ha": _yaml_number(row.get("area_ha")),
                "yield_fresh_kg_ha": _yaml_number(row.get("yield_fresh_kg_ha")),
                "FracRenew": row.get("FracRenew"),
                "FracRemove": row.get("FracRemove"),
                "FracBurnt": row.get("FracBurnt"),
                "CF": row.get("CF"),
            }
        )
    return crops


def _apply_field_modules(
    spec: Mapping[str, Any],
    farm: Mapping[str, Any],
    params: Mapping[str, float],
    *,
    n_mms_avb_kg: float,
    n_prp_kg: float,
    forks: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Link leftover manure N once, then run soil N2O and lime/urea CO2."""
    field_id = farm.get("field_id")
    if not field_id:
        return {
            "soil_n2o_kg": 0.0,
            "lime_co2_kg": 0.0,
            "urea_co2_kg": 0.0,
            "extras": {},
        }
    field = spec["fields"][field_id]
    linker = HolosFieldN()
    soil = HolosSoilN2O()
    lime = HolosLimeUreaCO2()
    crops = _field_crops(field)
    field_n = linker.compute(
        {
            "N_MMS_Avb_kg": n_mms_avb_kg,
            "N_PRP_kg": n_prp_kg + _yaml_number(field.get("F_PRP_extra_kg")),
            "F_SN": _yaml_number(field.get("F_SN")),
            "F_ON_other_kg": _yaml_number(field.get("F_ON_other_kg")),
            "F_CR": _yaml_number(field.get("F_CR")),
            "F_SOM": _yaml_number(field.get("F_SOM")),
            "FracFEED": _yaml_number(field.get("FracFEED")),
            "FracFUEL": _yaml_number(field.get("FracFUEL")),
            "FracCNST": _yaml_number(field.get("FracCNST")),
            "link_manure_n": bool(field.get("link_manure_n", True)),
            "F_ON_override": field.get("F_ON_override"),
            "crops": crops,
        },
        params,
    )
    soil_in: dict[str, Any] = {
        "F_SN": field_n["F_SN"],
        "F_ON": field_n["F_ON"],
        "F_CR": field_n["F_CR"],
        "F_SOM": field_n["F_SOM"],
        "F_PRP_CPP": field_n["F_PRP_CPP"],
        "climate": str(field.get("climate") or "wet"),
        "forks": dict(forks or {}),
    }
    if field.get("P_PE") not in (None, ""):
        soil_in["P_PE"] = _yaml_number(field.get("P_PE"))
    if field.get("RFtext") not in (None, ""):
        soil_in["RFtext"] = _yaml_number(field.get("RFtext"))
    if field.get("RFtopo") not in (None, ""):
        soil_in["RFtopo"] = _yaml_number(field.get("RFtopo"))
    soil_out = soil.compute(soil_in, params)
    lime_out = lime.compute(
        {
            "M_limestone_t": _yaml_number(field.get("M_limestone_t")),
            "M_dolomite_t": _yaml_number(field.get("M_dolomite_t")),
            "M_urea_t": _yaml_number(field.get("M_urea_t")),
        },
        params,
    )
    return {
        "soil_n2o_kg": float(soil_out["N2O_total"]),
        "lime_co2_kg": float(lime_out["CO2_lime_kg"]),
        "urea_co2_kg": float(lime_out["CO2_urea_kg"]),
        "extras": {
            "field_id": field_id,
            "N_MMS_Avb_kg": n_mms_avb_kg,
            "N_PRP_kg": n_prp_kg,
            "F_SN": field_n["F_SN"],
            "F_ON": field_n["F_ON"],
            "F_CR": field_n["F_CR"],
            "F_SOM": field_n["F_SOM"],
            "F_PRP_CPP": field_n["F_PRP_CPP"],
            "F_AM_kg": field_n["F_AM_kg"],
            "EF1_used": float(soil_out["EF1_used"]),
            "P_PE": soil_in.get("P_PE"),
            "residue_crops": field_n.get("residue_crops") or [],
            "soil_n2o_by_source": dict(soil_out.get("soil_n2o_by_source") or {}),
            "N2O_soil_direct_kg": float(soil_out["N2O_direct"]),
            "N2O_soil_indirect_vol_kg": float(soil_out["N2O_indirect_vol"]),
            "N2O_soil_indirect_leach_kg": float(soil_out["N2O_indirect_leach"]),
        },
    }


def compute_stylized_farm_flows(
    spec: Mapping[str, Any],
    farm: Mapping[str, Any],
    params: Mapping[str, float],
    forks: Mapping[str, str],
    *,
    run: str,
) -> FarmFlows:
    """Run Holos modules per animal class and optional field modules."""
    constants = _const(spec)
    gwp = gwp_from_spec(spec)
    enteric = HolosEnteric()
    vs_module = HolosVolatileSolids()
    manure = HolosManure()
    manure_ch4 = HolosManureCH4()
    groups: list[GroupFlows] = []
    fork_settings = dict(forks)
    herds = list(farm.get("herds") or [])
    manure_id = farm.get("manure_id")
    manure_cfg = spec["manure_variants"][manure_id] if manure_id else {"systems": {}, "cover_type": "none"}
    n_mms_avb = 0.0
    n_prp = 0.0

    if herds and is_monogastric(str(spec["animal_classes"][herds[0]]["animal_type"])):
        for class_id in herds:
            animal = spec["animal_classes"][class_id]
            head = float(animal["head"]["value"])
            manure_in = {
                "head": head,
                "animal_type": animal["animal_type"],
                "climate_zone": spec["meta"]["climate_zone"],
                "systems": dict(manure_cfg["systems"]),
                "cover_type": str(manure_cfg.get("cover_type", "none")),
                "forks": fork_settings,
            }
            if "VS_kg_day" in animal:
                manure_in["VS_kg_day"] = float(animal["VS_kg_day"]["value"])
            manure_in["Nex_kg_yr"] = nex_kg_yr(spec, animal, constants)
            ent = enteric.compute(
                {"head": head, "animal_type": animal["animal_type"], "forks": fork_settings},
                params,
            )
            man = manure.compute(manure_in, params)
            by_system = _manure_ch4_by_system(manure_ch4, manure_in, params)
            n_mms_avb += float(man["N_MMS_Avb_kg"])
            n_prp += float(man["N_PRP_kg"])
            groups.append(
                GroupFlows(
                    group_id=str(class_id),
                    label=ANIMAL_LABELS.get(str(class_id), str(class_id).replace("_", " ")),
                    head=head,
                    enteric_ch4_kg=float(ent["CH4_total"]),
                    manure_ch4_by_system_kg=by_system,
                    n2o_direct_kg=float(man["N2O_direct"]),
                    n2o_indirect_kg=float(man["N2O_indirect_vol"]),
                    n_mms_avb_kg=float(man["N_MMS_Avb_kg"]),
                    n_prp_kg=float(man["N_PRP_kg"]),
                )
            )
    elif herds:
        diet = spec["diets"][farm["diet_id"]]
        for class_id in herds:
            animal = spec["animal_classes"][class_id]
            de, tdn, forage = herd_de_tdn(spec, farm, animal, diet)
            energy = net_energy(spec, animal, constants, de)
            head = float(animal["head"]["value"])
            enteric_in = {
                "head": head,
                "animal_type": animal["animal_type"],
                "animal_class": animal["animal_class"],
                "NE_m": energy["NE_m"],
                "NE_a": energy["NE_a"],
                "NE_l": energy["NE_l"],
                "NE_work": energy["NE_work"],
                "NE_p": energy["NE_p"],
                "NE_g": energy["NE_g"],
                "RE_m": energy["RE_m"],
                "RE_g": energy["RE_g"],
                "DE_percent": de,
                "TDN_percent": tdn,
                "forks": fork_settings,
            }
            ent = enteric.compute(enteric_in, params)
            vs_in = {
                "GE_MJ_day": float(ent["GE_used"]),
                "DE_percent": de,
                "TDN_percent": tdn,
                "ASH_percent": constants["ASH_percent"],
                "forage_percent": forage,
                "animal_class": animal["animal_class"],
                "weight_kg": energy["weight_kg"],
                "forks": fork_settings,
            }
            vs_out = vs_module.compute(vs_in, params)
            manure_in = {
                "head": head,
                "animal_type": animal["animal_type"],
                "climate_zone": spec["meta"]["climate_zone"],
                "systems": dict(manure_cfg["systems"]),
                "VS_kg_day": float(vs_out["VS_kg_day"]),
                "Nex_kg_yr": nex_kg_yr(spec, animal, constants),
                "animal_class": animal["animal_class"],
                "cover_type": str(manure_cfg.get("cover_type", "none")),
                "forks": fork_settings,
            }
            man = manure.compute(manure_in, params)
            by_system = _manure_ch4_by_system(manure_ch4, manure_in, params)
            if abs(sum(by_system.values()) - float(man["CH4"])) > MASS_TOL_KG_CO2E:
                raise ValueError(
                    f"Per-system manure CH4 {sum(by_system.values())} != engine CH4 {man['CH4']}"
                )
            n_mms_avb += float(man["N_MMS_Avb_kg"])
            n_prp += float(man["N_PRP_kg"])
            groups.append(
                GroupFlows(
                    group_id=str(class_id),
                    label=ANIMAL_LABELS.get(str(class_id), str(class_id).replace("_", " ")),
                    head=head,
                    enteric_ch4_kg=float(ent["CH4_total"]),
                    manure_ch4_by_system_kg=by_system,
                    n2o_direct_kg=float(man["N2O_direct"]),
                    n2o_indirect_kg=float(man["N2O_indirect_vol"]),
                    n_mms_avb_kg=float(man["N_MMS_Avb_kg"]),
                    n_prp_kg=float(man["N_PRP_kg"]),
                )
            )

    field_out = _apply_field_modules(
        spec, farm, params, n_mms_avb_kg=n_mms_avb, n_prp_kg=n_prp, forks=fork_settings
    )
    extras: dict[str, Any] = {
        "farm_type": farm.get("farm_type"),
        "diet_id": farm.get("diet_id"),
        "manure_id": farm.get("manure_id"),
    }
    extras.update(field_out["extras"])
    return FarmFlows(
        farm_id=str(farm["id"]),
        run=run,
        forks=fork_settings,
        groups=groups,
        soil_n2o_kg=field_out["soil_n2o_kg"],
        lime_co2_kg=field_out["lime_co2_kg"],
        urea_co2_kg=field_out["urea_co2_kg"],
        gwp=gwp,
        extras=extras,
    )


def compute_county_flows(
    root: Path,
    county_name: str,
    forks: Mapping[str, str],
    *,
    run: str,
    pathway: str = "epa_vs",
) -> FarmFlows:
    """Optional county Sankey: same Holos modules as the VT/DE runner."""
    runner = _load_runner(root)
    epa = runner.load_epa_assumptions()
    counties = runner.load_vt_de_counties()
    match = counties[counties["COUNTY_NAME"].str.upper() == county_name.strip().upper()]
    if match.empty:
        raise ValueError(f"County '{county_name}' not in the VT/DE trial table")
    row = match.iloc[0]
    farm = runner.v3_farm_from_row(row, epa)
    params = runner.holos_compute_params(runner.load_registries(), mcf_set="ipcc15C")
    gwp = dict(runner.GWP_AR5)
    enteric = HolosEnteric()
    vs_module = HolosVolatileSolids()
    manure = HolosManure()
    manure_ch4 = HolosManureCH4()
    soil = HolosSoilN2O()
    groups: list[GroupFlows] = []
    n_prp = 0.0
    fork_settings = dict(forks)
    for herd in farm["herds"]:
        manure_cfg = herd.get("manure") or {}
        animal_flag = manure_cfg.get("animal")
        if animal_flag == "dairy":
            animal = "dairy"
        elif animal_flag in ("other_cattle", "beef"):
            animal = "beef"
        else:
            animal = "dairy" if herd.get("ym_category") == "dairy" else "beef"
        head = float(herd["head"])
        enteric_in = {
            "head": head,
            "animal_type": animal,
            "animal_class": str(herd.get("animal_class", "adult")),
            "GE_MJ_day": float(herd["GE_MJ_day"]),
            "forks": fork_settings,
        }
        ent = enteric.compute(enteric_in, params)
        vs_val, _src = runner._vs_for_herd(herd, fork_settings, params, pathway, vs_module)
        manure_in: dict[str, Any] = {
            "head": head,
            "animal_type": animal,
            "climate_zone": "15C",
            "systems": dict(manure_cfg["systems"]),
            "animal_class": str(herd.get("animal_class", "adult")),
            "cover_type": str(herd.get("cover_type", "none")),
            "forks": fork_settings,
        }
        if vs_val is not None:
            manure_in["VS_kg_day"] = vs_val
        nex = manure_cfg.get("Nex_kg_yr", herd.get("Nex_kg_yr"))
        if nex not in (None, ""):
            manure_in["Nex_kg_yr"] = float(nex)
        man = manure.compute(manure_in, params)
        by_system = _manure_ch4_by_system(manure_ch4, manure_in, params)
        n_prp += float(man["N_PRP_kg"])
        groups.append(
            GroupFlows(
                group_id=animal,
                label=ANIMAL_LABELS.get(animal, animal),
                head=head,
                enteric_ch4_kg=float(ent["CH4_total"]),
                manure_ch4_by_system_kg=by_system,
                n2o_direct_kg=float(man["N2O_direct"]),
                n2o_indirect_kg=float(man["N2O_indirect_vol"]),
                n_mms_avb_kg=float(man["N_MMS_Avb_kg"]),
                n_prp_kg=float(man["N_PRP_kg"]),
            )
        )
    soil_in = {
        "F_SN": float(farm["soil"]["F_SN"]),
        "F_ON": float(farm["soil"]["F_ON"]),
        "F_CR": float(farm["soil"]["F_CR"]),
        "F_SOM": float(farm["soil"].get("F_SOM", 0.0)),
        "F_PRP_CPP": float(farm["soil"].get("F_PRP_CPP", 0.0)) + n_prp,
        "climate": farm["soil"]["climate"],
        "forks": fork_settings,
    }
    soil_out = soil.compute(soil_in, params)
    return FarmFlows(
        farm_id=f"county_{_slug(str(row['COUNTY_NAME'])).upper()}",
        run=run,
        forks=fork_settings,
        groups=groups,
        soil_n2o_kg=float(soil_out["N2O_total"]),
        gwp=gwp,
        extras={
            "county": str(row["COUNTY_NAME"]),
            "state": str(row["STATE_ALPHA"]),
            "fips": str(row["fips"]),
            "pathway": pathway,
        },
    )


def _add_node(
    nodes: dict[str, dict[str, Any]],
    node_id: str,
    *,
    label: str,
    kind: str,
    layer: int,
    color: str,
) -> None:
    if node_id not in nodes:
        nodes[node_id] = {
            "id": node_id,
            "label": label,
            "kind": kind,
            "layer": layer,
            "color": color,
            "value": 0.0,
        }


def _add_link(
    links: list[dict[str, Any]],
    nodes: dict[str, dict[str, Any]],
    source: str,
    target: str,
    value: float,
    *,
    units: str = "kg CO2e",
    extra: Mapping[str, Any] | None = None,
) -> None:
    if abs(value) <= ZERO_KG:
        return
    amount = _round(value)
    links.append(
        {
            "source": source,
            "target": target,
            "value": amount,
            "units": units,
            **dict(extra or {}),
        }
    )
    nodes[source]["value"] = _round(float(nodes[source]["value"]) + amount)
    # target value is filled after inflow/outflow assignment for intermediates


def build_process_sankey(flows: FarmFlows) -> dict[str, Any]:
    """Animal groups → processes → gases (GWP labelled) → total CO2e."""
    gwp = flows.gwp
    nodes: dict[str, dict[str, Any]] = {}
    links: list[dict[str, Any]] = []

    _add_node(nodes, "gas.CH4", label=f"CH4 (GWP {gwp['CH4']:g})", kind="gas", layer=2, color=NODE_COLORS["gas_CH4"])
    _add_node(nodes, "gas.N2O", label=f"N2O (GWP {gwp['N2O']:g})", kind="gas", layer=2, color=NODE_COLORS["gas_N2O"])
    _add_node(nodes, "gas.CO2", label=f"CO2 (GWP {gwp.get('CO2', 1.0):g})", kind="gas", layer=2, color=NODE_COLORS["gas_CO2"])
    _add_node(nodes, "sink.CO2e", label="total CO2e", kind="sink", layer=3, color=NODE_COLORS["sink"])

    def process_node(process_id: str, label: str) -> str:
        _add_node(nodes, process_id, label=label, kind="process", layer=1, color=NODE_COLORS["process"])
        return process_id

    for group in flows.groups:
        animal_id = f"animal.{group.group_id}"
        _add_node(
            nodes,
            animal_id,
            label=group.label,
            kind="animal",
            layer=0,
            color=NODE_COLORS["animal"],
        )
        enteric_id = process_node("process.enteric_ch4", "enteric CH4")
        _add_link(
            links,
            nodes,
            animal_id,
            enteric_id,
            group.enteric_ch4_kg * gwp["CH4"],
            extra={"native_kg": _round(group.enteric_ch4_kg), "gas": "CH4"},
        )
        for system, ch4_kg in sorted(group.manure_ch4_by_system_kg.items()):
            proc_id = process_node(
                f"process.manure_ch4.{system}",
                f"manure CH4 ({SYSTEM_LABELS.get(system, system)})",
            )
            _add_link(
                links,
                nodes,
                animal_id,
                proc_id,
                ch4_kg * gwp["CH4"],
                extra={"native_kg": _round(ch4_kg), "gas": "CH4", "system": system},
            )
        direct_id = process_node("process.manure_n2o_direct", "direct manure N2O")
        _add_link(
            links,
            nodes,
            animal_id,
            direct_id,
            group.n2o_direct_kg * gwp["N2O"],
            extra={"native_kg": _round(group.n2o_direct_kg), "gas": "N2O"},
        )
        indirect_id = process_node("process.manure_n2o_indirect", "indirect N2O")
        _add_link(
            links,
            nodes,
            animal_id,
            indirect_id,
            group.n2o_indirect_kg * gwp["N2O"],
            extra={"native_kg": _round(group.n2o_indirect_kg), "gas": "N2O"},
        )

    if flows.soil_n2o_kg > ZERO_KG:
        soil_id = process_node("process.soil_n2o", "soil N2O")
        by_src = {
            key: float(value)
            for key, value in dict(flows.extras.get("soil_n2o_by_source") or {}).items()
        }
        if not by_src:
            by_src = {"F_ON": flows.soil_n2o_kg}
        gwp_n2o = gwp["N2O"]

        def _src_co2e(name: str) -> float:
            return by_src.get(name, 0.0) * gwp_n2o

        f_on_co2e = _src_co2e("F_ON")
        f_prp_co2e = _src_co2e("F_PRP_CPP")
        total_mms = sum(group.n_mms_avb_kg for group in flows.groups)
        total_prp = sum(group.n_prp_kg for group in flows.groups)
        if f_on_co2e > ZERO_KG:
            _add_node(
                nodes,
                "field.applied_manure",
                label="applied manure N",
                kind="field",
                layer=1,
                color=NODE_COLORS["field"],
            )
            allocated = 0.0
            if total_mms > ZERO_KG:
                for group in flows.groups:
                    share = f_on_co2e * (group.n_mms_avb_kg / total_mms)
                    allocated += share
                    _add_link(
                        links,
                        nodes,
                        f"animal.{group.group_id}",
                        "field.applied_manure",
                        share,
                        extra={"native_kg": _round(by_src.get("F_ON", 0.0) * (group.n_mms_avb_kg / total_mms)), "gas": "N2O", "n_source": "F_ON"},
                    )
            leftover = f_on_co2e - allocated
            if leftover > ZERO_KG:
                _add_node(
                    nodes,
                    "field.other_organic",
                    label="other organic N",
                    kind="soil",
                    layer=0,
                    color=NODE_COLORS["soil"],
                )
                _add_link(
                    links,
                    nodes,
                    "field.other_organic",
                    "field.applied_manure",
                    leftover,
                    extra={"native_kg": _round(leftover / gwp_n2o), "gas": "N2O", "n_source": "F_ON_other"},
                )
            _add_link(
                links,
                nodes,
                "field.applied_manure",
                soil_id,
                f_on_co2e,
                extra={"native_kg": _round(by_src.get("F_ON", 0.0)), "gas": "N2O", "n_source": "F_ON"},
            )
        if f_prp_co2e > ZERO_KG:
            _add_node(
                nodes,
                "field.prp",
                label="pasture urine/dung N",
                kind="field",
                layer=1,
                color=NODE_COLORS["field"],
            )
            if total_prp > ZERO_KG:
                for group in flows.groups:
                    share = f_prp_co2e * (group.n_prp_kg / total_prp)
                    _add_link(
                        links,
                        nodes,
                        f"animal.{group.group_id}",
                        "field.prp",
                        share,
                        extra={"native_kg": _round(by_src.get("F_PRP_CPP", 0.0) * (group.n_prp_kg / total_prp)), "gas": "N2O", "n_source": "F_PRP"},
                    )
            else:
                _add_node(nodes, "animal.soil", label="soil N inputs", kind="soil", layer=0, color=NODE_COLORS["soil"])
                _add_link(
                    links,
                    nodes,
                    "animal.soil",
                    "field.prp",
                    f_prp_co2e,
                    extra={"native_kg": _round(by_src.get("F_PRP_CPP", 0.0)), "gas": "N2O", "n_source": "F_PRP"},
                )
            _add_link(
                links,
                nodes,
                "field.prp",
                soil_id,
                f_prp_co2e,
                extra={"native_kg": _round(by_src.get("F_PRP_CPP", 0.0)), "gas": "N2O", "n_source": "F_PRP"},
            )
        source_nodes = (
            ("F_SN", "soil.synthetic", "synthetic N", "soil", NODE_COLORS["soil"]),
            ("F_CR", "crop.residues", "crop residues", "crop", NODE_COLORS["crop"]),
            ("F_SOM", "soil.som", "mineralised SOM N", "soil", NODE_COLORS["soil"]),
        )
        for src_name, node_id, label, kind, color in source_nodes:
            amount = _src_co2e(src_name)
            if amount <= ZERO_KG:
                continue
            _add_node(nodes, node_id, label=label, kind=kind, layer=0, color=color)
            _add_link(
                links,
                nodes,
                node_id,
                soil_id,
                amount,
                extra={"native_kg": _round(by_src.get(src_name, 0.0)), "gas": "N2O", "n_source": src_name},
            )
    if flows.lime_co2_kg > ZERO_KG or flows.urea_co2_kg > ZERO_KG:
        _add_node(
            nodes,
            "soil.amendments",
            label="lime / urea",
            kind="amendment",
            layer=0,
            color=NODE_COLORS["amendment"],
        )
        if flows.lime_co2_kg > ZERO_KG:
            lime_id = process_node("process.lime_co2", "lime CO2")
            _add_link(
                links,
                nodes,
                "soil.amendments",
                lime_id,
                flows.lime_co2_kg * gwp.get("CO2", 1.0),
                extra={"native_kg": _round(flows.lime_co2_kg), "gas": "CO2"},
            )
        if flows.urea_co2_kg > ZERO_KG:
            urea_id = process_node("process.urea_co2", "urea CO2")
            _add_link(
                links,
                nodes,
                "soil.amendments",
                urea_id,
                flows.urea_co2_kg * gwp.get("CO2", 1.0),
                extra={"native_kg": _round(flows.urea_co2_kg), "gas": "CO2"},
            )

    ch4_from_process = 0.0
    n2o_from_process = 0.0
    co2_from_process = 0.0
    for link in list(links):
        target = str(link["target"])
        if not target.startswith("process."):
            continue
        gas = str(link.get("gas", ""))
        if gas == "CH4":
            _add_link(links, nodes, target, "gas.CH4", float(link["value"]), extra={"gas": "CH4"})
            ch4_from_process += float(link["value"])
        elif gas == "N2O":
            _add_link(links, nodes, target, "gas.N2O", float(link["value"]), extra={"gas": "N2O"})
            n2o_from_process += float(link["value"])
        elif gas == "CO2":
            _add_link(links, nodes, target, "gas.CO2", float(link["value"]), extra={"gas": "CO2"})
            co2_from_process += float(link["value"])

    _add_link(links, nodes, "gas.CH4", "sink.CO2e", ch4_from_process, extra={"gas": "CH4"})
    _add_link(links, nodes, "gas.N2O", "sink.CO2e", n2o_from_process, extra={"gas": "N2O"})
    _add_link(links, nodes, "gas.CO2", "sink.CO2e", co2_from_process, extra={"gas": "CO2"})

    nodes = _prune_unused_nodes(nodes, links)
    _finalize_node_values(nodes, links)
    return {
        "view": flows.run,
        "units": "kg CO2e",
        "gwp": dict(gwp),
        "totals": flows.totals(),
        "nodes": _sorted_nodes(nodes),
        "links": _sorted_links(links),
    }


def build_fork_delta_sankey(
    baseline: FarmFlows,
    combined: FarmFlows,
    single_forks: Mapping[str, FarmFlows],
) -> dict[str, Any]:
    """
    source_correct CO2e plus/minus each fork band → holos_as_coded CO2e.

    Interaction = combined − baseline − sum(single-fork deltas). Plotly needs
    positive link values, so decreases leave as 'removed' sinks and increases
    enter as 'added' sources.
    """
    gwp = baseline.gwp
    base = baseline.co2e_kg
    holos = combined.co2e_kg
    deltas = {fork_id: flows.co2e_kg - base for fork_id, flows in single_forks.items()}
    interaction = holos - base - sum(deltas.values())
    nodes: dict[str, dict[str, Any]] = {}
    links: list[dict[str, Any]] = []
    _add_node(
        nodes,
        "source.source_correct",
        label=f"source_correct ({_round(base / 1000.0)} t CO2e)",
        kind="source_total",
        layer=0,
        color=NODE_COLORS["source_total"],
    )
    _add_node(
        nodes,
        "sink.holos_as_coded",
        label=f"holos_as_coded ({_round(holos / 1000.0)} t CO2e)",
        kind="sink",
        layer=2,
        color=NODE_COLORS["sink"],
    )

    removed = 0.0
    added = 0.0
    for fork_id in sorted(deltas):
        delta = deltas[fork_id]
        if abs(delta) <= MASS_TOL_KG_CO2E:
            continue
        if delta < 0.0:
            node_id = f"fork.{fork_id}.removed"
            _add_node(
                nodes,
                node_id,
                label=f"{fork_id} removed",
                kind="fork_removed",
                layer=1,
                color=NODE_COLORS["fork_removed"],
            )
            _add_link(
                links,
                nodes,
                "source.source_correct",
                node_id,
                -delta,
                extra={"fork_id": fork_id, "sign": "removed", "delta_kg_co2e": _round(delta)},
            )
            removed += -delta
        else:
            node_id = f"fork.{fork_id}.added"
            _add_node(
                nodes,
                node_id,
                label=f"{fork_id} added",
                kind="fork_added",
                layer=1,
                color=NODE_COLORS["fork_added"],
            )
            _add_link(
                links,
                nodes,
                node_id,
                "sink.holos_as_coded",
                delta,
                extra={"fork_id": fork_id, "sign": "added", "delta_kg_co2e": _round(delta)},
            )
            added += delta

    if interaction < -MASS_TOL_KG_CO2E:
        node_id = "fork.interaction.removed"
        _add_node(
            nodes,
            node_id,
            label="fork interaction removed",
            kind="fork_removed",
            layer=1,
            color=NODE_COLORS["fork_removed"],
        )
        _add_link(
            links,
            nodes,
            "source.source_correct",
            node_id,
            -interaction,
            extra={"fork_id": "INTERACTION", "sign": "removed", "delta_kg_co2e": _round(interaction)},
        )
        removed += -interaction
    elif interaction > MASS_TOL_KG_CO2E:
        node_id = "fork.interaction.added"
        _add_node(
            nodes,
            node_id,
            label="fork interaction added",
            kind="fork_added",
            layer=1,
            color=NODE_COLORS["fork_added"],
        )
        _add_link(
            links,
            nodes,
            node_id,
            "sink.holos_as_coded",
            interaction,
            extra={"fork_id": "INTERACTION", "sign": "added", "delta_kg_co2e": _round(interaction)},
        )
        added += interaction

    through = base - removed
    if through < -MASS_TOL_KG_CO2E:
        raise ValueError(f"Fork-delta through-flow is negative ({through})")
    if through > ZERO_KG:
        _add_link(
            links,
            nodes,
            "source.source_correct",
            "sink.holos_as_coded",
            through,
            extra={"sign": "retained"},
        )

    nodes = _prune_unused_nodes(nodes, links)
    _finalize_node_values(nodes, links)
    return {
        "view": "fork_delta",
        "units": "kg CO2e",
        "gwp": dict(gwp),
        "totals": {
            "source_correct_CO2e_kg": _round(base),
            "holos_as_coded_CO2e_kg": _round(holos),
            "sum_single_fork_delta_kg": _round(sum(deltas.values())),
            "interaction_kg": _round(interaction),
            "CO2e_kg": _round(holos),
            "CO2e_t": _round(holos / 1000.0),
        },
        "fork_deltas_kg_co2e": {key: _round(value) for key, value in sorted(deltas.items())},
        "nodes": _sorted_nodes(nodes),
        "links": _sorted_links(links),
    }


def _prune_unused_nodes(
    nodes: dict[str, dict[str, Any]],
    links: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    used = {str(link["source"]) for link in links} | {str(link["target"]) for link in links}
    return {node_id: node for node_id, node in nodes.items() if node_id in used}


def _finalize_node_values(nodes: dict[str, dict[str, Any]], links: Sequence[Mapping[str, Any]]) -> None:
    inflow: dict[str, float] = {node_id: 0.0 for node_id in nodes}
    outflow: dict[str, float] = {node_id: 0.0 for node_id in nodes}
    for link in links:
        outflow[str(link["source"])] += float(link["value"])
        inflow[str(link["target"])] += float(link["value"])
    for node_id, node in nodes.items():
        node["inflow"] = _round(inflow[node_id])
        node["outflow"] = _round(outflow[node_id])
        if node["kind"] in {"animal", "source_total", "fork_added", "soil", "amendment", "crop"}:
            node["value"] = node["outflow"]
        elif node["kind"] in {"sink", "fork_removed"}:
            node["value"] = node["inflow"]
        else:
            node["value"] = node["inflow"]


def _sorted_nodes(nodes: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(nodes[key]) for key in sorted(nodes, key=lambda node_id: (nodes[node_id]["layer"], node_id))]


def _sorted_links(links: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted((dict(link) for link in links), key=lambda item: (item["source"], item["target"], item["value"]))


def node_balances(view: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    """Inflow and outflow at each node (kg CO2e)."""
    balances = {
        node["id"]: {"inflow": 0.0, "outflow": 0.0, "value": float(node.get("value", 0.0))}
        for node in view["nodes"]
    }
    for link in view["links"]:
        balances[link["source"]]["outflow"] += float(link["value"])
        balances[link["target"]]["inflow"] += float(link["value"])
    return balances


def assert_mass_conserved(view: Mapping[str, Any], *, tol: float = MASS_TOL_KG_CO2E) -> None:
    balances = node_balances(view)
    kinds = {node["id"]: node["kind"] for node in view["nodes"]}
    for node_id, balance in balances.items():
        kind = kinds[node_id]
        if kind in {"animal", "source_total", "fork_added", "soil", "amendment", "crop"}:
            if abs(balance["inflow"]) > tol:
                raise AssertionError(f"{node_id} source has inflow {balance['inflow']}")
            if abs(balance["outflow"] - balance["value"]) > tol:
                raise AssertionError(f"{node_id} source outflow {balance['outflow']} != {balance['value']}")
        elif kind in {"sink", "fork_removed"}:
            if abs(balance["outflow"]) > tol:
                raise AssertionError(f"{node_id} sink has outflow {balance['outflow']}")
            if abs(balance["inflow"] - balance["value"]) > tol:
                raise AssertionError(f"{node_id} sink inflow {balance['inflow']} != {balance['value']}")
        elif abs(balance["inflow"] - balance["outflow"]) > tol:
            raise AssertionError(
                f"{node_id} inflow {balance['inflow']} != outflow {balance['outflow']}"
            )


def build_farm_payload(
    *,
    farm_id: str,
    inputs_file: str,
    source_correct: FarmFlows,
    holos_as_coded: FarmFlows,
    single_forks: Mapping[str, FarmFlows],
    output_version: str,
    engine_version: str = ENGINE_VERSION,
) -> dict[str, Any]:
    views = {
        "source_correct": build_process_sankey(source_correct),
        "holos_as_coded": build_process_sankey(holos_as_coded),
        "fork_delta": build_fork_delta_sankey(source_correct, holos_as_coded, single_forks),
    }
    for view in views.values():
        assert_mass_conserved(view)
    return {
        "schema": SCHEMA,
        "version": output_version,
        "farm_id": farm_id,
        "engine_version": engine_version,
        "inputs_file": inputs_file,
        "fork_set": {
            "source_correct": dict(source_correct.forks),
            "holos_as_coded": dict(holos_as_coded.forks),
            "catalog": fork_catalog(),
        },
        "gwp": {
            **source_correct.gwp,
            "source": "IPCC Fifth Assessment Report, 100-year GWP without climate-carbon feedbacks",
        },
        "units": {
            "value": "kg CO2e",
            "native_ch4": "kg CH4 / year",
            "native_n2o": "kg N2O / year",
            "total_displayed": "t CO2e = kg CO2e / 1000",
        },
        "run_metadata": {
            "source_correct": {"run": source_correct.run, **source_correct.extras},
            "holos_as_coded": {"run": holos_as_coded.run, **holos_as_coded.extras},
        },
        "views": views,
    }


def render_plotly_html(payload: Mapping[str, Any]) -> str:
    """Deterministic Plotly HTML (CDN). Dashboard can also read the JSON."""
    farm_id = json.dumps(payload["farm_id"])
    version = json.dumps(payload["version"])
    data = json.dumps(payload["views"], sort_keys=True, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>ghgsim Sankey {payload["farm_id"]} {payload["version"]}</title>
  <script src="{PLOTLY_CDN}"></script>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 16px; color: #263238; }}
    #view {{ margin: 0 0 12px 0; }}
    #chart {{ width: 100%; height: 720px; }}
  </style>
</head>
<body>
  <h1>Emissions Sankey — <span id="farm"></span> <span id="ver"></span></h1>
  <label>View
    <select id="view">
      <option value="source_correct">source_correct</option>
      <option value="holos_as_coded">holos_as_coded</option>
      <option value="fork_delta">fork delta</option>
    </select>
  </label>
  <div id="chart"></div>
  <script>
    const FARM = {farm_id};
    const VERSION = {version};
    const VIEWS = {data};
    document.getElementById("farm").textContent = FARM;
    document.getElementById("ver").textContent = VERSION;
    function draw(name) {{
      const view = VIEWS[name];
      const nodes = view.nodes;
      const index = Object.fromEntries(nodes.map((n, i) => [n.id, i]));
      const trace = {{
        type: "sankey",
        arrangement: "snap",
        node: {{
          pad: 16,
          thickness: 16,
          label: nodes.map(n => n.label + "\\n" + n.value.toFixed(3) + " kg CO2e"),
          color: nodes.map(n => n.color),
        }},
        link: {{
          source: view.links.map(l => index[l.source]),
          target: view.links.map(l => index[l.target]),
          value: view.links.map(l => l.value),
          color: view.links.map(l => "rgba(120,144,156,0.35)"),
        }},
      }};
      Plotly.react("chart", [trace], {{
        title: FARM + " — " + name + " (" + view.units + ")",
        font: {{ size: 12 }},
        margin: {{ l: 20, r: 20, t: 40, b: 20 }},
      }}, {{responsive: true, displaylogo: false}});
    }}
    const sel = document.getElementById("view");
    sel.addEventListener("change", () => draw(sel.value));
    draw("source_correct");
  </script>
</body>
</html>
"""


def view_image_paths(
    figures_dir: Path,
    farm_id: str,
    view_name: str,
    version: int,
) -> dict[str, Path]:
    """Versioned per-view SVG/PNG paths. Never the html/json stem."""
    prefix = f"sankey_{_slug(farm_id)}_{view_name}"
    stem = f"{prefix}_AN_v{version}"
    return {
        "svg": Path(figures_dir) / f"{stem}.svg",
        "png": Path(figures_dir) / f"{stem}.png",
    }


def next_view_version(figures_dir: Path, farm_id: str, view_name: str) -> int:
    """Next AN_vN free for both the SVG and PNG of this farm view."""
    figures_dir = Path(figures_dir)
    prefix = f"sankey_{_slug(farm_id)}_{view_name}"
    return max(
        next_an_version(figures_dir, prefix, ".svg"),
        next_an_version(figures_dir, prefix, ".png"),
    )


def sankey_figure(payload: Mapping[str, Any], view_name: str):
    """Plotly Sankey for one view. Requires plotly (optional extra `figures`)."""
    import plotly.graph_objects as go

    view = payload["views"][view_name]
    nodes = view["nodes"]
    index = {node["id"]: i for i, node in enumerate(nodes)}
    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=16,
                    thickness=16,
                    label=[f"{node['label']}\n{node['value']:.3f} kg CO2e" for node in nodes],
                    color=[node["color"] for node in nodes],
                ),
                link=dict(
                    source=[index[link["source"]] for link in view["links"]],
                    target=[index[link["target"]] for link in view["links"]],
                    value=[link["value"] for link in view["links"]],
                    color=["rgba(120,144,156,0.35)" for _ in view["links"]],
                ),
            )
        ]
    )
    fig.update_layout(
        title=f"{payload['farm_id']} — {view_name} ({view.get('units', 'kg CO2e')})",
        font_size=12,
        width=1400,
        height=800,
        margin=dict(l=20, r=20, t=48, b=20),
    )
    return fig


def try_render_static(
    payload: Mapping[str, Any],
    dest: Path,
    *,
    view_name: str = "source_correct",
    scale: int = 1,
) -> dict[str, Any]:
    """Write one SVG/PNG with plotly+kaleido when both are installed."""
    dest = Path(dest)
    if dest.exists():
        return {"rendered": False, "reason": f"exists {dest}"}
    try:
        fig = sankey_figure(payload, view_name)
    except ImportError:
        return {"rendered": False, "reason": "plotly not installed"}
    try:
        kwargs: dict[str, Any] = {}
        if dest.suffix.lower() == ".png" and scale != 1:
            kwargs["scale"] = scale
        fig.write_image(str(dest), **kwargs)
    except Exception as exc:  # kaleido / chrome missing
        return {"rendered": False, "reason": str(exc)}
    return {"rendered": dest.exists(), "reason": "plotly+kaleido"}


def write_sankey_view_images(
    payload: Mapping[str, Any],
    figures_dir: Path,
    *,
    scale: int = 2,
    version: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Write per-view SVG + PNG (scale 2). Never overwrites."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    farm_id = str(payload["farm_id"])
    written: dict[str, dict[str, Any]] = {}
    for view_name in SANKEY_VIEWS:
        ver = int(version) if version is not None else next_view_version(figures_dir, farm_id, view_name)
        paths = view_image_paths(figures_dir, farm_id, view_name, ver)
        for path in paths.values():
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite {path}")
        svg_result = try_render_static(payload, paths["svg"], view_name=view_name, scale=1)
        png_result = try_render_static(payload, paths["png"], view_name=view_name, scale=scale)
        written[view_name] = {
            "version": ver,
            "svg": paths["svg"] if svg_result["rendered"] else None,
            "png": paths["png"] if png_result["rendered"] else None,
            "svg_reason": svg_result["reason"],
            "png_reason": png_result["reason"],
        }
    return written


def discover_sankey_payloads(figures_dir: Path) -> list[Path]:
    """Newest sankey_<farm>_AN_vN.json per farm (not per-view image stems)."""
    figures_dir = Path(figures_dir)
    newest: dict[str, tuple[int, Path]] = {}
    for path in figures_dir.glob("sankey_*_AN_v*.json"):
        match = PAYLOAD_JSON_RE.match(path.name)
        if match is None:
            continue
        farm = match.group(1)
        if any(farm.endswith(f"_{view}") for view in SANKEY_VIEWS):
            continue
        version = int(match.group(2))
        prev = newest.get(farm)
        if prev is None or version > prev[0]:
            newest[farm] = (version, path)
    return [item[1] for _, item in sorted(newest.items())]


def export_static_views(
    *,
    repo: Path | None = None,
    figures_dir: Path | None = None,
    scale: int = 2,
    farm_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Export per-view SVG/PNG from existing Sankey JSON. Does not bump html/json."""
    root = repo_root(repo)
    out_dir = Path(figures_dir) if figures_dir is not None else root / "docs" / "figures"
    wanted = {_slug(name) for name in farm_ids} if farm_ids else None
    items: list[dict[str, Any]] = []
    for json_path in discover_sankey_payloads(out_dir):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        farm = _slug(str(payload["farm_id"]))
        if wanted is not None and farm not in wanted:
            continue
        views = write_sankey_view_images(payload, out_dir, scale=scale)
        items.append({"farm_id": payload["farm_id"], "source": json_path.name, "views": views})
    return {"n": len(items), "scale": scale, "items": items}


def write_sankey(
    payload: Mapping[str, Any],
    figures_dir: Path,
    *,
    version: int,
    render_static: bool = True,
    scale: int = 2,
) -> dict[str, Path | None | dict[str, Any]]:
    """Write versioned html/json and optional per-view svg/png. Never overwrites."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    farm = _slug(str(payload["farm_id"]))
    stem = f"sankey_{farm}_AN_v{version}"
    html_path = figures_dir / f"{stem}.html"
    json_path = figures_dir / f"{stem}.json"
    for path in (html_path, json_path):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    html_path.write_text(render_plotly_html(payload), encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written: dict[str, Path | None | dict[str, Any]] = {
        "html": html_path,
        "json": json_path,
        "views": None,
    }
    if render_static:
        written["views"] = write_sankey_view_images(payload, figures_dir, scale=scale)
    return written


def stylized_params(root: Path, spec: Mapping[str, Any]) -> dict[str, float]:
    runner = _load_runner(root)
    params = dict(runner.holos_compute_params(runner.load_registries(), mcf_set="ipcc15C"))
    beef = spec.get("animal_classes", {}).get("beef_cow")
    if beef and "Ym_pct" in beef:
        params["Ym_beef_medium"] = float(beef["Ym_pct"]["value"])
    return params


def build_stylized_payload(
    spec: Mapping[str, Any],
    farm: Mapping[str, Any],
    params: Mapping[str, float],
    *,
    inputs_file: str,
    output_version: str,
) -> dict[str, Any]:
    source = compute_stylized_farm_flows(spec, farm, params, {}, run="source_correct")
    holos = compute_stylized_farm_flows(spec, farm, params, combined_forks(), run="holos_as_coded")
    singles = {
        row["fork_id"]: compute_stylized_farm_flows(
            spec, farm, params, {row["fork_id"]: row["alt"]}, run=row["fork_id"]
        )
        for row in fork_catalog()
    }
    return build_farm_payload(
        farm_id=str(farm["id"]),
        inputs_file=inputs_file,
        source_correct=source,
        holos_as_coded=holos,
        single_forks=singles,
        output_version=output_version,
    )


def build_county_payload(
    root: Path,
    county_name: str,
    *,
    output_version: str,
) -> dict[str, Any]:
    source = compute_county_flows(root, county_name, {}, run="source_correct")
    holos = compute_county_flows(root, county_name, combined_forks(), run="holos_as_coded")
    singles = {
        row["fork_id"]: compute_county_flows(root, county_name, {row["fork_id"]: row["alt"]}, run=row["fork_id"])
        for row in fork_catalog()
    }
    return build_farm_payload(
        farm_id=source.farm_id,
        inputs_file="legacy/livingghg_AN_v3/results_TRIAL_AN_v3/counties_{VT,DE}_AN_v3.csv",
        source_correct=source,
        holos_as_coded=holos,
        single_forks=singles,
        output_version=output_version,
    )


def generate(
    *,
    repo: Path | None = None,
    figures_dir: Path | None = None,
    farm_ids: Sequence[str] | None = None,
    counties: Sequence[str] | None = None,
    render_static: bool = True,
) -> dict[str, Any]:
    """Build Sankeys for stylized farms (default: all) and optional counties."""
    root = repo_root(repo)
    data_dir = root / "data"
    farms_yaml = latest_versioned(data_dir, "stylized_farms", ".yaml")
    spec = load_stylized_spec(farms_yaml)
    params = stylized_params(root, spec)
    out_dir = Path(figures_dir) if figures_dir is not None else root / "docs" / "figures"
    wanted = set(farm_ids) if farm_ids else None
    farms = [farm for farm in spec["farms"] if wanted is None or farm["id"] in wanted]
    if wanted is not None:
        missing = wanted - {farm["id"] for farm in farms}
        if missing:
            raise ValueError(f"Unknown stylized farm id(s): {sorted(missing)}")
    written: list[dict[str, Any]] = []
    rel_yaml = farms_yaml.resolve().relative_to(root.resolve()).as_posix()

    def _write(payload: dict[str, Any]) -> dict[str, Any]:
        farm = _slug(str(payload["farm_id"]))
        version = next_an_version(out_dir, f"sankey_{farm}", ".json")
        payload = dict(payload)
        payload["version"] = f"AN_v{version}"
        # Rebuild HTML title version; views are already version-independent.
        paths = write_sankey(payload, out_dir, version=version, render_static=render_static)
        return {"farm_id": payload["farm_id"], "version": version, "paths": paths, "payload": payload}

    for farm in farms:
        version = next_an_version(out_dir, f"sankey_{_slug(farm['id'])}", ".json")
        payload = build_stylized_payload(
            spec, farm, params, inputs_file=rel_yaml, output_version=f"AN_v{version}"
        )
        written.append(_write(payload))
    for county in counties or ():
        version_guess_id = f"county_{_slug(county).upper()}"
        version = next_an_version(out_dir, f"sankey_{version_guess_id}", ".json")
        payload = build_county_payload(root, county, output_version=f"AN_v{version}")
        written.append(_write(payload))
    return {"inputs_file": rel_yaml, "n": len(written), "items": written}
