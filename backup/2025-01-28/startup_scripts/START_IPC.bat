@echo off
cls
echo ============================================
echo     IPC SYSTEM ONE-CLICK LAUNCHER
echo ============================================
echo.

REM Kill existing Python processes (skip if causing issues)
echo [1/2] Preparing system...
REM taskkill /F /IM python.exe 2>nul >nul
ping localhost -n 2 >nul

REM Start the all-in-one system
echo [2/2] Starting IPC system...
echo.

REM Run the integrated launcher with error handling
python start_all_ipc.py 2>&1

REM Check error level
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo Error occurred! Error code: %errorlevel%
    echo.
    echo Possible solutions:
    echo 1. Check Python installation: python --version
    echo 2. Try running directly: python start_all_ipc.py
    echo 3. Check for missing modules
    echo ============================================
    echo.
)

pause