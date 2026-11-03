# Bubble PC setup log (AN_v1)

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
- Install: `.venv\Scripts\python -m pip install -e ".[dev]"`, plus `pip install SALib` (the `sobol` extra; `tests/test_services.py` imports it but the `dev` extra does not include it)
- Tests: `$env:PYTHONUTF8='1'; .venv\Scripts\python -m pytest -q` gives **210 passed, 2 skipped**

### Known Windows issue (code bug, not patched here)

Without UTF-8 mode, `tests/test_coefficient_trace.py::test_questions_address_aaron_holos_team_not_unverified_surname` fails with `UnicodeDecodeError` (cp1252, byte 0x9d) at `tests/test_coefficient_trace.py:79`. `Path.read_text()` is called without `encoding="utf-8"`. Fix: pass `encoding="utf-8"`, and add SALib to the `dev`/`test` extras.

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

- **APSIM Next Gen**: no winget package. It needs a General Use licence registration at https://registration.apsim.info (current release 2026.02.7980.0) and Alex has to submit the form. Record the release number and commit after install.
- **DayCent**: waiting on LandEngine (CSU) admin approval. Not installed.
- **No D: drive**: everything is on C:. To move later, re-clone and set `PIP_CACHE_DIR`.