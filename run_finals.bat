@echo off
setlocal
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"

if not exist "%BACKEND%\app\main.py" (
    echo [ERROR] Could not find backend\app\main.py
    echo Keep run_finals.bat inside the JurisTwin project root.
    pause
    exit /b 1
)

cd /d "%BACKEND%"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] backend\.venv is missing.
    echo Run setup_windows.bat first.
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%"

echo ================================================
echo   JurisTwin Sentinel - Championship v5
echo ================================================
echo Backend:   http://127.0.0.1:8000
echo Finals UI: http://127.0.0.1:8000/finals
echo Swagger:   http://127.0.0.1:8000/docs
echo.
echo Starting local decision-integrity runtime...
echo The browser will open automatically when JurisTwin is ready.
echo.

start "" /b ".venv\Scripts\python.exe" "scripts\open_finals_when_ready.py"
".venv\Scripts\python.exe" run.py

if errorlevel 1 (
    echo.
    echo [ERROR] Backend stopped with an error.
    pause
)
