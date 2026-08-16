@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "VENV_PY=%BACKEND%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [ERROR] backend\.venv is missing. Run setup_windows.bat first.
  pause
  exit /b 1
)
cd /d "%BACKEND%"
set "PYTHONPATH=%CD%"
echo ========================================================
echo   JurisTwin Sentinel - Finals Preflight v5.7
echo ========================================================
echo.
echo [1/2] Running automated regression suite...
"%VENV_PY%" -X utf8 -m pytest -q
if errorlevel 1 goto :fail
echo.
echo [2/2] Running championship control preflight...
"%VENV_PY%" -X utf8 "scripts\industry_preflight.py"
if errorlevel 1 goto :fail
echo.
echo [PASS] JurisTwin is finals-ready.
pause
exit /b 0
:fail
echo.
echo [FAIL] Preflight found an issue. Do not demo until it is resolved.
pause
exit /b 1
