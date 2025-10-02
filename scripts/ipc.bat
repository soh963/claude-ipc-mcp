@echo off
REM IPC Global Command Wrapper with aliases for Codex CLI compatibility
REM IMPORTANT: Stay in current directory to use project-local .ipc settings

REM Use uv run if available, fallback to python
where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=uv run python"
) else (
    set "PYTHON_CMD=python"
)

REM Set IPC command path
set "IPC_CMD=D:\claude-ipc-mcp\tools\ipc_global_command.py"

REM Auto-initialize if .ipc doesn't exist
if not exist ".ipc" (
    echo Project not initialized. Running 'ipc init'...
    %PYTHON_CMD% "%IPC_CMD%" init
)

REM Check if first argument is an alias that needs translation
if "%1"=="list" (
    REM Translate 'ipc list' to 'ipc instances list --full'
    %PYTHON_CMD% "%IPC_CMD%" instances list --full
) else if "%1"=="start-broker" (
    %PYTHON_CMD% "%IPC_CMD%" broker start
) else if "%1"=="stop-broker" (
    %PYTHON_CMD% "%IPC_CMD%" broker stop
) else if "%1"=="broker-status" (
    %PYTHON_CMD% "%IPC_CMD%" broker status
) else if "%1"=="delete-instance" (
    %PYTHON_CMD% "%IPC_CMD%" instances delete %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="reset-instances" (
    %PYTHON_CMD% "%IPC_CMD%" instances reset
) else if "%1"=="clear-messages" (
    %PYTHON_CMD% "%IPC_CMD%" messages clear --force
) else if "%1"=="show-session" (
    %PYTHON_CMD% "%IPC_CMD%" session
) else if "%1"=="clear-session" (
    %PYTHON_CMD% "%IPC_CMD%" session clear
) else if "%1"=="start-responder" (
    %PYTHON_CMD% "%IPC_CMD%" responder start %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="start-all-responders" (
    %PYTHON_CMD% "%IPC_CMD%" responder start-all %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="stop-responder" (
    %PYTHON_CMD% "%IPC_CMD%" responder stop %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="stop-all-responders" (
    %PYTHON_CMD% "%IPC_CMD%" responder stop-all
) else if "%1"=="responder-status" (
    %PYTHON_CMD% "%IPC_CMD%" responder status %2 %3 %4 %5 %6 %7 %8 %9
) else (
    REM Pass through all other commands as-is
    %PYTHON_CMD% "%IPC_CMD%" %*
)
