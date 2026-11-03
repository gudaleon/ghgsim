"""
IPCC 2019 Refinement Eq 11.6 (Updated) and Eq 11.7: crop residue N (F_CR).

Opened: 2019 Refinement Vol 4 Ch 11 PDF, Table 11.1a (New) p. 11.18.
Annual crops: FracRenew = 1. FracRemove and FracBurnt default to 0 when
removal/burning data are absent (IPCC text). Coefficients are crop-specific;
activity (area, yield) is supplied by the caller.
"""

from collections.abc import Mapping
from typing import Any

from ghgsim.core.module import Citation, ParamRef, VarSpec, validate_module
from ghgsim.modules.holos.process_defs import crop_residue_n_process

_FCR = crop_residue_n_process()

# Table 11.1a (New) p. 11.18 crop keys used in param ids.
TABLE_11_1A_CROPS = (
    "maize",
    "soybeans",
    "winter_wheat",
    "spring_wheat",
    "grains",
)

# NASS / farm aliases -> Table 11.1a key. Wheat -> winter wheat is a mapping
# choice (Spring Wheat RS = 0.28); values themselves are VERIFIED.
CROP_ALIASES = {
    "maize": "maize",
    "corn": "maize",
    "corn_grain": "maize",
    "soybeans": "soybeans",
    "soybean": "soybeans",
    "winter_wheat": "winter_wheat",
    "spring_wheat": "spring_wheat",
    "wheat": "winter_wheat",
    "grains": "grains",
    "generic_grains": "grains",
}

NASS_SHORT_DESC = {
    "maize": "CORN, GRAIN",
    "soybeans": "SOYBEANS",
    "winter_wheat": "WHEAT",
    "wheat": "WHEAT",
}


def resolve_crop_key(crop: str) -> str:
    """Map a farm/NASS crop name to a Table 11.1a key."""
    key = CROP_ALIASES.get(str(crop).strip().lower())
    if key is None:
        raise ValueError(
            f"Unknown crop '{crop}'. Table 11.1a keys: {TABLE_11_1A_CROPS}. "
            f"Aliases: {sorted(CROP_ALIASES)}"
        )
    return key


def crop_coeff_param_keys(crop_key: str) -> dict[str, str]:
    """Registry keys for N_AG, N_BG, R_AG, RS, DRY of one Table 11.1a crop."""
    return {
        "N_AG": f"IPCC2019.N_AG.{crop_key}",
        "N_BG": f"IPCC2019.N_BG.{crop_key}",
        "R_AG": f"IPCC2019.R_AG.{crop_key}",
        "RS": f"IPCC2019.RS.{crop_key}",
        "DRY": f"IPCC2019.DRY.{crop_key}",
    }


def coeffs_from_params(crop: str, params: Mapping[str, Any]) -> dict[str, float]:
    """Read Table 11.1a coefficients from a compute-params dict (short names)."""
    key = resolve_crop_key(crop)
    return {
        "N_AG": float(params[f"N_AG_{key}"]),
        "N_BG": float(params[f"N_BG_{key}"]),
        "R_AG": float(params[f"R_AG_{key}"]),
        "RS": float(params[f"RS_{key}"]),
        "DRY": float(params[f"DRY_{key}"]),
    }


