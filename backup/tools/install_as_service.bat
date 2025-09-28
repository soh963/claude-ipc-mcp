@echo off
echo Installing Claude IPC Auto-Responder as Windows Service...

REM Create a Python script that runs as a service
echo Creating service wrapper...

REM Option 1: Using NSSM (Non-Sucking Service Manager) if available
where nssm >nul 2>nul
if %errorlevel% equ 0 (
    echo Using NSSM to install service...
    nssm install ClaudeIPCMonitor "C:\Python313\python.exe" "D:\claude-ipc-mcp\tools\realtime_notifier.py"
    nssm set ClaudeIPCMonitor Description "Claude IPC Real-time Message Monitor"
    nssm set ClaudeIPCMonitor Start SERVICE_AUTO_START
    nssm start ClaudeIPCMonitor
    echo Service installed and started with NSSM!
) else (
    echo NSSM not found. Using Task Scheduler instead...

    REM Create scheduled task that runs at system startup
    schtasks /create /tn "ClaudeIPC_Service" ^
        /tr "python D:\claude-ipc-mcp\tools\realtime_notifier.py" ^
        /sc onstart ^
        /ru SYSTEM ^
        /rl highest ^
        /f

    REM Also run every minute for reliability
    schtasks /create /tn "ClaudeIPC_Monitor" ^
        /tr "python D:\claude-ipc-mcp\tools\simple_auto_responder.py claude" ^
        /sc minute /mo 1 ^
        /ru %USERNAME% ^
        /f

    echo Scheduled tasks created!
)

echo.
echo Service installation complete!
echo.
echo To check status:
echo   - Task Scheduler: schtasks /query /tn "ClaudeIPC_*"
echo   - NSSM (if used): nssm status ClaudeIPCMonitor
echo.
echo To uninstall:
echo   - Task Scheduler: schtasks /delete /tn "ClaudeIPC_Service" /f
echo   - NSSM (if used): nssm remove ClaudeIPCMonitor
pause