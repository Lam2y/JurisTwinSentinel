@echo off
setlocal EnableExtensions
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
for /f "delims=" %%P in ('.venv\Scripts\python.exe scripts\choose_port.py') do set "JURISTWIN_PORT=%%P"
if not defined JURISTWIN_PORT (
    echo [ERROR] Could not select a free local port.
    pause
    exit /b 1
)

set "JURISTWIN_BASE=http://127.0.0.1:%JURISTWIN_PORT%"

echo ================================================
echo   JurisTwin Sentinel - Championship v5.4
echo ================================================
echo Backend:   %JURISTWIN_BASE%
echo Finals UI: %JURISTWIN_BASE%/finals
echo Swagger:   %JURISTWIN_BASE%/docs
echo.
if not "%JURISTWIN_PORT%"=="8000" echo [INFO] Port 8000 was busy. JurisTwin safely selected port %JURISTWIN_PORT%.
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
