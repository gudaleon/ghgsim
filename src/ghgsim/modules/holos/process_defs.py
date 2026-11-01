"""
Holos Route A process definitions (Reichert 1995 ProcessDef).

Equations are taken from IPCC 2006 Vol 4 Ch 10, not from Holos source.
holos_as_coded forks encode confirmed Holos discrepancies as alternate
rate strings. Holos behaviour is described, not copied, in fork equations.
"""

from ghgsim.core.processes import ForkOption, ProcessDef
from ghgsim.core.variables import ProgramVariable


def ge_intake_variable() -> ProgramVariable:
    """
    Gross energy intake from net energy and digestibility (IPCC 2006 Eq 10.3).

    Default uses DE%. The holos_as_coded path is a separate ProgramVariable
    returned by ge_intake_variable_holos_tdn().
    """
    return ProgramVariable(
        name="GE",
        units="MJ / day",
        description="Gross energy intake, IPCC 2006 Eq 10.3 with DE%",
        equation=(
            "((NE_m + NE_a + NE_l + NE_work + NE_p) / RE_m "
            "+ (NE_g / RE_g if RE_g != 0 else 0.0)) / (DE_percent / 100.0)"
        ),
        dependencies=["NE_m", "NE_a", "NE_l", "NE_work", "NE_p", "NE_g", "RE_m", "RE_g", "DE_percent"],
    )


def ge_intake_variable_holos_tdn() -> ProgramVariable:
    """Holos-as-coded GE: same Eq 10.3 structure with TDN% in the denominator."""
    return ProgramVariable(
        name="GE",
        units="MJ / day",
        description="Gross energy intake with TDN% denominator (Holos-as-coded)",
        equation=(
            "((NE_m + NE_a + NE_l + NE_work + NE_p) / RE_m "
            "+ (NE_g / RE_g if RE_g != 0 else 0.0)) / (TDN_percent / 100.0)"
        ),
        dependencies=["NE_m", "NE_a", "NE_l", "NE_work", "NE_p", "NE_g", "RE_m", "RE_g", "TDN_percent"],
    )


def urinary_energy_ipcc() -> ProgramVariable:
    """
    UE as a fraction of GE (IPCC 2006 Vol 4 Ch 10 p. 10.54).

    Typical UE = 0.04. Exception: high-concentrate diets with DE% greater
    than approximately 80% use UE = 0.02.
    """
    return ProgramVariable(
        name="UE",
        units="fraction of GE",
        description="Urinary energy fraction, IPCC 2006 p. 10.54",
        equation="0.02 if DE_percent >= 80.0 else 0.04",
        dependencies=["DE_percent"],
    )


def urinary_energy_holos() -> ProgramVariable:
    """Holos-as-coded UE: 0.02 when grain% >= 85, else 0.04."""
    return ProgramVariable(
        name="UE",
        units="fraction of GE",
        description="Urinary energy fraction, Holos-as-coded grain-percent switch",
        equation="0.02 if (100.0 - forage_percent) >= 85.0 else 0.04",
        dependencies=["forage_percent"],
    )


def enteric_ch4_process() -> ProcessDef:
    """Daily enteric CH4, IPCC 2006 Eq 10.21 without the 365-day factor."""
    process = ProcessDef(
        name="enteric_methane",
        description="Enteric CH4 from gross energy and Ym (IPCC 2006 Eq 10.21, daily)",
        rate_equation="GE * (Ym_percent / 100.0) / CH4_ENERGY",
        stoichiometry={"CH4_kg_day": 1.0},
        unit="kg CH4 / head / day",
        forks={
            "holos_as_coded": ForkOption(
                name="holos_as_coded",
                description="CE-06: dairy calf enteric CH4 forced to zero",
                modified_equation="0.0 if animal_class == 'calf' else GE * (Ym_percent / 100.0) / CH4_ENERGY",
                issue_ref="CE-06",
                label="holos_as_coded",
            ),
        },
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/",
        equation="Equation 10.21",
        page="10.30",
        notes="IPCC 2006 Vol 4 Ch 10; daily form omits the 365 factor",
    )
    return process


