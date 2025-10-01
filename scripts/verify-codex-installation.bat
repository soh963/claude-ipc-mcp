@echo off
REM Verify Codex/Cursor IPC installation

echo ====================================
echo Codex/Cursor IPC Verification
echo ====================================
echo.

set SCRIPT_DIR=%~dp0
for %%i in ("%SCRIPT_DIR%..") do set PROJECT_ROOT=%%~fi

echo Checking installation...
echo.

REM Check .cursorrules in project root
echo [1/3] Checking .cursorrules in project root...
if exist "%PROJECT_ROOT%\.cursorrules" (
    echo     √ .cursorrules found
    echo     Location: %PROJECT_ROOT%\.cursorrules
) else (
    echo     X .cursorrules NOT found
    echo     Please run scripts\install-codex-cli.bat
)

echo.

REM Check .codex directory
echo [2/3] Checking .codex directory...
if exist "%USERPROFILE%\.codex" (
    echo     √ .codex directory exists
    if exist "%USERPROFILE%\.codex\config.toml" (
        echo     √ config.toml found
    ) else (
        echo     ! config.toml not found (optional)
    )
) else (
    echo     ! .codex directory not found (optional)
)

echo.

REM Check if Cursor is installed
echo [3/3] Checking Cursor installation...
where cursor >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     √ Cursor CLI found
) else (
    echo     ! Cursor CLI not found (may be installed but not in PATH)
    echo     Location: Usually in %LOCALAPPDATA%\Programs\cursor\
)

echo.
echo ====================================
echo Verification Complete
echo ====================================
echo.
echo How to use:
echo 1. Open project in Cursor
echo 2. Use natural language commands:
echo    - "IPC 상태 확인해줘"
echo    - "codex-main으로 등록해줘"
echo    - "메시지 확인"
echo.
echo Note: Cursor loads .cursorrules automatically
echo       No manual activation needed!
echo.
pause
