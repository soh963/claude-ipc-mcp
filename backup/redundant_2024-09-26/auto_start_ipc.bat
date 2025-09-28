@echo off
REM ============================================================
REM Claude IPC MCP Auto-Start Script
REM Automatically starts IPC system on Windows startup
REM ============================================================

echo ========================================
echo   Claude IPC MCP System Starting...
echo ========================================
echo.

REM Set environment variables
set CLAUDE_IPC_HOME=D:\claude-ipc-mcp
set CLAUDE_IPC_DB=%USERPROFILE%\.claude-ipc-data\messages.db
set CLAUDE_IPC_ENABLED=true
set CLAUDE_IPC_AUTO_RESPONDER=true

REM Change to project directory
cd /d %CLAUDE_IPC_HOME%

REM Initialize database
echo [1/4] Initializing database...
python tools\ipc_manager.py init

REM Register all instances
echo [2/4] Registering instances...
python tools\ipc_manager.py register claude
python tools\ipc_manager.py register gemini
python tools\ipc_manager.py register codex
python tools\ipc_manager.py register codex-local
python tools\ipc_manager.py register lm

REM Start auto-responder in background
echo [3/4] Starting auto-responder...
start /B /MIN python tools\auto_responder.py

REM Optional: Start monitoring (comment out if not needed)
REM echo [4/4] Starting monitoring (optional)...
REM start /MIN cmd /c "python tools\fixed_monitor.py claude"

echo.
echo ========================================
echo   IPC System Started Successfully!
echo ========================================
echo.
echo Environment Variables Set:
echo   CLAUDE_IPC_HOME=%CLAUDE_IPC_HOME%
echo   CLAUDE_IPC_DB=%CLAUDE_IPC_DB%
echo   CLAUDE_IPC_ENABLED=%CLAUDE_IPC_ENABLED%
echo.
echo To start monitoring, type: ipc-monitor
echo To send message, type: ipc-send [from] [to] "message"
echo.
timeout /t 5 /nobreak > nul