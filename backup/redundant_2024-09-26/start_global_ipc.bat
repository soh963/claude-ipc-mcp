@echo off
echo ====================================
echo Starting Global IPC System...
echo ====================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.12 or higher
    pause
    exit /b 1
)

REM Set environment variables for this session
set CLAUDE_IPC_HOME=D:\claude-ipc-mcp
set CLAUDE_IPC_DB=%USERPROFILE%\.claude-ipc-data\messages.db
set CLAUDE_IPC_PORT=9876
set CLAUDE_IPC_ENABLED=true
set CLAUDE_IPC_AUTO_RESPONDER=true

REM Create necessary directories
if not exist "%USERPROFILE%\.claude-ipc-data" mkdir "%USERPROFILE%\.claude-ipc-data"
if not exist "%CLAUDE_IPC_HOME%\logs" mkdir "%CLAUDE_IPC_HOME%\logs"

REM Check if broker is already running
netstat -an | findstr :9876 >nul
if %errorlevel% == 0 (
    echo [INFO] IPC Broker already running on port 9876
) else (
    echo [1/4] Starting IPC Broker Server...
    start /B python "%CLAUDE_IPC_HOME%\src\claude_ipc_server.py" 2> "%CLAUDE_IPC_HOME%\logs\broker_error.log"
    timeout /t 3 /nobreak >nul
)

REM Start global auto-registrar
echo [2/4] Starting Auto-Registration System...
start /B python "%CLAUDE_IPC_HOME%\global_auto_register.py" 2> "%CLAUDE_IPC_HOME%\logs\registrar_error.log"

REM Wait for registrar to initialize
timeout /t 2 /nobreak >nul

REM Start monitoring
echo [3/4] Starting Status Monitor...
start cmd /k python "%CLAUDE_IPC_HOME%\global_status.py"

REM Run connection test
echo [4/4] Running Connection Test...
timeout /t 2 /nobreak >nul
python "%CLAUDE_IPC_HOME%\test_global_connection.py"

echo.
echo ====================================
echo Global IPC System Started!
echo ====================================
echo.
echo Available commands:
echo   ipc_status     - Check system status
echo   ipc_test       - Test connectivity
echo   ipc_monitor    - Open monitoring dashboard
echo.
echo Press any key to keep this window open...
pause >nul