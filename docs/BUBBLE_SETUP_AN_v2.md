# Bubble PC setup log (AN_v2)

Date: 2026-11-03 (America/New_York). Machine: "Bubble", Windows 11, 20 cores, 31 GB RAM. Google Drive is mounted at G: (not used for code). There is no D: drive yet, so everything is on C:.

## Installed versions

| Tool | Version | Path / notes |
|---|---|---|
| Git | 2.55.0.windows.5 | C:\Program Files\Git (already present) |
| GitHub CLI | 2.103.3 | winget user scope, %LOCALAPPDATA%\Microsoft\WinGet\Packages\GitHub.cli_*\bin\gh.exe; logged in as gudaleon |
| Node.js | v26.13.0 (LTS) | C:\Program Files\nodejs |
| Python | 3.12.10 | %LOCALAPPDATA%\Programs\Python\Python312 |
| Docker Desktop | 4.98.0 (Engine 29.9.2) | engine running |
| winget | v1.29.380 | already present |

## ghgsim

- Clone: `C:\ghgsim`, main at `5a4510642d99921ae9f7483c506009c3fe56da69`
- Venv: `C:\ghgsim\.venv` (Python 3.12, about 418 MB)
- Install: `.venv\Scripts\python -m pip install -e ".[dev]"` (SALib is now in the `dev` and `test` extras)
- Tests: `.venv\Scripts\python -X utf8=0 -m pytest -q` gives **210 passed, 2 skipped** (UTF-8 mode off)

### Windows encoding fix (commit 0541f69)

Before the fix, `tests/test_coefficient_trace.py:79` failed on Windows with `UnicodeDecodeError` (cp1252, byte 0x9d). The cause was `read_text()` with no encoding. Commit `0541f69` adds `encoding="utf-8"` to every text `read_text()`, `Path.open()` and `open()` call in `src/`, `tests/` and `scripts/` (25 files; binary and tarfile opens are unchanged). It also adds `SALib>=1.4` to the `test` and `dev` extras.

## APSIM Next Generation

- Version: **2026.11.8142.0** (`Models.exe --version` prints `APSIM 2026.11.8142.0`; the ProductVersion of Models.exe and Models.dll is the same)
- Install path: `C:\Program Files\APSIM2026.11.8142.0`; CLI: `C:\Program Files\APSIM2026.11.8142.0\bin\Models.exe`
- Licence: General Use (Alex's account). Cite Holzworth et al. (2018) Environ. Model. Softw. 103:43-51, doi:10.1016/j.envsoft.2018.02.002, and state the release number and commit.
- Release: builds.apsim.info lists revision 8142 with releaseDate `2026-11-03T02:30:00` and issue **#11705**, "LinearInterpolationFunction: use Y values changed after the model is created" (https://github.com/APSIMInitiative/ApsimX/issues/11705).
- Source commit: the binary does not embed a commit hash. Build 8142 corresponds to ApsimX PR #11706, which fixes #11705, merge commit **`d1dca5e97aa4930a2015722362483b1216005037`** (merged 2026-11-03T02:22:58Z = 2026-11-02 21:22 ET). This mapping comes from the GitHub API, not from the binary.
- Headless test: copied `Examples\Maize.apsimx` to `C:\ghgsim-runs\apsim_test` and ran `Models.exe Maize.apsimx --csv`. It finished in about 4 s and wrote `Maize.db` and `Maize.Report.csv` (1,490 bytes). Weather comes from `%root%/Examples/WeatherFiles/Dalby.met` in the install folder.
## HESTIA Community Edition

- Source: https://gitlab.com/hestia-earth/hestia-community-edition, cloned to `C:\hestia-ce`
- Tag `v7.1.0`, commit `d63cd6b6394afd002737bebbf38fa7985ad00c8a`
- v7.1.0 has no `docker-compose.prod.yml`. It ships `docker-compose.example.yml` for published images, with `CE_VERSION` set in `.env`. Run with:
  `.env`: `CE_VERSION=7.1.0`, `MAX_AREA_SIZE=100000`, `AMQP_HEARTBEAT=30`
  `docker compose -f docker-compose.example.yml up -d`
- Upstream says the example compose is not a tested deployment and not recommended for production.
- Images:
  - hestiae/ce-api:7.1.0 `sha256:765c828cafc2292b637e909b9b30ff630b44b57958f4c3927fdd962c83b0366f`
  - hestiae/ce-runner:7.1.0 `sha256:ab7006e3bcd55fc83a11ef24b4748e8f863c7efef8d9355ed4ebb50b0a546471`
  - hestiae/ce-ui:7.1.0 `sha256:24884c249226e324b52f22ed153fb5fe022aad08d93f31b96d494bcaeb83fe96`
  - hestiae/hestia-caching-api:0.2.7 `sha256:4345ffdb772f0fd18a8aa46ac5478d0849c29eaf0180fb588d45c57949c98dce`
  - rabbitmq:4.1-management, postgres:17, dpage/pgadmin4, traefik:v3 (these upstream tags float)
- Check: http://localhost returns 200 and http://localhost/api/docs returns 200.
- Disk: Docker images 3.8 GB, containers 32 MB, volumes 57 MB, clone 495 MB.
- No Earth Engine `ee/credentials.json`, so geographic gap-filling is off.

## Blockers

- ~~APSIM~~: resolved. 2026.11.8142.0 is installed (see above).
- **HESTIA CE**: resolved. It runs under Docker (see above).
- **DayCent**: waiting on LandEngine (CSU) admin approval. Not installed.
- **No D: drive**: everything is on C:. To move later, re-clone and set `PIP_CACHE_DIR`.
