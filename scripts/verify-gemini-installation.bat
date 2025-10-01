@echo off
REM ========================================================================
REM  Gemini CLI Installation Verification Script
REM  Verifies that IPC TOML commands are correctly installed
REM  Platform: Windows
REM ========================================================================

setlocal enabledelayedexpansion

set "GEMINI_DIR=%USERPROFILE%\.gemini\commands\ipc"

echo.
echo ========================================
echo  Gemini CLI Installation Verification
echo ========================================
echo.

REM Check if directory exists
if exist "%GEMINI_DIR%" (
    echo [92m[PASS][0m Directory exists: %GEMINI_DIR%
) else (
    echo [91m[FAIL][0m Directory NOT found: %GEMINI_DIR%
    echo.
    echo Please run: scripts\install-gemini-cli.bat
    pause
    exit /b 1
)

echo.
echo Checking TOML files...
echo.

REM List expected files
set "FILES=setup.toml status.toml list.toml send.toml check.toml responder-start.toml responder-status.toml responder-stop.toml doctor.toml"
set "FOUND_COUNT=0"
set "MISSING_COUNT=0"

for %%f in (%FILES%) do (
    if exist "%GEMINI_DIR%\%%f" (
        echo [92m[PASS][0m %%f
        set /a FOUND_COUNT+=1
    ) else (
        echo [91m[FAIL][0m %%f NOT FOUND
        set /a MISSING_COUNT+=1
    )
)

echo.
echo ========================================
echo  Summary
echo ========================================
echo.
echo Found: %FOUND_COUNT%/9 files
echo Missing: %MISSING_COUNT% files
echo.

if %MISSING_COUNT% equ 0 (
    echo [92m[PASS][0m All 9 TOML files are installed correctly!
    echo.
    echo Next steps:
    echo 1. Restart Gemini CLI
    echo 2. Type / and look for /ipc: commands
    echo 3. Test with: /ipc:setup gemini-test
    echo.
) else (
    echo [91m[FAIL][0m Installation incomplete
    echo.
    echo Please run: scripts\install-gemini-cli.bat
    echo.
)

REM Check environment variables
echo.
echo Checking environment variables...
echo.

if defined IPC_CHAT (
    echo [92m[PASS][0m IPC_CHAT=%IPC_CHAT%
) else (
    echo [91m[FAIL][0m IPC_CHAT not set
)

if defined IPC_DB_PATH (
    echo [92m[PASS][0m IPC_DB_PATH=%IPC_DB_PATH%
) else (
    echo [91m[FAIL][0m IPC_DB_PATH not set
)

if defined IPC_HOST (
    echo [92m[PASS][0m IPC_HOST=%IPC_HOST%
) else (
    echo [91m[FAIL][0m IPC_HOST not set
)

if defined IPC_GLOBAL_PORT (
    echo [92m[PASS][0m IPC_GLOBAL_PORT=%IPC_GLOBAL_PORT%
) else (
    echo [91m[FAIL][0m IPC_GLOBAL_PORT not set
)

echo.
pause
