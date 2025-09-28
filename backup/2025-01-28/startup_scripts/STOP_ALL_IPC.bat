@echo off
cls
echo ============================================
echo     STOPPING ALL IPC SERVICES
echo ============================================
echo.

REM ===== STEP 1: 모든 IPC 관련 프로세스 종료 =====
echo [1/3] Terminating all IPC processes...

REM 창 제목으로 프로세스 종료
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *IPC*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Monitor*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Auto-Responder*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Broker*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *auto_responder*" 2>nul

REM 특정 스크립트 이름으로도 종료
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *claude_ipc*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *enhanced_monitor*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *integrated_system*" 2>nul

timeout /t 2 /nobreak > nul
echo       Done - All processes terminated

REM ===== STEP 2: 세션 파일 정리 =====
echo.
echo [2/3] Cleaning up session files...
del /F /Q "%USERPROFILE%\.ipc-session" 2>nul
echo       Done - Session file removed

REM ===== STEP 3: 확인 =====
echo.
echo [3/3] Verifying shutdown...
netstat -an | findstr :9876 > nul
if %errorlevel%==0 (
    echo       WARNING: Port 9876 still in use
    echo       Force killing all Python processes...
    taskkill /F /IM python.exe 2>nul
    taskkill /F /IM pythonw.exe 2>nul
    timeout /t 2 /nobreak > nul
    echo       Done - All Python processes killed
) else (
    echo       Success - Port 9876 is free
)

echo.
echo ============================================
echo     ALL IPC SERVICES STOPPED
echo ============================================
echo.
pause