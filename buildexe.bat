@echo off
cd /d c:\Users\miles\OneDrive\Documents\interactive-tester
echo Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist
echo Building new executable...
.\.venv\Scripts\python.exe -m PyInstaller build_gui.spec
pause