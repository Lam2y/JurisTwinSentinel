@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "VENV_PY=%BACKEND%\.venv\Scripts\python.exe"

if not exist "%BACKEND%\app\main.py" (
    echo [ERROR] Could not find backend\app\main.py
    echo Keep run_finals.bat inside the JurisTwin project root.
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo [ERROR] backend\.venv is missing or incomplete.
    echo Run setup_windows.bat once before the finals.
    pause
    exit /b 1
)

cd /d "%BACKEND%"
"%VENV_PY%" "scripts\finals_launcher.py"
if errorlevel 1 (
    echo.
    echo [ERROR] JurisTwin stopped unexpectedly.
    echo Run run_preflight.bat for a diagnostic report.
    pause
)
