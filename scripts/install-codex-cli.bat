@echo off
REM Install IPC integration for Codex/Cursor AI
REM This script copies .cursorrules to your project root

echo ====================================
echo Codex/Cursor IPC Installation
echo ====================================
echo.

REM Get the script directory (where this batch file is located)
set SCRIPT_DIR=%~dp0
set SOURCE_DIR=%SCRIPT_DIR%codex-config

REM Get project root (one level up from scripts/)
for %%i in ("%SCRIPT_DIR%..") do set PROJECT_ROOT=%%~fi

echo Source: %SOURCE_DIR%
echo Target: %PROJECT_ROOT%
echo.

REM Check if source files exist
if not exist "%SOURCE_DIR%\.cursorrules" (
    echo [ERROR] Source file not found: %SOURCE_DIR%\.cursorrules
    echo.
    pause
    exit /b 1
)

REM Copy .cursorrules to project root
echo [1/2] Copying .cursorrules to project root...
copy /Y "%SOURCE_DIR%\.cursorrules" "%PROJECT_ROOT%\.cursorrules" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy .cursorrules
    pause
    exit /b 1
)
echo     [OK] .cursorrules copied

REM Optional: Copy config.toml to .codex directory (if Codex CLI supports it)
echo.
echo [2/2] Checking for .codex directory...
if not exist "%USERPROFILE%\.codex" (
    echo     Creating %USERPROFILE%\.codex directory...
    mkdir "%USERPROFILE%\.codex"
)

if exist "%SOURCE_DIR%\config.toml" (
    echo     Copying config.toml to .codex directory...
    copy /Y "%SOURCE_DIR%\config.toml" "%USERPROFILE%\.codex\config.toml" >nul
    if %ERRORLEVEL% EQU 0 (
        echo     [OK] config.toml copied
    ) else (
        echo     [WARN] config.toml copy failed (optional)
    )
) else (
    echo     [WARN] config.toml not found (optional)
)

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Open your project in Cursor/Codex
echo 2. Cursor will automatically load .cursorrules
echo 3. Test with natural language
echo.
echo Example commands (Korean):
echo   - IPC setup
echo   - IPC status check
echo   - send message to gemini
echo   - check messages
echo   - start auto-responder
echo.
echo Note: Unlike Gemini CLI, Codex uses natural language
echo       instead of slash commands like /ipc:status
echo.
pause
