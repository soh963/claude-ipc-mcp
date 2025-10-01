@echo off
REM Comprehensive IPC Test Runner
REM This script runs all IPC tests and diagnostics

echo ============================================================
echo IPC COMPREHENSIVE TEST SUITE
echo ============================================================
echo.

REM Step 1: Fix duplicate brokers
echo [1/5] Checking for duplicate broker processes...
python tools\fix_broker_duplicates.py
if errorlevel 1 (
    echo Warning: Broker duplicate fix had issues
)
echo.

REM Step 2: Diagnose broker
echo [2/5] Running broker diagnostics...
python tools\diagnose_broker.py
if errorlevel 1 (
    echo Error: Broker diagnostics failed!
    echo Please check broker status and restart if needed.
    pause
    exit /b 1
)
echo.

REM Step 3: Run comprehensive tests
echo [3/5] Running comprehensive IPC tests...
python test\test_ipc_comprehensive.py
set TEST_RESULT=%errorlevel%
echo.

REM Step 4: Run existing pytest tests
echo [4/5] Running pytest tests...
pytest test\ -v --tb=short
set PYTEST_RESULT=%errorlevel%
echo.

REM Step 5: Summary
echo [5/5] Test Summary
echo ============================================================
if %TEST_RESULT%==0 (
    echo Comprehensive tests: PASS
) else (
    echo Comprehensive tests: FAIL
)

if %PYTEST_RESULT%==0 (
    echo Pytest tests: PASS
) else (
    echo Pytest tests: FAIL
)
echo ============================================================

if %TEST_RESULT%==0 if %PYTEST_RESULT%==0 (
    echo.
    echo All tests passed!
    exit /b 0
) else (
    echo.
    echo Some tests failed. Please review the output above.
    pause
    exit /b 1
)