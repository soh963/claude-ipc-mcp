@echo off
echo ====================================
echo Starting SAFE Auto-Responder System
echo ====================================
echo.
echo This prevents infinite loops by:
echo - Using message deduplication
echo - Limiting response frequency
echo - Filtering auto-response patterns
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

REM Start SAFE responder instead
echo.
echo [2/3] Starting SAFE Responder System...
echo   This uses loop prevention mechanisms
echo.

REM Use the safe responder scripts instead
if exist "%CLAUDE_IPC_HOME%\safe_auto_responder.py" (
    python "%CLAUDE_IPC_HOME%\safe_auto_responder.py"
) else if exist "%CLAUDE_IPC_HOME%\simple_responder.py" (
    echo Running simple responder with single instance...
    python "%CLAUDE_IPC_HOME%\simple_responder.py"
) else (
    echo [ERROR] No safe responder script found!
    echo Creating minimal safe responder...
    python "%CLAUDE_IPC_HOME%\tools\auto_responder.py" --safe-mode
)

echo.
echo [3/3] Safe Auto-Responder System Stopped
echo.
pause