class IPCC2019CropResidue:
    """Tier 1 F_CR for one crop stand (Eq 11.6 Updated / Eq 11.7)."""

    id = "ipcc2019.crop_residue"
    version = "1.0.0"

    inputs = {
        "crop": VarSpec("crop", "dimensionless", "Table 11.1a crop key or alias", "scalar", True),
        "area_ha": VarSpec("area_ha", "ha", "Harvested area", "scalar", True),
        "yield_fresh_kg_ha": VarSpec(
            "yield_fresh_kg_ha", "kg fresh / ha", "Fresh yield (Eq 11.7 Crop = yield * DRY)", "scalar", True
        ),
        "FracRenew": VarSpec("FracRenew", "fraction", "Fraction of area renewed (annual = 1)", "scalar", False),
        "FracRemove": VarSpec("FracRemove", "fraction", "Fraction of AG residue removed", "scalar", False),
        "FracBurnt": VarSpec("FracBurnt", "fraction", "Fraction of AG residue burnt", "scalar", False),
        "CF": VarSpec("CF", "dimensionless", "Combustion factor (unused when FracBurnt = 0)", "scalar", False),
    }

    parameters = {
        "N_AG_maize": ParamRef("IPCC2019.N_AG.maize", "Table 11.1a maize above-ground N fraction"),
        "N_BG_maize": ParamRef("IPCC2019.N_BG.maize", "Table 11.1a maize below-ground N fraction"),
        "R_AG_maize": ParamRef("IPCC2019.R_AG.maize", "Table 11.1a maize AG residue / crop DM"),
        "RS_maize": ParamRef("IPCC2019.RS.maize", "Table 11.1a maize root / shoot"),
        "DRY_maize": ParamRef("IPCC2019.DRY.maize", "Table 11.1a maize dry-matter fraction"),
        "FracRenew_annual": ParamRef("IPCC2019.FracRenew.annual", "Annual crops FracRenew = 1"),
        "FracRemove_default": ParamRef("IPCC2019.FracRemove.default_zero", "No-removal default"),
        "FracBurnt_default": ParamRef("IPCC2019.FracBurnt.default_zero", "No-burning default"),
        "CF_default": ParamRef("IPCC2019.CF.unused_when_unburnt", "CF unused when FracBurnt = 0"),
    }

    outputs = {
        "F_CR": VarSpec("F_CR", "kg N / year", "Residue N returned to soil (Eq 11.6)", "scalar", True),
        "Crop_kg_ha": VarSpec("Crop_kg_ha", "kg DM / ha", "Dry-matter crop yield (Eq 11.7)", "scalar", True),
        "AGDM_kg_ha": VarSpec("AGDM_kg_ha", "kg DM / ha", "Above-ground residue DM", "scalar", True),
        "AGR_kg": VarSpec("AGR_kg", "kg DM / year", "Above-ground residue dry matter", "scalar", True),
        "BGR_kg": VarSpec("BGR_kg", "kg DM / year", "Below-ground residue dry matter", "scalar", True),
        "crop_key": VarSpec("crop_key", "dimensionless", "Resolved Table 11.1a key", "scalar", True),
    }

    sources = [
        Citation(
            source="2019 Refinement to the 2006 IPCC Guidelines, Volume 4, Chapter 11",
            table="Table 11.1a (New)",
            equation="Eq 11.6 (Updated), Eq 11.7",
            page="11.14-11.18",
        ),
    ]

    def compute(self, inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
        crop_key = resolve_crop_key(str(inputs["crop"]))
        coeffs = coeffs_from_params(crop_key, params)
        area = float(inputs["area_ha"])
        yield_fresh = float(inputs["yield_fresh_kg_ha"])
        frac_renew = float(inputs.get("FracRenew") if inputs.get("FracRenew") not in (None, "") else params.get("FracRenew_annual", 1.0))
        frac_remove = float(inputs.get("FracRemove") if inputs.get("FracRemove") not in (None, "") else params.get("FracRemove_default", 0.0))
        frac_burnt = float(inputs.get("FracBurnt") if inputs.get("FracBurnt") not in (None, "") else params.get("FracBurnt_default", 0.0))
        cf = float(inputs.get("CF") if inputs.get("CF") not in (None, "") else params.get("CF_default", 0.0))
        dry = coeffs["DRY"]
        r_ag = coeffs["R_AG"]
        crop_dm = yield_fresh * dry
        agdm = crop_dm * r_ag
        agr = agdm * area
        bgr = (crop_dm + agdm) * coeffs["RS"] * area * frac_renew
        f_cr = _FCR.compute_rate(
            {
                "yield_fresh_kg_ha": yield_fresh,
                "DRY": dry,
                "R_AG": r_ag,
                "area_ha": area,
                "N_AG": coeffs["N_AG"],
                "FracRemove": frac_remove,
                "FracBurnt": frac_burnt,
                "CF": cf,
                "RS": coeffs["RS"],
                "FracRenew": frac_renew,
                "N_BG": coeffs["N_BG"],
            }
        )
        return {
            "F_CR": f_cr,
            "Crop_kg_ha": crop_dm,
            "AGDM_kg_ha": agdm,
            "AGR_kg": agr,
            "BGR_kg": bgr,
            "crop_key": crop_key,
        }


def f_cr_from_crops(crops: list[Mapping[str, Any]], params: Mapping[str, Any]) -> dict[str, Any]:
    """Sum Eq 11.6 F_CR over a list of crop specs. Returns F_CR and per-crop rows."""
    module = IPCC2019CropResidue()
    total = 0.0
    rows: list[dict[str, Any]] = []
    for spec in crops:
        out = module.compute(
            {
                "crop": spec["crop"],
                "area_ha": spec["area_ha"],
                "yield_fresh_kg_ha": spec["yield_fresh_kg_ha"],
                "FracRenew": spec.get("FracRenew"),
                "FracRemove": spec.get("FracRemove"),
                "FracBurnt": spec.get("FracBurnt"),
                "CF": spec.get("CF"),
            },
            params,
        )
        total += float(out["F_CR"])
        rows.append({"crop": spec["crop"], **out})
    return {"F_CR": total, "crops": rows}


errors = validate_module(IPCC2019CropResidue())
if errors:
    raise ValueError(f"IPCC2019CropResidue module validation failed: {errors}")
