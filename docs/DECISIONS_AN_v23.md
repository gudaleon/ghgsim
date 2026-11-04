# Decisions AN_v23 (APSIM crop consistency check)

- **D23.1 Install.** APSIM Next Gen 2026.11.8142.0 (commit d1dca5e, ApsimX PR #11706) run portable without admin: official build-8142 package contents in D:\APSIM, .NET 10 user runtime (dotnet-install) in D:\dotnet10, win-x64 e_sqlite3 from NuGet SQLitePCLRaw.lib.e_sqlite3 2.1.11. The Windows installer needs admin and a system-wide .NET 10. Models.dll SHA-256 is in the run manifest.
- **D23.2 Soil.** No soil parameters invented: APSoil No. 900 Black Vertosol (Norwin, Darling Downs, Qld; CSIRO / GRDC 2011), as shipped in Examples/Maize.apsimx.
- **D23.3 Weather.** No shipped example pairs a documented soil with US warm-temperate-moist weather. Main run = example as shipped (AU_Dalby.met); climate-matched sensitivity = shipped NZ_Hamilton.met on the same soil. 0 N controls for fertiliser-induced EF. Years 1990/91-1999/2000 (Jul-Jun).
- **D23.4 Scope.** APSIM = direct soil N2O only (no NH3 volatilisation/indirect); compared with ghgsim and HESTIA direct terms. GLEAM has no crop module (n/a). Consistency check, not validation.
- **D23.5 Figure.** Fig. 6 = scripts/make_paperB_figures_AN_v6.py -> figures/fig6_four_way_AN_v1.png.
