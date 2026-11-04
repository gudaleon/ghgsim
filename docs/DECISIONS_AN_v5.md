# Decisions AN_v5 (2026-11-03) — US county run v2

1. Headline variant is `D_allocated`; `disclosed` and `reconstructed` reported alongside.
2. Census identities used only when exactly one term is withheld (exact, no estimation). Result: no cells recoverable (complementary suppression).
3. State remainder of each withheld series is allocated over withheld counties in proportion to the disclosed OPERATIONS WITH INVENTORY count; equal shares if no weight.
4. Residue-factor NA/"-" cells filled from the generic grain/bean/tuber rows of the same table; marked SUBSTITUTE in ipcc_params_AN_v10.csv.
5. Residue scope: 19 Census grain/pulse/tuber/peanut series. Excluded: hay, forage, silage, cotton, vegetables. FracRemove = 0, no burning.
6. Sheep, goats, horses, mules/asses: all excreted N to PRP with EF3PRP_SO in both versions. 2019 manure CH4 uses dry-lot EF (matching the 2006 "dry systems" basis). PRP (0.6 g/kg VS) left as a possible sensitivity.
7. Pullets use their own Nrate (2006 0.62, 2019 0.77).
8. 2019 run uses Table 10.13A VS and Table 10A.5 TAM; swine treated as finishing.
9. 2006 FracGas gaps (Table 10.22) verified absent; not filled; N conserved to soils.
10. F_OS and F_SOM remain gaps: no public county data; EPA uses DayCent.
11. No irrigation adjustment to FracLeach.
12. Map uses cb_2021 county boundaries so Connecticut counties match NASS (cb_2022 uses planning regions).
