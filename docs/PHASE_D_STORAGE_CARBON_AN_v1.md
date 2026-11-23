# Phase D: manure-storage carbon (AN_v1)

Carbon in stored manure, from the opened Holos V4 algorithm document.
This file does not overwrite `docs/PHASE_C_MANURE_STORAGE_AN_v1.md`.
No GPL source was copied.

## What was opened

- Pogue et al. (2026) *Holos Version 4.0 Algorithm Documentation*, print PDF
  on holos-aafc/Holos at `913bc8c`
  (`Pogue et al 2026_Printversion_Holos_V4.0_Algorithm_Document_ENGLISH_FINAL.pdf`),
  **Section 4.1.3.1 through 4.1.3.3**, pages 163–165
  (Eq 4.1.3-13 through 4.1.3-18).
- The carbon methods in the public C#, read only, at commit `53401a022f6c`
  (2026-11-13): `AnimalResultsServiceBase.cs:1301-1367`.

## Equations that match the print

| equation | print | code |
|---|---|---|
| 4.1.3-13 | `C_manureCH4 = CH4_manure × 12/16` | `CalculateCarbonLostAsMethaneDuringManagement` returns `CH4 * (12.0/16.0)` (`:1337`) |
| 4.1.3-14 | `C_flow = (C_excretion + C_bedding) − C_manureCH4` | `:1352`, argument documented as "Amount of C excreted" |
| 4.1.3-15 | `C(t) = C(t−1) + C_flow(t)` | `:1367`, when nothing was removed |
| 4.1.3-16 | sum of group stocks on a day | caller-side sum |

`C_excretion` and `C_bedding` are inputs. They are not calculated in this phase.
No county carbon stock is reported.

## Fork (`HOLOS.STORAGE.carbon_removal`)

Eq 4.1.3-15 accumulates the stock. Eq 4.1.3-17, on the day after a removal,
writes `Total_C(t) = Total_C(t−1) × (1 − fraction)`. Both assign the day-t
stock. Eq 4.1.3-6 in the same section resolves that pair for volatile solids:
today's inflow is added in full, and only the carryover is multiplied by
`(1 − fraction)`. `source_correct` uses that resolution for carbon. The
fraction is the ratio Eq 4.1.3-17 writes. Its bounds, 0 to 0.95, are the
note under Eq 4.1.3-6.

`holos_as_coded` does not reduce the carbon stock.
`CalculateAmountOfCarbonInStorageOnCurrentDay` (`:1363-1367`) is
`C(t) = C_flow(t) + C(t−1)`. The comment at `:1129-1134` says carbon is
intended to follow the net-of-removals pattern. The comment at `:1156-1158`
says the daily storage advance still carries volume only.

## Not in this phase

- **Eq 4.1.3-18.** The print says this separate liquid-VS stock after removal
  is not implemented in the Holos V4 code. Methane already reduces
  `VSavailable` through Eq 4.1.3-6 (Phase C). A second VS stock is not added.
- **Pasture zero.** The same C# method sets storage carbon to 0 when housing
  is pasture (`:1320-1326`). Section 4.1.3 does not say that. It is not
  applied here.
- **Section 4.2** (manure nitrogen and housing N2O) is the next block of the
  print. It is not Eq 4.1.3-13 onward, and it is not stepped.

## Tests

`tests/test_storage_carbon.py` checks 12/16, plain accumulation, the
carryover-only removal (6 then 12.6 against 15), the 0.95 cap, a negative
flow left unfloored, the group sum, and the fork default.
