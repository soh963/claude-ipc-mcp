@echo off
echo Starting 4 Individual Monitor Windows...
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

echo Opening monitor windows...
echo.

REM Claude 모니터 (녹색)
start "Claude Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0A && python tools\monitor_instance.py claude"

REM 잠시 대기
timeout /t 1 /nobreak > nul

REM Gemini 모니터 (청록색)
start "Gemini Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0B && python tools\monitor_instance.py gemini"

REM 잠시 대기
timeout /t 1 /nobreak > nul

REM Codex 모니터 (빨간색)
start "Codex Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0C && python tools\monitor_instance.py codex"

REM 잠시 대기
timeout /t 1 /nobreak > nul

REM LM 모니터 (노란색)
start "LM Monitor" cmd /k "cd /d D:\claude-ipc-mcp && color 0E && python tools\monitor_instance.py lm"

echo.
echo ================================
echo 4 Monitor Windows Opened!
echo ================================
echo.
echo Each window shows messages for its instance:
echo   Claude - Green  (0A)
echo   Gemini - Cyan   (0B)
echo   Codex  - Red    (0C)
echo   LM     - Yellow (0E)
echo.
echo To send messages, use:
echo   python tools\ipc_manager.py send [from] [to] [message]
echo.
echo Example:
echo   python tools\ipc_manager.py send claude gemini "Hello!"
echo ================================
echo.
pause