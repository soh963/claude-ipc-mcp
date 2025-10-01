@echo off
REM ========================================================================
REM  IPC Slash Commands Installation Script for All AI CLIs
REM  Installs IPC commands globally for Claude Code, Gemini CLI, and Codex CLI
REM  Platform: Windows
REM ========================================================================

setlocal enabledelayedexpansion

:: Configuration
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

:: Color definitions (using PowerShell for colored output)
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "NC=[0m"

echo.
echo ========================================
echo  IPC Slash Commands - All CLIs Installer
echo ========================================
echo.

:: Check if running as administrator (recommended)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo %YELLOW%Warning: Not running as administrator%NC%
    echo Some operations may fail. Consider running as admin.
    echo.
    pause
)

:: ================================================================================
:: Step 1: Install Claude Code Commands
:: ================================================================================

echo.
echo %BLUE%[1/3] Installing Claude Code slash commands...%NC%
echo.

set "CLAUDE_DIR=%USERPROFILE%\.claude\commands\ipc"

if not exist "%CLAUDE_DIR%" (
    echo Creating directory: %CLAUDE_DIR%
    mkdir "%CLAUDE_DIR%" 2>nul
)

:: Copy Claude Code .md files
echo Copying Claude Code command files...
copy /Y "%SCRIPT_DIR%\..\scripts\ipc\*.md" "%CLAUDE_DIR%\" >nul 2>&1

if %errorLevel% equ 0 (
    echo %GREEN%✓ Claude Code: 9 commands installed%NC%
) else (
    echo %RED%✗ Claude Code: Installation failed%NC%
)

:: ================================================================================
:: Step 2: Install Gemini CLI Commands
:: ================================================================================

echo.
echo %BLUE%[2/3] Installing Gemini CLI slash commands...%NC%
echo.

set "GEMINI_DIR=%USERPROFILE%\.gemini\commands\ipc"

if not exist "%GEMINI_DIR%" (
    echo Creating directory: %GEMINI_DIR%
    mkdir "%GEMINI_DIR%" 2>nul
)

:: Copy Gemini CLI .toml files
echo Copying Gemini CLI command files...
copy /Y "%SCRIPT_DIR%\gemini-commands\*.toml" "%GEMINI_DIR%\" >nul 2>&1

if %errorLevel% equ 0 (
    echo %GREEN%✓ Gemini CLI: 9 commands installed%NC%
) else (
    echo %RED%✗ Gemini CLI: Installation failed%NC%
)

:: ================================================================================
:: Step 3: Install Codex CLI Commands
:: ================================================================================

echo.
echo %BLUE%[3/3] Installing Codex CLI configuration...%NC%
echo.

set "CODEX_DIR=%USERPROFILE%\.codex"
set "CODEX_CONFIG=%CODEX_DIR%\config.toml"
set "CODEX_AGENTS=%CODEX_DIR%\AGENTS.md"

if not exist "%CODEX_DIR%" (
    echo Creating directory: %CODEX_DIR%
    mkdir "%CODEX_DIR%" 2>nul
)

:: Check if config.toml already exists
if exist "%CODEX_CONFIG%" (
    echo %YELLOW%Warning: config.toml already exists%NC%
    echo Creating backup: config.toml.backup
    copy /Y "%CODEX_CONFIG%" "%CODEX_CONFIG%.backup" >nul 2>&1

    echo.
    echo Please manually merge the IPC configuration from:
    echo   %SCRIPT_DIR%\codex-config\config.toml
    echo Into your existing config.toml at:
    echo   %CODEX_CONFIG%
    echo.
) else (
    echo Copying Codex config.toml...
    copy /Y "%SCRIPT_DIR%\codex-config\config.toml" "%CODEX_CONFIG%" >nul 2>&1

    if %errorLevel% equ 0 (
        echo %GREEN%✓ Codex CLI: config.toml installed%NC%
    ) else (
        echo %RED%✗ Codex CLI: config.toml installation failed%NC%
    )
)

:: Copy AGENTS.md
echo Copying Codex AGENTS.md...
copy /Y "%SCRIPT_DIR%\codex-config\AGENTS.md" "%CODEX_AGENTS%" >nul 2>&1

if %errorLevel% equ 0 (
    echo %GREEN%✓ Codex CLI: AGENTS.md installed%NC%
) else (
    echo %RED%✗ Codex CLI: AGENTS.md installation failed%NC%
)

:: ================================================================================
:: Step 4: Set Environment Variables
:: ================================================================================

echo.
echo %BLUE%[4/4] Setting environment variables...%NC%
echo.

:: Update IPC_CHAT environment variable
setx IPC_CHAT "%PROJECT_ROOT%" >nul 2>&1
echo %GREEN%✓ IPC_CHAT=%PROJECT_ROOT%%NC%

:: Update other IPC variables
setx IPC_DB_PATH "%USERPROFILE%\.claude-ipc-data\messages.db" >nul 2>&1
echo %GREEN%✓ IPC_DB_PATH=%USERPROFILE%\.claude-ipc-data\messages.db%NC%

setx IPC_HOST "127.0.0.1" >nul 2>&1
echo %GREEN%✓ IPC_HOST=127.0.0.1%NC%

setx IPC_GLOBAL_PORT "9876" >nul 2>&1
echo %GREEN%✓ IPC_GLOBAL_PORT=9876%NC%

:: ================================================================================
:: Installation Summary
:: ================================================================================

echo.
echo ========================================
echo %GREEN% Installation Complete!%NC%
echo ========================================
echo.
echo Installed commands:
echo.
echo %BLUE%Claude Code:%NC%
echo   Location: %CLAUDE_DIR%
echo   Commands: /ipc:setup, /ipc:status, /ipc:list, /ipc:send,
echo             /ipc:check, /ipc:responder-*, /ipc:doctor
echo.
echo %BLUE%Gemini CLI:%NC%
echo   Location: %GEMINI_DIR%
echo   Commands: Same as above (TOML format)
echo.
echo %BLUE%Codex CLI:%NC%
echo   Location: %CODEX_DIR%
echo   Files: config.toml, AGENTS.md
echo.
echo %BLUE%Environment Variables:%NC%
echo   IPC_CHAT=%PROJECT_ROOT%
echo   IPC_DB_PATH=%USERPROFILE%\.claude-ipc-data\messages.db
echo   IPC_HOST=127.0.0.1
echo   IPC_GLOBAL_PORT=9876
echo.
echo ========================================
echo %YELLOW% Next Steps:%NC%
echo ========================================
echo.
echo 1. %GREEN%Restart all AI CLIs%NC% to load new commands
echo.
echo 2. %GREEN%Test installation:%NC%
echo    - Claude Code: Type / and look for /ipc: commands
echo    - Gemini CLI: Type / and look for /ipc: commands
echo    - Codex CLI: Type / and look for /ipc: commands
echo.
echo 3. %GREEN%Verify setup:%NC%
echo    Run: scripts\verify-global-installation.ps1
echo.
echo 4. %GREEN%Start using IPC:%NC%
echo    /ipc:setup myname
echo    /ipc:status
echo    /ipc:list
echo.
echo %YELLOW%Note:%NC% If Codex CLI had existing config.toml,
echo please manually merge the IPC configuration.
echo.

pause
