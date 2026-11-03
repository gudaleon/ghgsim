# Goal 4: Holos Route A - Implementation Status

**Version:** AN_v9  
**Date:** 2026-11-02  
**Branch:** cursor/goal4-phase-c-manure-storage-80da  
**Base:** cursor/goal4-phase-b-crops-soils-e537  
**Status:** Phase C liquid-manure tank (model version plus three code-vs-manual forks)

Does not overwrite `docs/HANDOFF_AN_v8.md`.

## Phase C

`HOLOS.CH4.liquid_tank` is a model-version option. Default remains IPCC 2006
Eq 10.23. `holos_v4_liquid_tank` is Pogue et al. 2026 Section 4.1.3
(Eq 4.1.3-1 through 4.1.3-10) for liquid dairy and swine. The opened C#
climate factor matches that print (T1 = 308.16 K, E = 19,347 cal/mol), so
the rate equation is not a bug fork.

`holos_as_coded` forks, active only on the tank option:

- `HOLOS.STORAGE.year_reset` (CE-11) — 1 January drops VS carryover
- `HOLOS.STORAGE.temp_window` — coded window is 31 days, print says 30
- `HOLOS.STORAGE.cli_no_drain` (CE-01) — CLI applications do not drain storage

The 0.95 emptying cap is in Eq 4.1.3-6 and in the code. It is not a bug fork.
Beef liquid stays on Eq 10.23 under both options (Sec 4.1.3 scope).

Missing daily temperature is `UNVERIFIED-input`. No county tank delta.

Narrative: `docs/PHASE_C_MANURE_STORAGE_AN_v1.md`.

## Still open

- County `holos_liang2020` and county liquid-tank runs need real weather
  (May–October P and PE; daily temperature). Do not invent either.
- ECCC 2022 NIR PDF for dairy Ym 5.6%
- Storage carbon and nitrogen pools beyond CH4 (Eq 4.1.3-13 onward) were
  not stepped in this phase
