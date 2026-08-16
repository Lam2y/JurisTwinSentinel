@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "PYTHON_CMD="
set "VENV_PY=%BACKEND%\.venv\Scripts\python.exe"

echo ========================================================
echo   JurisTwin Sentinel - Windows First-Time Setup v5.7
echo ========================================================
echo.

if not exist "%BACKEND%\app\main.py" (
    echo [ERROR] Could not find backend\app\main.py
    echo Keep this BAT file in the project root.
    pause
    exit /b 1
)

cd /d "%BACKEND%"
echo [1/7] Working directory: %CD%
echo [2/7] Finding a complete Python installation...

where py >nul 2>&1
if not errorlevel 1 (
    rem Prefer the versions used most often for the finals build, but remain compatible with a
    rem machine that only has a newer standard CPython installation.
    for %%V in (3.12 3.11 3.10 3.13 3.14) do (
        if not defined PYTHON_CMD (
            py -%%V -c "import sys,venv; print(sys.executable)" >nul 2>&1
            if not errorlevel 1 set "PYTHON_CMD=py -%%V"
        )
    )
    if not defined PYTHON_CMD (
        py -3 -c "import sys,venv; print(sys.executable)" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -3"
    )
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys,venv; assert sys.version_info >= (3,10)" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo.
    echo [ERROR] No standard Python 3.10+ installation with venv was found.
    echo The Microsoft Store alias or an application-private Python is not sufficient.
    echo Install 64-bit CPython 3.12 from python.org when possible, then rerun this setup.
    pause
    exit /b 1
)

echo Selected Python command: %PYTHON_CMD%
%PYTHON_CMD% -c "import sys; print('Python executable:',sys.executable); print('Python version:',sys.version.split()[0])"
if errorlevel 1 goto :fail

if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import sys,venv; print(sys.executable)" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Existing backend\.venv is incomplete. Rebuilding it safely...
        rmdir /s /q ".venv"
    )
)

if not exist "%VENV_PY%" (
    echo [3/7] Creating backend\.venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :fail
) else (
    echo [3/7] Existing virtual environment is usable.
)

echo [4/7] Installing/verifying dependencies inside the virtual environment...
"%VENV_PY%" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :fail
"%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :fail

echo [5/7] Generating local signing/security secrets if needed...
"%VENV_PY%" "%ROOT%tools\bootstrap_env.py"
if errorlevel 1 goto :fail

set "PYTHONPATH=%CD%"
echo [6/7] Verifying the backend and warming the local AI stack...
"%VENV_PY%" -X utf8 -c "import os,sys,time; print('Venv Python:',sys.executable); t=time.perf_counter(); from app.main import app; from app.services.policy_ml import get_policy_ai; m=get_policy_ai().model_card(); print('Backend import OK'); print('AI ready: domain Macro-F1',m['held_out_development_benchmark']['domain_macro_f1'],'stance Macro-F1',m['held_out_development_benchmark']['stance_macro_f1']); print('Warm-up seconds:',round(time.perf_counter()-t,2))"
if errorlevel 1 goto :fail

echo [7/7] Running a compact finals control check...
"%VENV_PY%" -X utf8 "scripts\industry_preflight.py" --ci
if errorlevel 1 goto :fail

echo.
echo ========================================================
echo   SETUP COMPLETE - READY FOR run_finals.bat
echo ========================================================
echo Tip: use run_preflight.bat the night before and morning of finals.
pause
exit /b 0

:fail
echo.
echo [ERROR] JurisTwin setup failed.
echo Working directory: %CD%
echo Use a standard CPython installation and rerun setup_windows.bat.
pause
exit /b 1
