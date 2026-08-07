@echo off
cd /d "%~dp0backend"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "from app.main import app; print('JurisTwin backend import OK')"
echo.
echo Setup complete. Run run_finals.bat next.
pause
