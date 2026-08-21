@echo off
setlocal
cd /d %~dp0backend
if not exist .venv (
  py -m venv .venv
  call .venv\Scripts\activate
  python -m pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
python -m pytest -q
if errorlevel 1 (
  echo.
  echo PREFLIGHT FAILED - do not start the finals demo until the failing test is fixed.
  pause
  exit /b 1
)
echo.
echo PREFLIGHT PASSED - all automated safety and workflow checks passed.
pause
