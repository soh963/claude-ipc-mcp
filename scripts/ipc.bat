@echo off
REM IPC Global Command Wrapper with aliases for Codex CLI compatibility

REM Save current directory
set "ORIGINAL_DIR=%CD%"

REM Change to IPC project directory to avoid "project not initialized" errors
cd /d "D:\claude-ipc-mcp"

REM Check if first argument is an alias that needs translation
if "%1"=="list" (
    REM Translate 'ipc list' to 'ipc instances list --full'
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" instances list --full
) else if "%1"=="start-broker" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" broker start
) else if "%1"=="stop-broker" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" broker stop
) else if "%1"=="broker-status" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" broker status
) else if "%1"=="delete-instance" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" instances delete %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="reset-instances" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" instances reset
) else if "%1"=="clear-messages" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" messages clear --force
) else if "%1"=="show-session" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" session
) else if "%1"=="clear-session" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" session clear
) else if "%1"=="start-responder" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" responder start %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="start-all-responders" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" responder start-all %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="stop-responder" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" responder stop %2 %3 %4 %5 %6 %7 %8 %9
) else if "%1"=="stop-all-responders" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" responder stop-all
) else if "%1"=="responder-status" (
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" responder status %2 %3 %4 %5 %6 %7 %8 %9
) else (
    REM Pass through all other commands as-is
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" %*
)

REM Restore original directory
cd /d "%ORIGINAL_DIR%"
