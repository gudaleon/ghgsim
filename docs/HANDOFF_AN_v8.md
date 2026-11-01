# Goal 4: Holos Route A - Implementation Status

**Version:** AN_v8  
**Date:** 2026-11-01  
**Branch:** cursor/goal4-phase2-holos-forks-e537  
**Base:** cursor/goal4-holos-route-a-c98e  
**Status:** Phase 3c complete (coefficient trace of every UNVERIFIED / SOURCE-TRACED Holos value)

Does not overwrite `docs/HANDOFF_AN_v7.md`.

---

## Phase 3c completed

Trace table: `data/coefficient_trace_AN_v1.csv`  
Narrative: `docs/COEFFICIENT_TRACE_AN_v1.md`  
Questions in that document are addressed to **Aaron (Holos team, AAFC)**.

Opened IPCC 2006/2019 Ch 10, ECCC 2024/2025 NIR Part 2, Little 2008, Sheppard 2015, Lactanet 2020 herds PDF, Benchaar 2001, Sommer 2000, Nennich 2005, ASAE/NRCS Ch. 4, 40 CFR JJ-2, EPA 2025 annex TOC. ECCC 2022 NIR PDF was not opened (archive interstitial).

**VERIFIED this phase (7 rows):** UE 85% grain switch and 0.04/0.02 pairing (IPCC 2006 Eq 10.24 notes pp. 10.42–10.43); ASH 8% example (same notes); Ym 6.3 and 7.0 diet rows that match IPCC 2019 Table 10.12 (Updated) p. 10.46.

**HOLOS-ONLY (29 rows):** include calf VS 0.0093, calf N 0.078 kg N/head/day, cover remaining 0.4/0.25, dairy Ym 5.6% point, beef B0 0.17 (claimed Table 10A-7 is swine; NA other cattle is 0.19), TAM 687/610/900/1200/86, cool pasture MCF 0.015 (IPCC cool is 0.01), US pasture 0.02 (IPCC 15°C is 0.015), US dairy Nrate 0.47 (NA Table 10.19 is 0.44).

Param CSVs were not rewritten. Operational UNVERIFIED / SOURCE-TRACED labels in `holos_params_*` stand until a later versioned CSV.

---

## Still open

- ECCC 2022 NIR Part 2 PDF (Holos citation year)
- NRC 2001 full tables for calf VS/N
- Personal communication cited as A. Alemu for beef TAM
