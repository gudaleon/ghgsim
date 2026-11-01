# livingghg (v0.2.0, Phase 2) - Apache-2.0
Open, versioned engine for IPCC **2006 vs 2019 Refinement** agricultural GHG:
- soil N2O: direct (Eq 11.1) and indirect (Eq 11.9, 11.10);
- Tier 2 enteric CH4 (Eq 10.21);
- **manure** CH4 (Eq 10.23) and N2O, direct (Eq 10.25) and indirect (Eq 10.26-10.29), with PRP N routed to soils;
- **fork registry** for importance-ranked adaptive debugging: OAT screen, LHS, and Sobol (SALib, optional).
Details:
- Parameters: `livingghg/data/ipcc_params_AN_v2.csv` (source, table, page, status). Non-VERIFIED rows raise unless `allow_unverified=True`.
- Forks: `livingghg/data/forks_AN_v2.json` (F001-F009).
- Examples: `examples/example_farm_AN_v2.json` holds **stylized example inputs**.
- County data: `data_nass/`, the USDA NASS 2022 Census extract (see README_NASS_AN_v1.md).
- Scripts: `scripts/fetch_nass_census2022.py`, `scripts/run_counties.py`, `scripts/sobol.py`; Bubble PC batch `run_bubble_AN_v1.bat`.
- Run: `pip install -e .[test,sobol]; pytest; python examples/demo.py`
- GWP100 (CH4 28, N2O 265; AR5) is a user setting in `engine.py`.
