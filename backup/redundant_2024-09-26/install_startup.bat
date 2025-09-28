@echo off
REM ============================================================
REM Install Claude IPC MCP to Windows Startup
REM ============================================================

echo Installing Claude IPC MCP to Windows Startup...
echo.

REM Create shortcut in startup folder
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SOURCE_FILE=D:\claude-ipc-mcp\auto_start_ipc.bat

REM Copy batch file to startup folder
copy "%SOURCE_FILE%" "%STARTUP_FOLDER%\claude_ipc_auto_start.bat"

if %ERRORLEVEL% == 0 (
    echo ✅ Successfully installed to Windows startup!
    echo    Location: %STARTUP_FOLDER%
    echo.
    echo The IPC system will now start automatically when Windows starts.
) else (
    echo ❌ Failed to install to startup folder.
    echo    Please run this script as Administrator.
)

echo.
pause