# Phase C: liquid manure storage (AN_v1)

Dairy and swine liquid manure CH4, from the opened Holos V4 algorithm
document. This file does not overwrite earlier phase notes. No GPL source
was copied. Do not merge.

## What was opened

- Pogue et al. (2026) *Holos Version 4.0 Algorithm Documentation*, print PDF
  on holos-aafc/Holos `main`
  (`Pogue et al 2026_Printversion_Holos_V4.0_Algorithm_Document_ENGLISH_FINAL.pdf`),
  **Section 4.1.3**, pages 161–162 (Eq 4.1.3-1 through 4.1.3-10).
- The same equations in the public C#, read only:
  `AnimalResultsServiceBase.cs:986-1036` and `:1052-1093`,
  `ManureStorageMath.cs:16-51`,
  `ClimateData.cs:511-521`.

The February 2025 draft docx is different (T1 = 303.16 K, E = 15,175 cal/mol,
MDP default 0.45, and a full empty instead of a 95% cap). The 2026 print and
the C# agree with each other, so that draft is not used.

Mangino et al. (2001) and Vergé et al. (2006) are the manual's cited method.
They were not re-opened. The printed constants are SOURCE-TRACED to the
algorithm document, not VERIFIED against those papers. IPCC's Annex form of
the van 't Hoff factor uses 15,175 cal/mol and 303.16 K; that is not what
Holos V4 prints.

## Model version (`HOLOS.CH4.liquid_tank`)

| option | meaning |
|---|---|
| `ipcc2006_eq10_23` (default) | IPCC 2006 Eq 10.23 for every system |
| `holos_v4_liquid_tank` | Holos V4 Sec 4.1.3 for liquid dairy and swine |

Printed daily climate factor (Eq 4.1.3-2), with T2 the mean of the window in kelvin:

`f = 1 - (1 - exp(E*(T2-T1)/(R*T1*T2)))^(1/30)`

T1 = 308.16 K, E = 19,347 cal/mol, R = 1.987 cal/K/mol. If the outdoor
temperature is at or below 1 °C, Eq 4.1.3-1 uses 1 °C. MDP = 1
(Eq 4.1.3-4). Volatile solids carry forward (Eq 4.1.3-5). A removal
yesterday multiplies that carryover by `(1 - fraction)` and the fraction
is capped at 0.95 (Eq 4.1.3-6, 95% emptying efficiency). Methane is
`VSconsumed * B0 * 0.67`, and a natural crust or solid cover multiplies by
`(1 - 0.40)` or `(1 - 0.25)` (Eq 4.1.3-9).

The tank applies only to `dairy`, `market_swine`, and `breeding_swine` on
`liquid_nocrust` or `liquid_crust`. Section 4.1.3 says liquid methane is a
dairy and swine calculation; beef stays on Eq 10.23 in both the manual and
the code (CE-15 is that scope, not a code-vs-manual bug).

Missing daily temperature sets `tank_status = UNVERIFIED-input` and keeps
Eq 10.23. No county tank delta is reported. This run has no NASA or other
daily series for the Vermont/Delaware counties.

The 0.95 cap is in the manual and in `ManureStorageMath.cs:16`. It is not a
`holos_as_coded` fork. CE-13's earlier UNVERIFIED label is superseded by the
2026 print. Eq 4.1.3-18 (a separate liquid-VS stock after removal) is marked
in the print as not implemented in the code. Methane uses VSavailable from
Eq 4.1.3-6, which is implemented, so that note does not change CH4 here.

ghgsim takes the removal as a unitless fraction. The print's `× 1000`
converts Eq 4.5.3-3 totals stored per 1000 L. It is not applied a second time.

## Code-vs-manual forks

These change CH4 only when `holos_v4_liquid_tank` is selected.

| fork | source_correct | holos_as_coded |
|---|---|---|
| `HOLOS.STORAGE.year_reset` (CE-11) | Eq 4.1.3-5 carries VS into 1 January | `AnimalResultsServiceBase.cs:124-127` and `:881-884` drop the previous day on 1 January, including yesterday's removal. The temperature window is climate data and is not cleared. |
| `HOLOS.STORAGE.temp_window` | last 30 days, ending today | `date.AddDays(-30)` through today, both ends included (`ClimateData.cs:521`), which is 31 days |
| `HOLOS.STORAGE.cli_no_drain` (CE-01) | Eq 4.1.3-6 uses the supplied fraction | CLI never sets `AnimalType`. `NotSelected` is the enum default, so `IsImportedManure()` is true (`ManureApplicationViewItem.cs:148-150`; `FieldSystemInputConverter.cs:270-285`) and `ManureService.cs:240-242` skips the application |

## Tests

`tests/test_liquid_tank.py` checks the printed climate factor at 10 °C
(0.002108867), the 1 °C floor, a hand-expanded three-day tank, the 0.95 cap,
the CLI zero-removal fork, the 1 January reset, and the 31-day window.
Beef liquid and a run with no temperatures stay on Eq 10.23.

## Versioned files

`holos_forks_AN_v7.json`, `holos_params_canada_AN_v10.csv`,
`coefficient_trace_AN_v9.csv`, `docs/figures/fork_diagram_AN_v6`.
Earlier versions were not overwritten.

Every run that writes a fork diagram still logs `release_number` and
`commit_hash` (`ghgsim.core.provenance.run_identity`), citing Holzworth et al.
(2018) *Environ. Model. Softw.* 103:43–51.
