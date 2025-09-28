@echo off
echo Starting 4-Panel IPC Monitor...
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
echo Starting Windows Terminal...
echo.

REM Try to run Windows Terminal directly
wt new-tab --title "IPC Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0A && python tools\fixed_monitor.py claude" ; split-pane -H cmd /k "cd /d D:\claude-ipc-mcp && color 0B && python tools\fixed_monitor.py gemini" ; split-pane -V -t 0 cmd /k "cd /d D:\claude-ipc-mcp && color 0C && python tools\fixed_monitor.py codex" ; split-pane -V -t 2 cmd /k "cd /d D:\claude-ipc-mcp && color 0E && python tools\fixed_monitor.py lm"

echo.
echo If Windows Terminal didn't open, run these commands manually in 4 separate terminals:
echo   python tools\fixed_monitor.py claude
echo   python tools\fixed_monitor.py gemini
echo   python tools\fixed_monitor.py codex
echo   python tools\fixed_monitor.py lm
echo.
pause