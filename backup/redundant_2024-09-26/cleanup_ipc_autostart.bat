@echo off
echo ========================================
echo  Removing All IPC Auto-Start Settings
echo ========================================
echo.

REM 1. Remove from Windows Startup folders
echo [1/5] Cleaning Startup folders...
del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\*ipc*.bat" 2>nul
del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\*IPC*.bat" 2>nul
del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\claude*.bat" 2>nul
del /f /q "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\*ipc*.bat" 2>nul
echo     - Startup folder cleaned

REM 2. Remove Registry entries
echo [2/5] Cleaning Registry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ClaudeIPC" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "claude_ipc" /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "IPC_System" /f 2>nul
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "ClaudeIPC" /f 2>nul
echo     - Registry cleaned

REM 3. Remove Task Scheduler tasks
echo [3/5] Cleaning Task Scheduler...
schtasks /delete /tn "ClaudeIPC" /f 2>nul
schtasks /delete /tn "claude_ipc_startup" /f 2>nul
schtasks /delete /tn "IPC_AutoStart" /f 2>nul
schtasks /delete /tn "IPC_Monitor" /f 2>nul
echo     - Task Scheduler cleaned

REM 4. Remove User Environment Variables
echo [4/5] Removing User Environment Variables...
setx IPC_SHARED_SECRET "" 2>nul
reg delete "HKCU\Environment" /v "IPC_SHARED_SECRET" /f 2>nul
setx CLAUDE_IPC_HOME "" 2>nul
reg delete "HKCU\Environment" /v "CLAUDE_IPC_HOME" /f 2>nul
setx CLAUDE_IPC_DB "" 2>nul
reg delete "HKCU\Environment" /v "CLAUDE_IPC_DB" /f 2>nul
setx CLAUDE_IPC_ENABLED "" 2>nul
reg delete "HKCU\Environment" /v "CLAUDE_IPC_ENABLED" /f 2>nul
setx CLAUDE_IPC_AUTO_RESPONDER "" 2>nul
reg delete "HKCU\Environment" /v "CLAUDE_IPC_AUTO_RESPONDER" /f 2>nul
setx IPC_DEFAULT_INSTANCE "" 2>nul
reg delete "HKCU\Environment" /v "IPC_DEFAULT_INSTANCE" /f 2>nul
setx IPC_PYTHON "" 2>nul
reg delete "HKCU\Environment" /v "IPC_PYTHON" /f 2>nul
setx IPC_CHECK "" 2>nul
reg delete "HKCU\Environment" /v "IPC_CHECK" /f 2>nul
setx IPC_SEND "" 2>nul
reg delete "HKCU\Environment" /v "IPC_SEND" /f 2>nul
setx IPC_LIST "" 2>nul
reg delete "HKCU\Environment" /v "IPC_LIST" /f 2>nul
setx IPC_MONITOR "" 2>nul
reg delete "HKCU\Environment" /v "IPC_MONITOR" /f 2>nul
setx IPC_INSTANCES "" 2>nul
reg delete "HKCU\Environment" /v "IPC_INSTANCES" /f 2>nul

REM Korean named variables
reg delete "HKCU\Environment" /v "IPC_확인" /f 2>nul
reg delete "HKCU\Environment" /v "IPC_모니터링" /f 2>nul
reg delete "HKCU\Environment" /v "IPC_메시지" /f 2>nul

echo     - Environment variables removed

REM 5. Remove from PATH if added
echo [5/5] Cleaning PATH...
REM This is complex and risky, so we'll just notify
echo     - Please manually check PATH for IPC-related entries

echo.
echo ========================================
echo  Cleanup Complete!
echo ========================================
echo.
echo All IPC auto-start settings have been removed:
echo   - Startup folder entries: REMOVED
echo   - Registry Run keys: REMOVED
echo   - Task Scheduler tasks: REMOVED
echo   - Environment variables: REMOVED
echo.
echo NOTE: You may need to:
echo   1. Restart your computer for all changes to take effect
echo   2. Manually check PATH variable for IPC entries
echo.
pause