def volatile_solids_process() -> ProcessDef:
    """Daily VS excretion, IPCC 2006 Eq 10.24. TDN fork is a modified equation."""
    process = ProcessDef(
        name="volatile_solids",
        description="Volatile solids excretion (IPCC 2006 Eq 10.24)",
        rate_equation=(
            "(GE * (1.0 - DE_percent / 100.0) + UE * GE) "
            "* (1.0 - ASH_percent / 100.0) / GE_PER_KG_DM"
        ),
        stoichiometry={"VS_kg_day": 1.0},
        unit="kg VS / head / day",
        forks={
            "holos_as_coded": ForkOption(
                name="holos_as_coded",
                description="AUDIT-VS-TDN: indigestible energy uses TDN% instead of DE%",
                modified_equation=(
                    "(GE * (1.0 - TDN_percent / 100.0) + UE * GE) "
                    "* (1.0 - ASH_percent / 100.0) / GE_PER_KG_DM"
                ),
                issue_ref="AUDIT-VS-TDN",
                label="holos_as_coded",
            ),
        },
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/",
        equation="Equation 10.24",
        page="10.54",
        notes="IPCC 2006 Vol 4 Ch 10; ASH as percent of dry matter",
    )
    return process


def calf_vs_holos_process() -> ProcessDef:
    """Holos-as-coded calf VS (CE-07). Coefficient is UNVERIFIED."""
    process = ProcessDef(
        name="calf_volatile_solids_holos",
        description="Holos dairy calf VS = 0.0093 * live weight (CE-07, UNVERIFIED)",
        rate_equation="calf_vs_coeff * weight_kg",
        stoichiometry={"VS_kg_day": 1.0},
        unit="kg VS / head / day",
    )
    process.add_source(
        doi_or_url="Holos DairyCattleResultsService.cs:159 (traceability only; not VERIFIED)",
        equation="Holos internal Equation 4.1.2-1",
        page="",
        notes="No primary published source found for 0.0093; UNVERIFIED",
    )
    return process


def manure_ch4_process() -> ProcessDef:
    """Daily manure CH4, IPCC 2006 Eq 10.23 without the 365-day factor."""
    process = ProcessDef(
        name="manure_methane",
        description="Manure CH4 from VS, B0, and MCF (IPCC 2006 Eq 10.23, daily)",
        rate_equation="VS * B0 * MCF * CH4_M3_TO_KG",
        stoichiometry={"CH4_kg_day": 1.0},
        unit="kg CH4 / head / day",
        forks={
            "holos_as_coded": ForkOption(
                name="holos_as_coded",
                description=(
                    "CE-14: Holos cover remaining = 1 - reduction "
                    "(0.40 crust / 0.25 solid cover); MCF is uncovered-tank"
                ),
                modified_equation="VS * B0 * MCF * CH4_M3_TO_KG * (1.0 - cover_reduction)",
                issue_ref="CE-14",
                label="holos_as_coded",
            ),
        },
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/",
        equation="Equation 10.23",
        page="10.53",
        notes="IPCC 2006 Vol 4 Ch 10; daily form omits the 365 factor; 0.67 kg/m3 is CH4 density",
    )
    return process


def manure_n2o_direct_process() -> ProcessDef:
    """Direct manure N2O-N, IPCC 2006 Eq 10.25 (before 44/28)."""
    process = ProcessDef(
        name="manure_n2o_direct",
        description="Direct manure N2O-N (IPCC 2006 Eq 10.25, N2O-N)",
        rate_equation="Nex_kg * EF3",
        stoichiometry={"N2O_N_kg": 1.0},
        unit="kg N2O-N",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/",
        equation="Equation 10.25",
        page="10.55",
        notes="IPCC 2006 Vol 4 Ch 10; convert N2O-N to N2O with 44/28",
    )
    return process


