@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "PYTHON_CMD="

echo ================================================
echo   JurisTwin Sentinel - Windows First-Time Setup
echo ================================================
echo.

if not exist "%BACKEND%\app\main.py" (
    echo [ERROR] Could not find backend\app\main.py
    echo Expected project root: %ROOT%
    echo Do not move this BAT file outside the project folder.
    pause
    exit /b 1
)

cd /d "%BACKEND%"
echo [1/6] Working directory: %CD%

echo [2/6] Finding a full Python installation...

rem Prefer the official Windows Python Launcher. pgAdmin ships its own
rem private Python runtime, which intentionally may not contain venv.
where py >nul 2>&1
if not errorlevel 1 (
    py -3.12 -c "import sys,venv; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.12"
    if defined PYTHON_CMD goto :python_found

    py -3.11 -c "import sys,venv; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.11"
    if defined PYTHON_CMD goto :python_found

    py -3.10 -c "import sys,venv; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.10"
    if defined PYTHON_CMD goto :python_found

    py -3 -c "import sys,venv; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
    if defined PYTHON_CMD goto :python_found
)

rem Fall back to PATH only if that Python actually provides venv.
where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys,venv" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
    if defined PYTHON_CMD goto :python_found
)

echo.
echo [ERROR] No normal Python installation with the 'venv' module was found.
echo.
echo Your current 'python' may be pgAdmin's private runtime:
where python 2>nul
echo.
echo Install standard 64-bit Python 3.11 or 3.12 from python.org.
echo IMPORTANT: tick "Add python.exe to PATH" during installation.
echo Then close this window, open a new Command Prompt, and run setup_windows.bat again.
echo.
pause
exit /b 1

:python_found
echo Selected Python command: %PYTHON_CMD%
%PYTHON_CMD% -c "import sys; print('Python executable:', sys.executable); print('Python version:', sys.version.split()[0])"
if errorlevel 1 goto :fail

if not exist ".venv\Scripts\python.exe" (
    echo [3/6] Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create backend\.venv
        goto :fail
    )
) else (
    echo [3/6] Virtual environment already exists.
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Could not activate backend\.venv
    goto :fail
)

echo [4/6] Installing backend dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

set "PYTHONPATH=%CD%"
echo [5/6] Generating local security secrets if needed...
python "%ROOT%tools\bootstrap_env.py"
if errorlevel 1 goto :fail

echo [6/6] Verifying JurisTwin backend import...
python -c "import os,sys; print('Venv Python:', sys.executable); print('Working directory:', os.getcwd()); from app.main import app; print('JurisTwin backend import OK')"
if errorlevel 1 goto :fail

echo.
echo ================================================
echo   SETUP COMPLETE
echo   Next: run_finals.bat
echo ================================================
pause
exit /b 0

:fail
echo.
echo [ERROR] JurisTwin setup failed.
echo Working directory: %CD%
echo.
echo Python commands visible on this PC:
where py 2>nul
where python 2>nul
pause
exit /b 1
