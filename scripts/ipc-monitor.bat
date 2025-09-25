@echo off
REM ============================================================
REM IPC Monitoring Command - Activates 4 terminal monitoring
REM Usage: ipc-monitor or just type "모니터링" in terminal
REM ============================================================

echo ========================================
echo   IPC 모니터링 시작 (Starting IPC Monitoring)
echo ========================================
echo.

REM Check environment variable
if "%CLAUDE_IPC_HOME%"=="" (
    set CLAUDE_IPC_HOME=D:\claude-ipc-mcp
)

cd /d %CLAUDE_IPC_HOME%

REM Initialize if needed
python tools\ipc_manager.py init 2>nul

REM Register instances
python tools\ipc_manager.py register claude 2>nul
python tools\ipc_manager.py register gemini 2>nul
python tools\ipc_manager.py register codex 2>nul
python tools\ipc_manager.py register codex-local 2>nul
python tools\ipc_manager.py register lm 2>nul

echo Starting 4-panel monitoring...
echo.

REM Start 4 monitor windows
start "Claude Monitor" cmd /k "cd /d %CLAUDE_IPC_HOME% && color 0A && python tools\fixed_monitor.py claude"
timeout /t 1 /nobreak > nul

start "Gemini Monitor" cmd /k "cd /d %CLAUDE_IPC_HOME% && color 0B && python tools\fixed_monitor.py gemini"
timeout /t 1 /nobreak > nul

start "Codex Monitor" cmd /k "cd /d %CLAUDE_IPC_HOME% && color 0C && python tools\fixed_monitor.py codex"
timeout /t 1 /nobreak > nul

start "LM Monitor" cmd /k "cd /d %CLAUDE_IPC_HOME% && color 0E && python tools\fixed_monitor.py lm"

echo.
echo ================================
echo ✅ 4 Monitor Windows Started!
echo ================================
echo.
echo Arrange the windows in a 2x2 grid for best viewing.
echo.
echo Commands:
echo   ipc-send [from] [to] "message"    - Send message
echo   ipc-check [instance]               - Check messages
echo   ipc-list                           - List instances
echo.
pause