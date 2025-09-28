@echo off
cls
echo ============================================
echo     INTEGRATED IPC SYSTEM
echo     Complete Solution with All Features
echo ============================================
echo.

REM ===== STEP 1: 기존 프로세스 모두 종료 =====
echo [1/5] Cleaning up existing processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *IPC*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Monitor*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Broker*" 2>nul
timeout /t 2 /nobreak > nul
echo       Done - All old processes terminated

REM ===== STEP 2: DB 초기화 (선택사항) =====
echo.
echo [2/5] Database initialization...
choice /C YN /M "Do you want to clear the database"
if %errorlevel%==1 (
    python -c "import sqlite3; from pathlib import Path; db=sqlite3.connect(Path.home()/'.claude-ipc-data'/'messages.db'); c=db.cursor(); c.execute('DELETE FROM messages'); c.execute('DELETE FROM instances'); c.execute('DELETE FROM sessions'); c.execute('DELETE FROM name_history'); db.commit(); print('       Database cleared!')"
) else (
    echo       Keeping existing database
)

REM ===== STEP 3: 통합 시스템 시작 =====
echo.
echo [3/5] Starting Integrated System...
start "IPC Integrated System" /MIN python start_integrated_system.py

timeout /t 3 /nobreak > nul

REM ===== STEP 4: 모니터링 시작 =====
echo.
echo [4/5] Starting Enhanced Monitor...
start "IPC Enhanced Monitor" python enhanced_monitor.py

REM ===== STEP 5: 종료 핸들러 설정 =====
echo.
echo [5/5] Setting up cleanup handler...
echo.

echo ============================================
echo     SYSTEM READY!
echo ============================================
echo.
echo Press Ctrl+C or close this window to stop all services
echo.

REM ===== 종료 시 자동 정리 =====
:WAIT_LOOP
timeout /t 60 /nobreak > nul
goto WAIT_LOOP

:CLEANUP
echo.
echo Shutting down all IPC services...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *IPC*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Monitor*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Broker*" 2>nul
echo All services stopped.
exit