def manure_n2o_indirect_vol_process() -> ProcessDef:
    """Indirect manure N2O-N from volatilisation, IPCC 2006 Eq 10.26-10.27."""
    process = ProcessDef(
        name="manure_n2o_indirect_vol",
        description="Indirect manure N2O-N via volatilisation (IPCC 2006 Eq 10.26-10.27)",
        rate_equation="Nex_kg * FracGasMS * EF4",
        stoichiometry={"N2O_N_kg": 1.0},
        unit="kg N2O-N",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/",
        equation="Equations 10.26 and 10.27",
        page="10.56",
        notes="IPCC 2006 Vol 4 Ch 10; convert N2O-N to N2O with 44/28",
    )
    return process


def swine_enteric_tier1_process() -> ProcessDef:
    """Daily swine enteric CH4 from the IPCC Tier 1 emission factor."""
    process = ProcessDef(
        name="swine_enteric_tier1",
        description="Swine enteric CH4, IPCC 2006/2019 Table 10.10 Tier 1 (daily)",
        rate_equation="EF_enteric_kg_head_yr / 365.0",
        stoichiometry={"CH4_kg_day": 1.0},
        unit="kg CH4 / head / day",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_10_Ch10_Livestock.pdf",
        equation="Equation 10.19",
        page="10.28",
        notes="Table 10.10 developed-country / high-productivity swine EF = 1.5 kg CH4 head-1 yr-1",
    )
    return process


def poultry_enteric_process() -> ProcessDef:
    """Poultry enteric CH4 is not developed (IPCC Table 10.9 / 10.10)."""
    process = ProcessDef(
        name="poultry_enteric",
        description="Poultry enteric CH4 = 0 (IPCC 2006/2019 Table 10.10: insufficient data)",
        rate_equation="0.0",
        stoichiometry={"CH4_kg_day": 1.0},
        unit="kg CH4 / head / day",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_10_Ch10_Livestock.pdf",
        equation="Table 10.9 / Table 10.10",
        page="10.27 / 10.28",
        notes="Method 'Not developed'; EF cell 'Insufficient data for calculation'",
    )
    return process


def manure_n2o_indirect_leach_process() -> ProcessDef:
    """Indirect manure N2O-N from leaching, IPCC 2006 Eq 10.28-10.29 / 2019 Table 10.22."""
    process = ProcessDef(
        name="manure_n2o_indirect_leach",
        description="Indirect manure N2O-N via leaching (IPCC 2006 Eq 10.28-10.29)",
        rate_equation="Nex_kg * FracLeachMS * EF5",
        stoichiometry={"N2O_N_kg": 1.0},
        unit="kg N2O-N",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4/19R_V4_Ch10_Livestock.pdf",
        equation="Equations 10.28 and 10.29",
        page="10.97 (2019 Table 10.22 FracLeachMS)",
        notes=(
            "IPCC 2006 provides no default FracLeachMS (country-specific). "
            "2019 Table 10.22 (Updated) publishes defaults; 0 for liquid/litter systems."
        ),
    )
    return process


def soil_n2o_direct_process() -> ProcessDef:
    """Direct soil N2O-N, IPCC 2006 Eq 11.1 (before 44/28)."""
    process = ProcessDef(
        name="soil_n2o_direct",
        description="Direct soil N2O-N (IPCC 2006 Eq 11.1)",
        rate_equation="(F_SN + F_ON + F_CR + F_SOM) * EF1 + F_PRP_CPP * EF3PRP",
        stoichiometry={"N2O_N_kg": 1.0},
        unit="kg N2O-N",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf",
        equation="Equation 11.1",
        page="11.7",
        notes="EF1 for F_SN/F_ON/F_CR/F_SOM; EF3PRP for urine/dung on PRP",
    )
    return process


def soil_n2o_indirect_vol_process() -> ProcessDef:
    """Indirect soil N2O-N from volatilisation, IPCC 2006 Eq 11.9."""
    process = ProcessDef(
        name="soil_n2o_indirect_vol",
        description="Indirect soil N2O-N via volatilisation (IPCC 2006 Eq 11.9)",
        rate_equation="(F_SN * FracGASF + (F_ON + F_PRP_CPP) * FracGASM) * EF4",
        stoichiometry={"N2O_N_kg": 1.0},
        unit="kg N2O-N",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf",
        equation="Equation 11.9",
        page="11.21",
        notes="2006 does not subtract volatilisation from the Eq 11.1 N inputs",
    )
    return process


