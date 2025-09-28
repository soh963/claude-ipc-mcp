@echo off
REM ================================================================
REM  UNIFIED IPC SYSTEM LAUNCHER
REM  모든 인스턴스 등록 + 자동응답 실행
REM ================================================================

echo ╔══════════════════════════════════════════════════════════╗
echo ║     UNIFIED IPC SYSTEM WITH AUTO-RESPONDERS             ║
echo ║                                                          ║
echo ║  Starting all instances with auto-responders...         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

cd /d D:\claude-ipc-mcp

REM Start the unified system
python start_all_instances_with_autoresponder.py

REM If error occurred
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error occurred while running the IPC system
    echo.
    pause
    exit /b %ERRORLEVEL%
)

REM Keep window open
pause