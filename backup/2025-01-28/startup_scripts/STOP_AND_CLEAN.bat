@echo off
echo === IPC System Complete Stop and Clean ===
echo.

echo [1/4] Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul

echo [2/4] Stopping IPC Server...
taskkill /F /FI "WINDOWTITLE eq IPC Server*" 2>nul

echo [3/4] Stopping all monitors...
taskkill /F /FI "WINDOWTITLE eq *Monitor*" 2>nul

echo [4/4] Stopping auto-responders...
taskkill /F /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul

echo.
echo === All processes stopped ===
echo.
pause