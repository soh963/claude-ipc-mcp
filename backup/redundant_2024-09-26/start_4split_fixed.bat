@echo off
echo Starting Windows Terminal 4-split IPC Interactive Clients...
echo.

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
    echo Starting Windows Terminal with 4 panes...
    echo.

    REM Windows Terminal 2x2 분할 (가로 2, 세로 2)
    REM 레이아웃:
    REM [claude] [gemini]
    REM [codex ] [lm    ]
    "%WT_PATH%" -w 0 nt --title "IPC 2x2" cmd /k "cd /d D:\claude-ipc-mcp && color 0A && echo. && echo === CLAUDE INSTANCE === && echo. && python tools\interactive_client.py claude" ; ^
    split-pane -H -s 0.5 cmd /k "cd /d D:\claude-ipc-mcp && color 0B && echo. && echo === GEMINI INSTANCE === && echo. && python tools\interactive_client.py gemini" ; ^
    split-pane -V -t 0 -s 0.5 cmd /k "cd /d D:\claude-ipc-mcp && color 0C && echo. && echo === CODEX INSTANCE === && echo. && python tools\interactive_client.py codex" ; ^
    move-focus -t 1 ; ^
    split-pane -V -s 0.5 cmd /k "cd /d D:\claude-ipc-mcp && color 0E && echo. && echo === LM INSTANCE === && echo. && python tools\interactive_client.py lm"

) else (
    echo Windows Terminal not found. Opening 4 separate windows...
    echo.

    REM 4개의 별도 창으로 실행
    start "Claude Instance" /D "D:\claude-ipc-mcp" cmd /k "color 0A && echo. && echo === CLAUDE INSTANCE === && echo. && python tools\interactive_client.py claude"
    timeout /t 1 /nobreak > nul

    start "Gemini Instance" /D "D:\claude-ipc-mcp" cmd /k "color 0B && echo. && echo === GEMINI INSTANCE === && echo. && python tools\interactive_client.py gemini"
    timeout /t 1 /nobreak > nul

    start "Codex Instance" /D "D:\claude-ipc-mcp" cmd /k "color 0C && echo. && echo === CODEX INSTANCE === && echo. && python tools\interactive_client.py codex"
    timeout /t 1 /nobreak > nul

    start "LM Instance" /D "D:\claude-ipc-mcp" cmd /k "color 0E && echo. && echo === LM INSTANCE === && echo. && python tools\interactive_client.py lm"
)

echo.
echo ================================
echo Interactive clients started!
echo.
echo Available commands in each terminal:
echo   Register this instance as [name]   (Auto-registered if parameter given)
echo   Send message to [name]: [message]
echo   Check messages
echo   List instances
echo   Help
echo ================================
echo.
pause