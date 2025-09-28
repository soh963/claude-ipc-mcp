@echo off
cls
echo ============================================
echo     IPC MANAGER - Smart Control
echo ============================================
echo.
echo Select mode:
echo   1. Integrated Mode (Auto everything)
echo   2. Manual Mode (Manual registration)
echo   3. Stop All Services
echo.
choice /C 123 /M "Select option"

if %errorlevel%==1 (
    echo Starting Integrated Mode...
    python ipc_manager.py integrated
) else if %errorlevel%==2 (
    echo Starting Manual Mode...
    python ipc_manager.py manual
) else if %errorlevel%==3 (
    echo Stopping all services...
    python ipc_manager.py stop
    echo Done!
)

pause