@echo off
echo Setting up automatic message checking...

REM Create scheduled task to run every 5 seconds
schtasks /create /tn "Claude_IPC_AutoCheck" /tr "python D:\claude-ipc-mcp\tools\simple_auto_responder.py claude" /sc minute /mo 1 /f

echo Task created! Messages will be checked every minute.
echo To stop: schtasks /delete /tn "Claude_IPC_AutoCheck" /f
pause