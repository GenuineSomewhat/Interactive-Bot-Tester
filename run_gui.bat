@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python src\interactive_gui.py
pause
