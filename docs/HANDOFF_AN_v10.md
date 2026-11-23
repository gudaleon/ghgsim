# Goal 4: Holos Route A - Implementation Status

**Version:** AN_v10  
**Date:** 2026-11-22  
**Branch:** cursor/phase-d-storage-carbon-ba38  
**Base:** main  
**Status:** Phase D storage carbon (Eq 4.1.3-13 through 4.1.3-17, one code-vs-manual fork)

Does not overwrite `docs/HANDOFF_AN_v9.md`.

## Phase D

`HOLOS.STORAGE.carbon_removal` is a `holos_as_coded` fork. Default is the
print. `C_manureCH4 = CH4 × 12/16` (Eq 4.1.3-13) and the daily flow
`C_excretion + C_bedding − C_manureCH4` (Eq 4.1.3-14) match the opened C#
and are not forks.

`source_correct` adds today's carbon inflow in full and multiplies yesterday's
stock by `(1 − fraction)` (Eq 4.1.3-15 and Eq 4.1.3-17, read the way
Eq 4.1.3-6 treats volatile solids). The opened C# at `53401a022f6c`
(`AnimalResultsServiceBase.cs:1363-1367`) does not reduce the carbon stock
when manure is removed. That is the fork.

`C_excretion` and `C_bedding` are inputs. No county carbon stock.

Narrative: `docs/PHASE_D_STORAGE_CARBON_AN_v1.md`.

## Still open

- County `holos_liang2020` and county liquid-tank runs still need the weather
  for the counties being compared. May–October P and PE for US counties are
  in `data/county_p_pe_may_oct_AN_v2.csv`. Daily temperature for the
  Vermont/Delaware set used by the tank comparison is not in this repo.
  Do not invent either. Most US counties are dry under Hargreaves, and
  `FR_Topo` is still unavailable, so a national Liang total is not reported.
- ECCC 2022 NIR PDF for dairy Ym 5.6%
- Eq 4.1.3-18 (separate liquid-VS stock after removal) is printed as not
  implemented in the Holos code. Not added.
- Section 4.2 manure nitrogen and housing N2O were not stepped
- The Ontario overwintering-maize rerun in FINDINGS_AN_v12 is still an
  author decision. The daily APSIM outputs it needs are not in this checkout
  (`*.csv.gz` is gitignored). No Paper B v21 was made.
