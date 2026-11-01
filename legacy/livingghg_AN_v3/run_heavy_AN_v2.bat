@echo off
REM livingghg v3 heavy run - generic Windows launcher (prepared for PENV-BSKX7Y3; NOT yet run).
REM Usage:  run_heavy_AN_v2.bat <INSTALL_ROOT> [trial]
REM   INSTALL_ROOT = folder containing the unzipped livingghg_AN_v3 (e.g. D:\lg\livingghg_AN_v3)
REM   trial        = optional; runs 2 states (VT,DE) with n=20 to check the install
REM Workers = %NUMBER_OF_PROCESSORS% - 2 (minimum 1). Results go to <INSTALL_ROOT>\results_AN_v3.
setlocal enabledelayedexpansion
if "%~1"=="" (echo Usage: %~nx0 INSTALL_ROOT [trial] & exit /b 1)
set "ROOT=%~1"
if not exist "%ROOT%\scripts\run_counties_AN_v3.py" (echo ERROR: %ROOT% is not a livingghg_AN_v3 folder & exit /b 1)
set /a WORKERS=%NUMBER_OF_PROCESSORS%-2
if !WORKERS! LSS 1 set WORKERS=1
set "MODE=full"
set "STATES=all"
set "N=1000"
set "TRIALFLAG="
if /i "%~2"=="trial" (set "MODE=trial" & set "STATES=VT,DE" & set "N=20" & set "TRIALFLAG=--trial")
echo Root=%ROOT%  cores=%NUMBER_OF_PROCESSORS%  workers=!WORKERS!  mode=!MODE!
cd /d "%ROOT%" || exit /b 1
where python >nul 2>nul || (echo ERROR: python not on PATH & exit /b 1)
if not exist ".venv\Scripts\python.exe" python -m venv .venv || exit /b 1
call ".venv\Scripts\activate.bat"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e .[test,sobol] || exit /b 1
python -m pytest -q tests || (echo TESTS FAILED - stopping & exit /b 1)
set "OUT=%ROOT%\results_AN_v3_!MODE!"
if not exist "!OUT!" mkdir "!OUT!"
python scripts\run_counties_AN_v3.py --states !STATES! --n !N! --workers !WORKERS! --out "!OUT!" !TRIALFLAG! > "!OUT!\log_counties_AN_v3.txt" 2>&1 || (echo county run failed, see log & exit /b 1)
python scripts\run_counties_AN_v3.py --states !STATES! --n 0 --workers !WORKERS! --withheld-fill prior_census --out "!OUT!\fork_F011_prior_census" !TRIALFLAG! >> "!OUT!\log_counties_AN_v3.txt" 2>&1
echo Done. Outputs in !OUT!
endlocal
