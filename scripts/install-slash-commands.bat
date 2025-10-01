@echo off
REM ========================================================================
REM  IPC Slash Commands Installation Script for Claude Code
REM  Automatically installs all IPC-related slash commands
REM ========================================================================

setlocal enabledelayedexpansion

REM Configuration
set "CLAUDE_COMMANDS_DIR=%USERPROFILE%\.claude\commands"
set "PROJECT_COMMANDS_DIR=.claude\commands"
set "SCRIPT_DIR=%~dp0"

echo.
echo ========================================
echo  IPC Slash Commands Installer
echo ========================================
echo.

REM Ask installation scope
echo Where would you like to install IPC commands?
echo.
echo [1] User-wide (recommended) - %USERPROFILE%\.claude\commands
echo     Commands available in ALL projects
echo.
echo [2] Project-only - .claude\commands
echo     Commands available ONLY in this project
echo.
set /p "INSTALL_SCOPE=Enter choice (1 or 2): "

if "%INSTALL_SCOPE%"=="1" (
    set "TARGET_DIR=%CLAUDE_COMMANDS_DIR%"
    set "SCOPE_NAME=user-wide"
) else if "%INSTALL_SCOPE%"=="2" (
    set "TARGET_DIR=%PROJECT_COMMANDS_DIR%"
    set "SCOPE_NAME=project-only"
) else (
    echo Invalid choice. Exiting.
    exit /b 1
)

echo.
echo Installing IPC commands (%SCOPE_NAME%)...
echo Target directory: %TARGET_DIR%
echo.

REM Create commands directory if it doesn't exist
if not exist "%TARGET_DIR%\ipc" (
    echo Creating directory: %TARGET_DIR%\ipc
    mkdir "%TARGET_DIR%\ipc"
)

REM Create ipc-setup.md
echo Creating /ipc-setup command...
(
echo # IPC Setup Command
echo.
echo Complete IPC setup in one command - register this instance and start auto-responder.
echo.
echo ## What this command does:
echo - Registers this Claude instance with the IPC broker
echo - Starts auto-responder for automatic message handling
echo - Verifies connection with ping test
echo.
echo ## Usage:
echo ```
echo /ipc-setup myname
echo ```
echo.
echo ## Arguments:
echo - $ARGUMENTS: Your instance name ^(alphanumeric, dash, underscore only^)
echo.
echo Now executing setup...
echo.
echo ```bash
echo uv run python tools/ipc_onboard.py --name $ARGUMENTS --policy smart
echo ```
) > "%TARGET_DIR%\ipc\setup.md"

REM Create ipc-status.md
echo Creating /ipc-status command...
(
echo # IPC Status Command
echo.
echo Check your IPC connection status and responder state.
echo.
echo ## What this command shows:
echo - Broker connection status
echo - Your instance registration
echo - Auto-responder status
echo - Recent message activity
echo.
echo ## Usage:
echo ```
echo /ipc-status
echo ```
echo.
echo Checking IPC status...
echo.
echo ```bash
echo uv run python tools/ipc_global_command.py status --json
echo ```
) > "%TARGET_DIR%\ipc\status.md"

REM Create ipc-list.md
echo Creating /ipc-list command...
(
echo # IPC List Instances Command
echo.
echo List all AI instances currently connected to the IPC broker.
echo.
echo ## What this command shows:
echo - All registered instances
echo - Last activity timestamp
echo - Active auto-responders
echo.
echo ## Usage:
echo ```
echo /ipc-list
echo ```
echo.
echo Retrieving instance list...
echo.
echo ```bash
echo uv run python tools/ipc_global_command.py instances --format table
echo ```
) > "%TARGET_DIR%\ipc\list.md"

REM Create ipc-send.md
echo Creating /ipc-send command...
(
echo # IPC Send Message Command
echo.
echo Send a message to another AI instance through IPC.
echo.
echo ## Arguments Format:
echo ```
echo /ipc-send FROM TO MESSAGE
echo ```
echo.
echo ## Example:
echo ```
echo /ipc-send claude gemini "Can you help with the API design?"
echo ```
echo.
echo ## What happens:
echo - Message is queued in broker
echo - Target instance receives notification
echo - Auto-responder may reply automatically
echo.
echo Sending message...
echo.
echo ```bash
echo uv run python tools/chat_once.py $ARGUMENTS
echo ```
) > "%TARGET_DIR%\ipc\send.md"

