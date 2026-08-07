@echo off
cd /d "%~dp0backend"
call .venv\Scripts\activate
start "" http://127.0.0.1:8000/finals
python run.py
