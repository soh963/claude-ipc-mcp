@echo off
echo Adding Claude IPC Monitor to Windows Startup...

REM Get the startup folder path
set "startup=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Create a batch file in the startup folder
echo @echo off > "%startup%\ClaudeIPCMonitor.bat"
echo start /min python D:\claude-ipc-mcp\tools\realtime_notifier.py >> "%startup%\ClaudeIPCMonitor.bat"

echo.
echo ✅ Added to Windows Startup!
echo.
echo The monitor will automatically start when you log in to Windows.
echo.
echo Location: %startup%\ClaudeIPCMonitor.bat
echo.
echo To remove from startup, delete the file above.
pause