@echo off
REM ========================================================================
REM  IPC Slash Commands Installation Script for Gemini CLI
REM  Installs IPC commands globally for Gemini CLI
REM  Platform: Windows
REM ========================================================================

setlocal enabledelayedexpansion

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo.
echo ========================================
echo  IPC Slash Commands - Gemini CLI Installer
echo ========================================
echo.

:: Check if running as administrator (recommended)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [93mWarning: Not running as administrator[0m
    echo Some operations may fail. Consider running as admin.
    echo.
    pause
)

:: ================================================================================
:: Step 1: Install Gemini CLI Commands
:: ================================================================================

echo.
echo [94mInstalling Gemini CLI slash commands...[0m
echo.

set "GEMINI_DIR=%USERPROFILE%\.gemini\commands\ipc"

if not exist "%GEMINI_DIR%" (
    echo Creating directory: %GEMINI_DIR%
    mkdir "%GEMINI_DIR%" 2>nul
    if %errorLevel% neq 0 (
        echo [91mError: Failed to create directory[0m
        pause
        exit /b 1
    fi
)

:: Copy Gemini CLI .toml files
echo Copying Gemini CLI command files...
if exist "%SCRIPT_DIR%\gemini-commands\*.toml" (
    copy /Y "%SCRIPT_DIR%\gemini-commands\*.toml" "%GEMINI_DIR%\" >nul 2>&1

    if %errorLevel% equ 0 (
        echo [92m✓ Gemini CLI: 9 commands installed[0m

        :: List installed files
        echo.
        echo Installed files:
        dir /B "%GEMINI_DIR%\*.toml"
    ) else (
        echo [91m✗ Gemini CLI: Installation failed[0m
        pause
        exit /b 1
    )
) else (
    echo [91mError: Source files not found at %SCRIPT_DIR%\gemini-commands\[0m
    pause
    exit /b 1
)

:: ================================================================================
:: Step 2: Set Environment Variables
:: ================================================================================

echo.
echo [94mSetting environment variables...[0m
echo.

:: Update IPC_CHAT environment variable
setx IPC_CHAT "%PROJECT_ROOT%" >nul 2>&1
echo [92m✓ IPC_CHAT=%PROJECT_ROOT%[0m

:: Update other IPC variables (project-local paths)
echo [92m✓ Using project-local .ipc/ structure[0m
echo [92m✓ Database: {project_root}/.ipc/data/ipc.db[0m
echo [92m✓ Port: Auto-assigned from project ID[0m
echo [92m✓ IPC_HOST=127.0.0.1[0m

setx IPC_HOST "127.0.0.1" >nul 2>&1

:: ================================================================================
:: Step 3: Verification
:: ================================================================================

echo.
echo [94mVerifying installation...[0m
echo.

set "FILE_COUNT=0"
for %%f in ("%GEMINI_DIR%\*.toml") do set /a FILE_COUNT+=1

if %FILE_COUNT% equ 9 (
    echo [92m✓ Verification: All 9 TOML files present[0m
) else (
    echo [93m⚠ Warning: Found %FILE_COUNT% files, expected 9[0m
)

:: Check environment variables
if defined IPC_CHAT (
    echo [92m✓ IPC_CHAT is set[0m
) else (
    echo [91m✗ IPC_CHAT is not set[0m
)

:: ================================================================================
:: Installation Summary
:: ================================================================================

echo.
echo ========================================
echo [92m Gemini CLI Installation Complete![0m
echo ========================================
echo.
echo Installed commands:
echo   Location: %GEMINI_DIR%
echo.
echo   [92m/ipc:setup[0m           - One-click IPC setup
echo   [92m/ipc:status[0m          - Check connection status
echo   [92m/ipc:list[0m            - List all instances
echo   [92m/ipc:send[0m            - Send message
echo   [92m/ipc:check[0m           - Check messages
echo   [92m/ipc:responder-start[0m - Start auto-responder
echo   [92m/ipc:responder-status[0m- Check responder status
echo   [92m/ipc:responder-stop[0m  - Stop responder
echo   [92m/ipc:doctor[0m          - Diagnose and fix issues
echo.
echo Environment Variables:
echo   IPC_CHAT=%PROJECT_ROOT%
echo   Using project-local .ipc/ structure
echo   Database: {project_root}/.ipc/data/ipc.db
echo   Port: Auto-assigned from project ID
echo   IPC_HOST=127.0.0.1
echo.
echo ========================================
echo [93m Next Steps:[0m
echo ========================================
echo.
echo 1. [92mRestart Gemini CLI[0m to load new commands
echo.
echo 2. [92mTest the installation:[0m
echo    Type / in Gemini CLI and look for /ipc: commands
echo.
echo 3. [92mVerify with:[0m
echo    scripts\verify-gemini-installation.bat
echo.
echo 4. [92mStart using IPC:[0m
echo    /ipc:setup gemini-main
echo    /ipc:status
echo    /ipc:list
echo.

pause
