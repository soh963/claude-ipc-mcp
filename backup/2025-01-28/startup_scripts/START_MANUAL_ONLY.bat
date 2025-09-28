@echo off
cls
echo ============================================
echo     MANUAL IPC SYSTEM
echo     수동 등록 전용 모드
echo ============================================
echo.

REM ===== STEP 1: 기존 프로세스 모두 종료 =====
echo [1/4] Cleaning up existing processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *IPC*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Monitor*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Broker*" 2>nul
timeout /t 2 /nobreak > nul
echo       Done - All old processes terminated

REM ===== STEP 2: 세션 파일 정리 =====
echo.
echo [2/4] Cleaning session files...
del /F /Q "%USERPROFILE%\.ipc-session" 2>nul
echo       Done - Session file removed

REM ===== STEP 3: 브로커만 시작 =====
echo.
echo [3/4] Starting Broker Server only...
start "IPC Broker" python src/claude_ipc_server.py

timeout /t 2 /nobreak > nul

REM ===== STEP 4: 모니터만 시작 (등록 없음) =====
echo.
echo [4/4] Starting Monitor (view only)...
start "IPC Monitor" python enhanced_monitor.py

echo.
echo ============================================
echo     MANUAL MODE READY!
echo ============================================
echo.
echo Now manually register instances in separate terminals:
echo   python tools/ipc_register.py claude
echo   python tools/ipc_register.py gemini
echo   python tools/ipc_register.py [instance_name]
echo.
echo Press Ctrl+C or close this window to stop all services
echo ============================================
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
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Broker*" 2>nul
echo All services stopped.
exit