REM Create ipc-check.md
echo Creating /ipc-check command...
(
echo # IPC Check Messages Command
echo.
echo Check for new messages sent to this instance.
echo.
echo ## Usage:
echo ```
echo /ipc-check myname
echo ```
echo.
echo ## Arguments:
echo - $ARGUMENTS: Your instance name
echo.
echo ## What you'll see:
echo - List of unread messages
echo - Sender and timestamp
echo - Message content
echo.
echo Checking messages...
echo.
echo ```bash
echo uv run python tools/ipc_global_command.py messages check --instance $ARGUMENTS
echo ```
) > "%TARGET_DIR%\ipc\check.md"

REM Create ipc-responder-start.md
echo Creating /ipc-responder-start command...
(
echo # IPC Start Auto-Responder Command
echo.
echo Start automatic message responder for this instance.
echo.
echo ## Arguments Format:
echo ```
echo /ipc-responder-start INSTANCE_NAME [POLICY]
echo ```
echo.
echo ## Policies:
echo - **simple**: Echo all messages back
echo - **smart**: Context-aware responses ^(default^)
echo.
echo ## Example:
echo ```
echo /ipc-responder-start claude smart
echo ```
echo.
echo Starting auto-responder...
echo.
echo ```bash
echo uv run python tools/ipc_global_command.py responder start $ARGUMENTS --detach
echo ```
) > "%TARGET_DIR%\ipc\responder-start.md"

REM Create ipc-responder-status.md
echo Creating /ipc-responder-status command...
(
echo # IPC Responder Status Command
echo.
echo Check if auto-responder is running for your instance.
echo.
echo ## Usage:
echo ```
echo /ipc-responder-status myname
echo ```
echo.
echo ## Arguments:
echo - $ARGUMENTS: Your instance name
echo.
echo ## What you'll see:
echo - Running status ^(active/stopped^)
echo - Process ID if running
echo - Last activity timestamp
echo - Current policy
echo.
echo Checking responder status...
echo.
echo ```bash
echo uv run python tools/ipc_global_command.py responder status $ARGUMENTS
echo ```
) > "%TARGET_DIR%\ipc\responder-status.md"

REM Create ipc-responder-stop.md
echo Creating /ipc-responder-stop command...
(
echo # IPC Stop Responder Command
echo.
echo Stop auto-responder for this instance.
echo.
echo ## Usage:
echo ```
echo /ipc-responder-stop myname
echo ```
echo.
echo ## Arguments:
echo - $ARGUMENTS: Your instance name
echo.
echo Stopping responder...
echo.
echo ```bash
echo uv run python tools/ipc_global_command.py responder stop $ARGUMENTS
echo ```
) > "%TARGET_DIR%\ipc\responder-stop.md"

REM Create ipc-doctor.md
echo Creating /ipc-doctor command...
(
echo # IPC Doctor Command
echo.
echo Diagnose and automatically fix common IPC connection issues.
echo.
echo ## What this command checks:
echo - Broker connectivity
echo - Database integrity
echo - Session token validity
echo - Auto-responder health
echo - File permissions
echo.
echo ## What it can fix:
echo - Restart dead broker
echo - Reset expired sessions
echo - Fix database schema
echo - Clean up zombie processes
echo.
echo ## Usage:
echo ```
echo /ipc-doctor
echo ```
echo.
echo Running diagnostics...
echo.
echo ```bash
echo uv run python tools/ipc_doctor.py --auto-fix
echo ```
) > "%TARGET_DIR%\ipc\doctor.md"

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Installed commands:
echo   /ipc:setup             - One-click IPC setup
echo   /ipc:status            - Check connection status
echo   /ipc:list              - List all instances
echo   /ipc:send              - Send message
echo   /ipc:check             - Check messages
echo   /ipc:responder-start   - Start auto-responder
echo   /ipc:responder-status  - Check responder status
echo   /ipc:responder-stop    - Stop responder
echo   /ipc:doctor            - Diagnose and fix issues
echo.
echo Location: %TARGET_DIR%\ipc\
echo.
echo To use these commands in Claude Code:
echo   1. Restart Claude Code to load new commands
echo   2. Type / in chat to see all commands
echo   3. Use /ipc: prefix to access IPC commands
echo.
echo Example: /ipc:setup claude-main
echo.
pause
