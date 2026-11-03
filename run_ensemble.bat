@echo off
REM Windows batch file for running ghgsim county ensemble
REM Usage: run_ensemble.bat [trial|full] [workers]

setlocal

set MODE=%1
set WORKERS=%2

if "%MODE%"=="" set MODE=trial
if "%WORKERS%"=="" (
    REM Default: CPU cores - 2
    set WORKERS=auto
)

echo ========================================
echo ghgsim County Ensemble Runner
echo ========================================
echo Mode: %MODE%
echo Workers: %WORKERS%
echo ========================================

if "%MODE%"=="trial" (
    echo Running TRIAL mode: VT + DE counties only
    python -m ghgsim.api.cli ensemble --mode trial --workers %WORKERS%
) else if "%MODE%"=="full" (
    echo WARNING: Running FULL US county ensemble
    echo This may take hours or days to complete.
    echo Press Ctrl+C to cancel, or
    pause
    python -m ghgsim.api.cli ensemble --mode full --workers %WORKERS%
) else (
    echo ERROR: Invalid mode '%MODE%'
    echo Usage: run_ensemble.bat [trial^|full] [workers]
    exit /b 1
)

echo.
echo ========================================
echo Ensemble run complete
echo ========================================

endlocal
