@echo off
REM IPC Global Command Wrapper with aliases for Codex CLI compatibility

REM Save current directory
set "ORIGINAL_DIR=%CD%"

REM Change to IPC project directory to avoid "project not initialized" errors
cd /d "D:\claude-ipc-mcp"

REM Check if first argument is an alias that needs translation
if "%1"=="list" (
    REM Translate 'ipc list' to 'ipc instances list --full' for Codex CLI
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" instances list --full
) else (
    REM Pass through all other commands as-is
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" %*
)

REM Restore original directory
cd /d "%ORIGINAL_DIR%"
