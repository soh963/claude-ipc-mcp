@echo off
setlocal enabledelayedexpansion

echo ===========================================
echo Claude CLI MCP Installation (using uv)
echo ===========================================

REM Check for uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: uv is required but not found
    echo Install it with: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    exit /b 1
)

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
REM Get parent directory (repo root)
for %%i in ("%SCRIPT_DIR%") do set "REPO_DIR=%%~dpi"
REM Remove trailing backslash from REPO_DIR
set "REPO_DIR=%REPO_DIR:~0,-1%"

REM Change to repo directory
cd /d "%REPO_DIR%"

REM Check for old installations
if exist "venv" goto :old_install_found
if exist ".venv" goto :old_install_found
goto :continue_install

:old_install_found
echo Warning: Old virtual environment detected!
echo This may interfere with UV installation.
echo.
set /p cleanup=Would you like to clean up old installations? (y/n):
if /i "%cleanup%"=="y" (
    echo Removing old virtual environments...
    if exist "venv" rmdir /s /q "venv"
    if exist ".venv" rmdir /s /q ".venv"
    echo Old installations cleaned up
) else (
    echo Warning: Proceeding with old installations present - this may cause issues
)
echo.

:continue_install
REM Install dependencies with uv
echo Installing dependencies with uv sync...
uv sync
if %errorlevel% neq 0 (
    echo Error: Failed to sync dependencies with uv
    exit /b 1
)

REM Ask user for installation scope
echo.
echo Where would you like to install the MCP?
echo 1) User level (available in all projects)
echo 2) Project level (only in current project)
echo.
set /p choice=Enter your choice (1 or 2):

REM Determine the scope flag
if "%choice%"=="1" (
    set "SCOPE=user"
    set "SCOPE_DESC=user level (all projects)"
) else if "%choice%"=="2" (
    set "SCOPE=project"
    set "SCOPE_DESC=project level (current project only)"
) else (
    echo Invalid choice. Defaulting to user level.
    set "SCOPE=user"
    set "SCOPE_DESC=user level (all projects)"
)

REM Add MCP to Claude Code using uvx
echo.
echo Adding IPC MCP to Claude Code at %SCOPE_DESC%...

REM Run the claude mcp add command
set "COMMAND=claude mcp add claude-cli -s %SCOPE% -- uvx --from %REPO_DIR% claude-ipc-mcp"
echo Running: %COMMAND%
echo.

%COMMAND%
if %errorlevel% equ 0 (
    echo Successfully added Claude CLI MCP!
    echo.

    REM Verify installation
    echo Verifying installation...
    claude mcp list | findstr /i "claude-cli" >nul
    if !errorlevel! equ 0 (
        echo MCP 'claude-cli' is now installed at %SCOPE_DESC%
        echo.
        echo Installation complete!
        echo.
        echo IMPORTANT: Complete restart required!
        echo 1. Exit Claude Code completely (type 'exit'^)
        echo 2. Start a fresh session with 'claude'
        echo 3. Do NOT use --continue or --resume flags
    ) else (
        echo MCP was added but not showing in list yet.
        echo This is normal - please restart Claude Code for it to appear.
    )
) else (
    echo Error: Failed to add MCP. Please check the error message above.
    echo.
    echo You can try running this command manually:
    echo %COMMAND%
    exit /b 1
)

echo ===========================================