@echo off
REM IPC Global Command Wrapper with aliases for Codex CLI compatibility

REM Check if first argument is an alias that needs translation
if "%1"=="list" (
    REM Translate 'ipc list' to 'ipc instances list --full' for Codex CLI
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" instances list --full
) else (
    REM Pass through all other commands as-is
    python "D:\claude-ipc-mcp\tools\ipc_global_command.py" %*
)
