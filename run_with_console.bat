@echo off
REM Run the Interactive Bot Tester with console output visible
echo Starting Interactive Bot Tester with console...
echo.
echo Debug output will appear below when you load a bot:
echo.
cd /d "%~dp0dist"
"Interactive Bot Tester.exe"
pause
