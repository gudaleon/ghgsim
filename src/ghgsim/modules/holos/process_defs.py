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
