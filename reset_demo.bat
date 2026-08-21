@echo off
cd /d %~dp0
python reset_demo.py
if errorlevel 1 py reset_demo.py
pause
