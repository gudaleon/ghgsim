# Phase B follow-up (AN_v2)

Correction of `HOLOS.N2O.ef1` on PR #16. AN_v1 mislabelled the Holos-coded
direct soil N2O EF. This file does not overwrite `PHASE_B_FOLLOWUP_AN_v1.md`.

## 1. What Holos actually codes

Opened (read only; no GPL copied):

- Pogue et al. (2025). *Holos V4.0 Algorithm Document*, repo-root `.docx` at
  holos-aafc/Holos commit `036f862`, **Section 2.5** (Nitrous oxide emission
  factor calculation, IPCC Canada Tier 2).
- `H.Core/Calculators/Nitrogen/N2OEmissionFactorCalculator.cs:478-656,777-788`
  at the same commit.

Holos implements Liang et al. (2020) *Nutr. Cycl. Agroecosyst.* 117:145–167,
DOI [10.1007/s10705-020-10058-w](https://doi.org/10.1007/s10705-020-10058-w):

- \(EF_{CT,P>PE}=\exp(0.00558\,P_i-7.7)\) (Eq 2.5.1-1)
- \(EF_{CT,P\le PE}=\exp(0.00558\,PE_i-7.7)\) (Eq 2.5.1-2)

\(P_i\) and \(PE_i\) are May–October growing-season precipitation and potential
evapotranspiration in mm (Holos: CanSIS 1980–2010). A dimensionless \(P/PE\)
ratio is **not** the Holos climate input.

Topography (Eq 2.5.2): humid (\(P/PE>1\)) uses \(EF_{CT}(P)\); dry uses
\(EF_{CT}(PE)\times FR_{Topo}+EF_{CT}(P)\times(1-FR_{Topo})\); irrigated uses
\(EF_{CT}(PE)\). Rochette et al. (2008) *Can. J. Soil Sci.* 88:641–654 is
cited for \(FR_{Topo}\) only, **not** Rochette Eq 3
\(EF_{eco}=0.022\times(P/PE)-0.0048\).

Edaphic / winter (Eq 2.5.3-2): \(EF_{Base}=EF_{Topo}\times RF_{TX}\times(1/0.645)\).
C# line 629: `const double winterCorrection = (1.0 / 0.645);`. \(RF_{TX}\)
defaults to 1 when texture is unspecified (manual Table 13).

The opened C# matches the opened V4 section. There is **no** `holos_as_coded`
EF1 bug fork.

## 2. Model-version options (not a bug fork)

`HOLOS.N2O.ef1` in `data/holos_forks_AN_v6.json`:

| option | meaning |
| --- | --- |
| `ipcc2006_ef1` (default) | IPCC 2006 Vol 4 Ch 11 Table 11.1 EF1 = 0.01 |
| `holos_liang2020` | Holos V4 Sec 2.5 / Liang 2020, as coded at `N2OEmissionFactorCalculator.cs:478-656,777-788` |

Missing growing-season P and PE → `EF1_status = UNVERIFIED-input` and the
engine keeps IPCC EF1 = 0.01. A `P_PE` ratio, including an assumed
\(P/PE=1\) clamp, is ignored.

AN_v1 labelled ghgsim’s IPCC 0.01 as `holos_as_coded` and Rochette Eq 3 as
`source_correct`. That is inverted against the Holos codebase and is withdrawn.

## 3. Dropped county finding

AN_v1 reported **+217,229 t CO2e** from Rochette \(EFeco=0.017\) at assumed
\(P/PE=1\). That clamp is not Vermont/Delaware growing-season weather, and it
is not the Holos EF. **Do not cite it.**

This run still has no county May–October P and PE (PRISM/NOAA/CanSIS). The
`holos_liang2020` option is therefore `UNVERIFIED-input` for VT/DE. No Liang
county delta is reported.

Reported county change (IPCC EF1 = 0.01 only), 17 VT+DE counties:

| total | t CO2e |
| --- | ---: |
| Baseline (trial soil, no FAM link) | 1,346,733 |
| Expanded (Eq 11.6 \(F_{CR}\) + Falcone hog/poultry N + cattle FAM) | 1,400,411 |
| \(\Delta\) expanded − baseline | **+53,678** |

Census gap unchanged: `nass_census2022_county_AN_v1.csv.gz` has cattle
inventory only. Poultry/swine enter as Falcone 2017 excreted N, not Census
heads. Script: `scripts/holos_vt_de_poultry_crops_AN_v2.py`.

## 4. APSIM provenance requirement

Holzworth, D. P., Huth, N. I., Fainges, J., Brown, H., Zurcher, E., Cichota,
R., Verrall, S., Herrmann, N. I., Zheng, B., & Snow, V. O. (2018). APSIM Next
Generation: Overcoming challenges in modernising a farming systems model.
*Environmental Modelling & Software*, **103**, 43–51.
DOI [10.1016/j.envsoft.2018.02.002](https://doi.org/10.1016/j.envsoft.2018.02.002).

Every ghgsim run now records `release_number` (package version) and
`commit_hash` (git SHA) via `ghgsim.core.provenance.run_identity()`. That
object is written on fork-diagram JSON, Sankey JSON, stylized-fork meta,
county-run meta, and archive `provenance.yaml`.

## 5. Versioned files (never overwrite)

- `data/holos_forks_AN_v6.json`
- `data/holos_params_canada_AN_v9.csv`
- `data/stylized_farms_AN_v6.yaml`
- `data/coefficient_trace_AN_v8.csv`
- `data/holos_fork_deltas_stylized_AN_v5.csv`
- `data/holos_vt_de_poultry_crops_AN_v2.csv`
- `docs/figures/fork_diagram_AN_v5.*`
- new `docs/figures/sankey_*_AN_vN.*`
- `docs/PHASE_B_FOLLOWUP_AN_v2.md` (this file)

No GPL Holos source was copied.
