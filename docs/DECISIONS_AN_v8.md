# Decisions AN_v8 (2026-11-03) - Paper B figures and draft v4, HESTIA without Earth Engine

1. **Earth Engine dropped for HESTIA.** Alex decided not to set up a Google Earth Engine project or service account.
   HESTIA CE runs get their site inputs (soil, climate, region) from us, labelled "regional statistical data",
   so every model gets the same inputs. HESTIA's own geospatial lookups are not used. No `EARTH_ENGINE_*`
   settings and no key file.
2. **Figure script rewritten on PENV.** `scripts/make_paperB_figures_AN_v1.py` exists only on Bubble's
   uncommitted branch (Bubble is off), so it was written again from scratch. It reads only committed results files and
   writes `figures/*_AN_v1.png` plus `figures/paperB_figures_manifest_AN_v1.json` with input SHA-256
   hashes and check values. It refuses to overwrite. The check values match the draft text: county median
   +10.7%, 1,971 counties up and 1,104 down, 5th-95th percentile -26.7% to +32.9%; soil N2O 62.1, 57.5 and
   93.8 Mt; stylized-farm range -18.5% to +88.4%.
3. **Fig. 3a is a histogram, not a map.** There is no county boundary file in the repo, and geopandas is not a
   dependency, so panel a shows the distribution of county changes (`D_allocated` variant). It is labelled
   "county map pending". Swap in the map once a boundary file is added.
4. **Fig. 1 is a schematic** drawn from the caption text, with no data in it.
5. **Fig. 5:** the six countries are compared for 1990, 2005 and 2023 using `3. Agriculture`. The US bar is
   EPA 2025 vs 2024 editions, with CO2, CH4 and N2O summed, for 1990, 2005 and 2022.
6. **Draft v4** = v3 with only the five figure placeholders replaced by images (`docs/paperB/`). Built with
   pandoc 3.13 and --citeproc to `G:\My Drive\Papers_To_Publish\PaperB\PaperB_draft_AN_v4.docx`.
