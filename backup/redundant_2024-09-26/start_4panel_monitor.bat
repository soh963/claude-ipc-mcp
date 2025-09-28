@echo off
echo Starting Windows Terminal 4-Panel IPC Monitor...
echo.

cd /d D:\claude-ipc-mcp

REM 데이터베이스 초기화
echo Initializing database...
python tools\ipc_manager.py init

REM 인스턴스 등록
echo Registering instances...
python tools\ipc_manager.py register claude
python tools\ipc_manager.py register gemini
python tools\ipc_manager.py register codex
python tools\ipc_manager.py register lm
echo.

REM Windows Terminal 경로 확인
set WT_PATH=%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe

if exist "%WT_PATH%" (
    echo Starting Windows Terminal with 4 panel monitors...
    echo.
    echo Layout:
    echo +------------+------------+
    echo ^| CLAUDE     ^| GEMINI     ^|
    echo +------------+------------+
    echo ^| CODEX      ^| LM         ^|
    echo +------------+------------+
    echo.

    REM Windows Terminal 4분할 모니터링
    "%WT_PATH%" new-tab --title "IPC Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0A && cls && python tools\monitor_instance.py claude" ; split-pane -H cmd /k "cd /d D:\claude-ipc-mcp && color 0B && cls && python tools\monitor_instance.py gemini" ; split-pane -V -t 0 cmd /k "cd /d D:\claude-ipc-mcp && color 0C && cls && python tools\monitor_instance.py codex" ; split-pane -V -t 2 cmd /k "cd /d D:\claude-ipc-mcp && color 0E && cls && python tools\monitor_instance.py lm"

) else (
    echo Windows Terminal not found. Opening 4 separate windows...
    echo.

    REM 4개의 별도 창으로 실행
    start "Claude Monitor" /D "D:\claude-ipc-mcp" cmd /k "color 0A && python tools\monitor_instance.py claude"
    timeout /t 1 /nobreak > nul

    start "Gemini Monitor" /D "D:\claude-ipc-mcp" cmd /k "color 0B && python tools\monitor_instance.py gemini"
    timeout /t 1 /nobreak > nul

    start "Codex Monitor" /D "D:\claude-ipc-mcp" cmd /k "color 0C && python tools\monitor_instance.py codex"
    timeout /t 1 /nobreak > nul

    start "LM Monitor" /D "D:\claude-ipc-mcp" cmd /k "color 0E && python tools\monitor_instance.py lm"
)

echo.
echo ================================
echo 4-Panel Monitor Started!
echo ================================
echo.
echo Each panel shows messages for its instance:
echo   Claude - Green  (0A)
echo   Gemini - Cyan   (0B)
echo   Codex  - Red    (0C)
echo   LM     - Yellow (0E)
echo.
echo Send messages from another terminal:
echo   python tools\ipc_manager.py send [from] [to] [message]
echo ================================
echo.
pause