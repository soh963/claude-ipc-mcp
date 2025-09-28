@echo off
echo ====================================
echo Starting Auto-Responder System
echo ====================================
echo.
echo This solves the problem:
echo "메시지 보내기는 되지만 메시지를 캐치하고 답변하는것이 안되는 상황"
echo (Messages can be sent but catching and responding doesn't work)
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Set environment variables
set CLAUDE_IPC_HOME=D:\claude-ipc-mcp
set CLAUDE_IPC_DB=%USERPROFILE%\.claude-ipc-data\messages.db
set PYTHONPATH=%CLAUDE_IPC_HOME%;%PYTHONPATH%

REM Check if broker is running
echo [1/3] Checking IPC Broker...
netstat -an | findstr :9876 >nul
if %errorlevel% == 0 (
    echo   ✓ IPC Broker is running
) else (
    echo   × IPC Broker not running
    echo   Starting broker...
    start /B python "%CLAUDE_IPC_HOME%\src\claude_ipc_server.py" 2>nul
    timeout /t 3 /nobreak >nul
    echo   ✓ IPC Broker started
)

REM Start the unified auto-responder system
echo.
echo [2/3] Starting Auto-Responder System...
echo   This will enable bi-directional communication
echo   between all AI CLI instances
echo.

REM IMPORTANT: The original start_all_auto_responders.py causes infinite loops!
REM Instead, use one of the safe alternatives:

echo WARNING: start_all_auto_responders.py can cause infinite loops!
echo Using safe alternative instead...
echo.

REM Option 1: Use safe_auto_responder.py if available
if exist "%CLAUDE_IPC_HOME%\safe_auto_responder.py" (
    echo Running safe_auto_responder.py with loop prevention...
    python "%CLAUDE_IPC_HOME%\safe_auto_responder.py"
    goto :end
)

REM Option 2: Use simple_responder.py for single instance
if exist "%CLAUDE_IPC_HOME%\simple_responder.py" (
    echo Running simple_responder.py for safe operation...
    python "%CLAUDE_IPC_HOME%\simple_responder.py"
    goto :end
)

REM Option 3: Run with --test flag to limit operation
echo Running with test mode to prevent infinite loops...
python "%CLAUDE_IPC_HOME%\start_all_auto_responders.py" --test

:end

echo.
echo [3/3] Auto-Responder System Stopped
echo.
pause