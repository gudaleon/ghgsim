# Benchmark datasets (AN_v1)

Two open N2O benchmark datasets. They are downloaded to Bubble under `C:\ghgsim-data\benchmarks\` and the data are not committed to the repo. The manifest is `data/benchmarks_manifest_AN_v1.json` and the fetch script is `scripts/fetch_benchmarks_AN_v1.py` (standard library only).

```powershell
python scripts/fetch_benchmarks_AN_v1.py --dest C:\ghgsim-data\benchmarks                    # download + verify SHA-256
python scripts/fetch_benchmarks_AN_v1.py --dest C:\ghgsim-data\benchmarks --write-manifest   # rebuild manifest
```

## 1. Global N2O Database v1.0 (EDI edi.877.1) - NOT DOWNLOADED

- Dorich, C.D., R.T. Conant, and D. Wang. 2021. Global N2O Database version 1.0 ver 1. Environmental Data Initiative. doi:10.6073/pasta/09a95cf44cd7835db002b0089ed5ffc3. CC BY 4.0.
- Status (2026-11-03): EDI's PASTA API refuses anonymous reads. Both `package/metadata/eml/edi/877/1` and `package/data/eml/edi/877/1` return HTTP 403 "Public Access ... not authorized". The portal's metadata and data views redirect to a login page with a Cloudflare Turnstile check.
- To fix: download the package by hand (logged in) from https://portal.edirepository.org/nis/mapbrowse?packageid=edi.877.1 into `C:\ghgsim-data\benchmarks\global_n2o_edi877v1\`, then rerun with `--write-manifest`. The script hashes any local files it finds there.

## 2. GRACEnet (Ag Data Commons, Figshare article 24660216, version 1) - DOWNLOADED, BUT NOT THE EXPECTED DATA

- DOI 10.15482/USDA.ADC/1235557, CC0, published on Figshare 2024-02-08. Cite Del Grosso et al. 2013 J. Environ. Qual. 42:1274-1280, doi:10.2134/jeq2013.03.0097.
- This article version holds **5 files, 37.2 MB**, not the expected 33 CSVs / ~378 MB: two GRACEnet brochures (PDF), `DET_GRACEnet_REAP_0.zip` (data-entry templates), `GRACEnet-NUOnet_DD_0.csv` (data dictionary), and `natres.zip` (contains `natres.xlsx`, `NatRes_citation.xlsx` and a locations shapefile zip).
- All SHA-256 values are recorded in the manifest, and Figshare MD5s match.
- The 33-CSV GRACEnet measurement tables are not in this article. They are probably in another Ag Data Commons record. The linked REAP record (doi:10.15482/USDA.ADC/1372394, Figshare 25119227) has no files through the API. Still open.