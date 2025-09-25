@echo off
echo Starting 4 Separate Monitor Windows...
echo.

cd /d D:\claude-ipc-mcp

echo Initializing database...
python tools\ipc_manager.py init

echo Registering instances...
python tools\ipc_manager.py register claude
python tools\ipc_manager.py register gemini
python tools\ipc_manager.py register codex
python tools\ipc_manager.py register lm
echo.

echo Starting 4 monitor windows...
echo.

REM Start 4 separate windows
start "Claude Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0A && python tools\fixed_monitor.py claude"
timeout /t 1 /nobreak > nul

start "Gemini Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0B && python tools\fixed_monitor.py gemini"
timeout /t 1 /nobreak > nul

start "Codex Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0C && python tools\fixed_monitor.py codex"
timeout /t 1 /nobreak > nul

start "LM Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0E && python tools\fixed_monitor.py lm"

echo.
echo ================================
echo 4 Monitor Windows Started!
echo ================================
echo.
echo Arrange the windows manually in a 2x2 grid.
echo.
echo Send messages from this terminal:
echo   python tools\ipc_manager.py send [from] [to] [message]
echo.
echo Examples:
echo   python tools\ipc_manager.py send claude gemini "Hello Gemini!"
echo   python tools\ipc_manager.py send gemini claude "Hi Claude!"
echo   python tools\ipc_manager.py broadcast claude "Hello everyone!"
echo ================================
echo.
pause