@echo off
REM livingghg v2 - single batch for Bubble PC (Windows 11). Requires livingghg_AN_v2 unzipped at G:\lg\livingghg_AN_v2
REM Approve ONE command:  G:\lg\livingghg_AN_v2\run_bubble_AN_v1.bat
setlocal
set LG=G:\lg
set PKG=%LG%\livingghg_AN_v2
set OUT=%LG%\results\v2
set LOG=%OUT%\run_bubble_AN_v1.log
if not exist "%OUT%" mkdir "%OUT%"
if exist "%OUT%\counties_VT_AN_v2.csv" (echo Results already exist in %OUT% - refusing to overwrite & exit /b 1)
echo [%date% %time%] start > "%LOG%"
if not exist "%LG%\venv\Scripts\python.exe" python -m venv "%LG%\venv" >> "%LOG%" 2>&1 || goto :fail
call "%LG%\venv\Scripts\activate.bat"
python -m pip install --upgrade pip >> "%LOG%" 2>&1
python -m pip install -e "%PKG%[test,sobol]" >> "%LOG%" 2>&1 || goto :fail
cd /d "%PKG%"
python -m pytest -q -p no:cacheprovider tests >> "%LOG%" 2>&1 || goto :fail
python scripts\run_counties.py --states all --n 10000 --workers 18 --out "%OUT%" >> "%LOG%" 2>&1 || goto :fail
python scripts\sobol.py --states all --n 4096 --workers 18 --out "%OUT%" >> "%LOG%" 2>&1 || goto :fail
echo [%date% %time%] done >> "%LOG%"
echo DONE - results in %OUT%
exit /b 0
:fail
echo [%date% %time%] FAILED - see %LOG% >> "%LOG%"
echo FAILED - see %LOG%
exit /b 1
