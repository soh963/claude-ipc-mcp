@echo off
echo Starting Fixed 4-Panel IPC Monitor...
echo.

cd /d D:\claude-ipc-mcp

REM Initialize database
echo Initializing database...
python tools\ipc_manager.py init

REM Register instances
echo Registering instances...
python tools\ipc_manager.py register claude
python tools\ipc_manager.py register gemini
python tools\ipc_manager.py register codex
python tools\ipc_manager.py register lm
echo.

REM Start Windows Terminal with 4 panels
echo Starting Windows Terminal with 4 panel monitors...
echo.
echo Layout:
echo +------------+------------+
echo ^| CLAUDE     ^| GEMINI     ^|
echo +------------+------------+
echo ^| CODEX      ^| LM         ^|
echo +------------+------------+
echo.

REM Windows Terminal command with fixed monitor
wt new-tab --title "IPC Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0A && python tools\fixed_monitor.py claude" ; split-pane -H cmd /k "cd /d D:\claude-ipc-mcp && color 0B && python tools\fixed_monitor.py gemini" ; split-pane -V -t 0 cmd /k "cd /d D:\claude-ipc-mcp && color 0C && python tools\fixed_monitor.py codex" ; split-pane -V -t 2 cmd /k "cd /d D:\claude-ipc-mcp && color 0E && python tools\fixed_monitor.py lm"

echo.
echo ================================
echo 4-Panel Monitor Started!
echo ================================
echo.
echo Send messages from another terminal:
echo   python tools\ipc_manager.py send [from] [to] [message]
echo.
echo Example:
echo   python tools\ipc_manager.py send claude gemini "Hello!"
echo   python tools\ipc_manager.py broadcast claude "Hello all!"
echo ================================
echo.
pause