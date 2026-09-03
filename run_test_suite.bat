@echo off
REM Test Suite Runner for Bot Tester (Windows)
REM Run predefined test suites and generate reports

setlocal enabledelayedexpansion

if not defined BOT_PATH set BOT_PATH=.
if not defined OUTPUT_FORMAT set OUTPUT_FORMAT=text
if not defined VERBOSE set VERBOSE=0

set TESTS_RUN=0
set TESTS_PASSED=0
set TESTS_FAILED=0

echo Bot Tester - Test Suite Runner (Windows)
echo Bot: %BOT_PATH%
echo ================================
echo.

REM Helper function to run a test
REM Note: This is simplified - full color support requires more complex batch logic

echo [1/7] Bot initialization ...
python src\cli_tester.py --bot %BOT_PATH% --info --output json >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PASS
    set /a TESTS_PASSED+=1
) else (
    echo FAIL
    set /a TESTS_FAILED+=1
)
set /a TESTS_RUN+=1

echo [2/7] Help command ...
python src\cli_tester.py --bot %BOT_PATH% --message "!help" --output json >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PASS
    set /a TESTS_PASSED+=1
) else (
    echo FAIL
    set /a TESTS_FAILED+=1
)
set /a TESTS_RUN+=1

echo [3/7] Admin permissions ...
python src\cli_tester.py --bot %BOT_PATH% --message "!status" --user-role admin --output json >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PASS
    set /a TESTS_PASSED+=1
) else (
    echo FAIL
    set /a TESTS_FAILED+=1
)
set /a TESTS_RUN+=1

echo [4/7] User permissions ...
python src\cli_tester.py --bot %BOT_PATH% --message "!status" --user-role user --output json >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PASS
    set /a TESTS_PASSED+=1
) else (
    echo FAIL
    set /a TESTS_FAILED+=1
)
set /a TESTS_RUN+=1

echo [5/7] High volume handling ^(10 messages^) ...
python src\cli_tester.py --bot %BOT_PATH% --high-volume "test" --count 10 --interval 0.05 --output json >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PASS
    set /a TESTS_PASSED+=1
) else (
    echo FAIL
    set /a TESTS_FAILED+=1
)
set /a TESTS_RUN+=1

echo [6/7] Duplicate message handling ...
python src\cli_tester.py --bot %BOT_PATH% --duplicate "test" --output json >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PASS
    set /a TESTS_PASSED+=1
) else (
    echo FAIL
    set /a TESTS_FAILED+=1
)
set /a TESTS_RUN+=1

echo [7/7] Error handling ^(409^) ...
python src\cli_tester.py --bot %BOT_PATH% --error "test" --error-code 409 --output json >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo PASS
    set /a TESTS_PASSED+=1
) else (
    echo FAIL
    set /a TESTS_FAILED+=1
)
set /a TESTS_RUN+=1

echo.
echo ================================
echo Results: %TESTS_PASSED% passed, %TESTS_FAILED% failed (total: %TESTS_RUN%)

if %TESTS_FAILED% EQU 0 (
    echo All tests passed!
    exit /b 0
) else (
    echo Some tests failed.
    exit /b 1
)

endlocal
