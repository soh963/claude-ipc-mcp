@echo off
REM Test Codex CLI IPC commands

echo ========================================
echo Testing Codex CLI IPC Commands
echo ========================================
echo.

REM Test 1: Status command
echo [1/3] Testing /ipc:status command...
uv run python tools\ipc_global_command.py status
if %ERRORLEVEL% EQU 0 (
    echo    ✓ Status command works
) else (
    echo    ✗ Status command failed
)
echo.

REM Test 2: List command
echo [2/3] Testing /ipc:list command...
uv run python tools\ipc_global_command.py instances list --full
if %ERRORLEVEL% EQU 0 (
    echo    ✓ List command works
) else (
    echo    ✗ List command failed
)
echo.

REM Test 3: Doctor command
echo [3/3] Testing /ipc:doctor command...
uv run python tools\ipc_doctor.py --auto-fix
if %ERRORLEVEL% EQU 0 (
    echo    ✓ Doctor command works
) else (
    echo    ✗ Doctor command failed
)
echo.

echo ========================================
echo All Codex CLI commands tested
echo ========================================
echo.
echo To use these commands in Codex CLI:
echo 1. Copy config\codex-config.toml to %%USERPROFILE%%\.codex\config.toml
echo 2. Update IPC_CHAT path in [environment] section
echo 3. Restart Codex CLI
echo 4. Use commands like: /ipc:status
echo.

pause
