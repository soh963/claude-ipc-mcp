@echo off
REM IPC Wrapper for Easy Terminal Usage
REM Usage: ipc-wrapper <command> [args...]

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Usage: ipc-wrapper ^<command^> [args...]
    echo.
    echo Available commands:
    echo   status              - Check IPC status
    echo   register ^<name^>     - Register as instance
    echo   list                - List all instances
    echo   send ^<to^> ^<msg^>     - Send message
    echo   ask ^<to^> ^<msg^>      - Send and wait for response
    echo   check               - Check messages
    echo   responder-start ^<name^> - Start auto-responder
    echo   responder-stop ^<name^>  - Stop auto-responder
    echo   responder-status ^<name^> - Check responder status
    echo   doctor              - Run diagnostics
    echo.
    echo Examples:
    echo   ipc-wrapper status
    echo   ipc-wrapper register codex-main
    echo   ipc-wrapper send gemini "Hello"
    echo   ipc-wrapper ask gemini "What's your status?"
    exit /b 0
)

set CMD=%~1
shift

REM Get project root
for %%i in ("%~dp0..") do set PROJECT_ROOT=%%~fi

cd /d "%PROJECT_ROOT%"

REM Execute commands
if "%CMD%"=="status" (
    uv run python tools/ipc_global_command.py status
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="register" (
    if "%~1"=="" (
        echo Error: Instance name required
        echo Usage: ipc-wrapper register ^<name^>
        exit /b 1
    )
    uv run python tools/ipc_global_command.py register %~1
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="list" (
    uv run python tools/ipc_global_command.py instances list --full
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="send" (
    if "%~2"=="" (
        echo Error: Target and message required
        echo Usage: ipc-wrapper send ^<to^> ^<message^>
        exit /b 1
    )
    uv run python tools/ipc_global_command.py chat --to %~1 %~2
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="ask" (
    if "%~2"=="" (
        echo Error: Target and message required
        echo Usage: ipc-wrapper ask ^<to^> ^<message^>
        exit /b 1
    )
    uv run python tools/ipc_global_command.py ask --to %~1 %~2 --timeout 10
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="check" (
    uv run python tools/ipc_global_command.py messages list
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="responder-start" (
    if "%~1"=="" (
        echo Error: Instance name required
        echo Usage: ipc-wrapper responder-start ^<name^>
        exit /b 1
    )
    uv run python tools/ipc_global_command.py responder start %~1 --policy smart --detach
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="responder-stop" (
    if "%~1"=="" (
        echo Error: Instance name required
        echo Usage: ipc-wrapper responder-stop ^<name^>
        exit /b 1
    )
    uv run python tools/ipc_global_command.py responder stop %~1
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="responder-status" (
    if "%~1"=="" (
        echo Error: Instance name required
        echo Usage: ipc-wrapper responder-status ^<name^>
        exit /b 1
    )
    uv run python tools/ipc_global_command.py responder status %~1
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="doctor" (
    uv run python tools/ipc_doctor.py --auto-fix
    exit /b %ERRORLEVEL%
)

echo Unknown command: %CMD%
echo Run 'ipc-wrapper' without arguments to see usage
exit /b 1
