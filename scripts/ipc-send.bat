@echo off
REM ============================================================
REM IPC Send Command - Send message between instances
REM Usage: ipc-send [from] [to] "message"
REM ============================================================

if "%CLAUDE_IPC_HOME%"=="" (
    set CLAUDE_IPC_HOME=D:\claude-ipc-mcp
)

if "%1"=="" goto usage
if "%2"=="" goto usage
if "%3"=="" goto usage

python %CLAUDE_IPC_HOME%\tools\ipc_manager.py send %1 %2 %3
goto :eof

:usage
echo Usage: ipc-send [from] [to] "message"
echo Example: ipc-send claude gemini "Hello Gemini!"
echo.
echo Available instances:
python %CLAUDE_IPC_HOME%\tools\ipc_manager.py list 2>nul