def soil_n2o_indirect_leach_process() -> ProcessDef:
    """Indirect soil N2O-N from leaching, IPCC 2006 Eq 11.10."""
    process = ProcessDef(
        name="soil_n2o_indirect_leach",
        description="Indirect soil N2O-N via leaching (IPCC 2006 Eq 11.10)",
        rate_equation="(F_SN + F_ON + F_CR + F_SOM + F_PRP_CPP) * FracLEACH * EF5",
        stoichiometry={"N2O_N_kg": 1.0},
        unit="kg N2O-N",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf",
        equation="Equation 11.10",
        page="11.21",
        notes="2006 Table 11.3 FracLEACH = 0.30 where leaching/runoff occurs",
    )
    return process


def lime_co2_process() -> ProcessDef:
    """CO2-C from limestone and dolomite, IPCC 2006 Eq 11.12."""
    process = ProcessDef(
        name="lime_co2",
        description="CO2-C from lime application (IPCC 2006 Eq 11.12)",
        rate_equation="M_limestone_t * EF_limestone + M_dolomite_t * EF_dolomite",
        stoichiometry={"CO2_C_t": 1.0},
        unit="tonne C",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf",
        equation="Equation 11.12",
        page="11.27",
        notes="EF limestone 0.12 and dolomite 0.13 tonne C / tonne lime; convert with 44/12",
    )
    return process


def urea_co2_process() -> ProcessDef:
    """CO2-C from urea application, IPCC 2006 Eq 11.13."""
    process = ProcessDef(
        name="urea_co2",
        description="CO2-C from urea application (IPCC 2006 Eq 11.13)",
        rate_equation="M_urea_t * EF_urea",
        stoichiometry={"CO2_C_t": 1.0},
        unit="tonne C",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf",
        equation="Equation 11.13",
        page="11.32",
        notes="EF urea 0.20 tonne C / tonne urea; convert with 44/12",
    )
    return process


def field_fam_process() -> ProcessDef:
    """Animal manure N applied to soils, IPCC 2006 Eq 11.4."""
    process = ProcessDef(
        name="field_fam",
        description="FAM from managed manure remaining after storage (IPCC 2006 Eq 11.4)",
        rate_equation="N_MMS_Avb_kg * (1.0 - FracFEED - FracFUEL - FracCNST)",
        stoichiometry={"F_AM_kg": 1.0},
        unit="kg N",
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/4_Volume4/V4_11_Ch11_N2O&CO2.pdf",
        equation="Equation 11.4",
        page="11.13",
        notes="If FracFEED/FracFUEL/FracCNST are unavailable, Chapter 11 uses N_MMS_Avb as FAM (fractions = 0)",
    )
    return process


def turkey_manure_ch4_holos_process() -> ProcessDef:
    """Turkey manure CH4: IPCC Eq 10.23 default; holos_as_coded CE-10 is zero."""
    process = ProcessDef(
        name="turkey_manure_methane_holos",
        description="Turkey manure CH4 (IPCC 2006 Eq 10.23); holos_as_coded CE-10 is zero",
        rate_equation="VS * B0 * MCF * CH4_M3_TO_KG",
        stoichiometry={"CH4_kg_day": 1.0},
        unit="kg CH4 / head / day",
        forks={
            "holos_as_coded": ForkOption(
                name="holos_as_coded",
                description="CE-10: Holos CLI turkey manure CH4 forced to zero",
                modified_equation="0.0",
                issue_ref="CE-10",
                label="holos_as_coded",
            ),
        },
    )
    process.add_source(
        doi_or_url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/",
        equation="Equation 10.23 (source_correct); Holos CLI CE-10 (holos_as_coded)",
        page="10.53",
        notes="Holos file:line citations are traceability only; no GPL code copied",
    )
    return process
