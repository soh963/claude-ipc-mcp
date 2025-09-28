@echo off
echo Starting Windows Terminal 4-Split Monitor...
echo.

cd /d D:\claude-ipc-mcp

REM 데이터베이스 초기화
python tools\ipc_manager.py init
python tools\ipc_manager.py register claude
python tools\ipc_manager.py register gemini
python tools\ipc_manager.py register codex
python tools\ipc_manager.py register lm

REM Windows Terminal 실행 (한 줄 명령으로)
wt -w 0 nt -d D:\claude-ipc-mcp cmd /c "color 0A && python tools\monitor_instance.py claude" `; split-pane -H -d D:\claude-ipc-mcp cmd /c "color 0B && python tools\monitor_instance.py gemini" `; split-pane -V -t 0 -d D:\claude-ipc-mcp cmd /c "color 0C && python tools\monitor_instance.py codex" `; move-focus -t 1 `; split-pane -V -d D:\claude-ipc-mcp cmd /c "color 0E && python tools\monitor_instance.py lm"

echo.
echo Windows Terminal opened with 4-panel layout!
echo.
pause