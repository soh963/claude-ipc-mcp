@echo off
cls
echo ============================================
echo     ULTIMATE IPC SYSTEM
echo     One-Click Complete Solution
echo ============================================
echo.

echo [+] Starting Ultimate System...
echo.

python start_ultimate_system.py

if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo ERROR DETECTED! Trying safe mode...
    echo ============================================
    echo.
    python start_simple.py
)

echo.
pause