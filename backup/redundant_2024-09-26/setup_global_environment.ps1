# PowerShell Script for Global IPC Environment Setup
# Run as Administrator

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Global IPC Environment Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if running as admin
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Get current directory
$IPC_HOME = (Get-Location).Path
Write-Host "📁 IPC Home Directory: $IPC_HOME" -ForegroundColor Green

# Set system environment variables
Write-Host "`n🔧 Setting system environment variables..." -ForegroundColor Yellow

try {
    # Core variables
    [System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_HOME", $IPC_HOME, "Machine")
    [System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_DB", "$env:USERPROFILE\.claude-ipc-data\messages.db", "Machine")
    [System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_PORT", "9876", "Machine")
    [System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_ENABLED", "true", "Machine")
    [System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_AUTO_RESPONDER", "true", "Machine")

    Write-Host "✅ Environment variables set successfully" -ForegroundColor Green

    # Add tools directory to PATH
    Write-Host "`n🛤️ Adding tools directory to PATH..." -ForegroundColor Yellow
    $currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    $toolsPath = "$IPC_HOME\tools"

    if ($currentPath -notlike "*$toolsPath*") {
        $newPath = "$currentPath;$toolsPath"
        [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
        Write-Host "✅ Tools directory added to PATH" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Tools directory already in PATH" -ForegroundColor Cyan
    }

    # Add Python scripts directory to PATH if exists
    $pythonScriptsPath = "$env:USERPROFILE\AppData\Local\Programs\Python\Python312\Scripts"
    if (Test-Path $pythonScriptsPath) {
        if ($currentPath -notlike "*$pythonScriptsPath*") {
            $newPath = "$currentPath;$pythonScriptsPath"
            [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
            Write-Host "✅ Python Scripts directory added to PATH" -ForegroundColor Green
        }
    }

} catch {
    Write-Host "❌ Error setting environment variables: $_" -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "`n📁 Creating necessary directories..." -ForegroundColor Yellow

$directories = @(
    "$env:USERPROFILE\.claude-ipc",
    "$env:USERPROFILE\.claude-ipc-data",
    "$env:USERPROFILE\.claude-ipc\logs",
    "$IPC_HOME\logs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Already exists: $dir" -ForegroundColor Cyan
    }
}

# Create startup batch file
Write-Host "`n📝 Creating startup script..." -ForegroundColor Yellow

$startupScript = @'
@echo off
echo ====================================
echo Starting Global IPC System...
echo ====================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Set environment variables for this session
set CLAUDE_IPC_HOME=__IPC_HOME__
set CLAUDE_IPC_DB=%USERPROFILE%\.claude-ipc-data\messages.db
set CLAUDE_IPC_PORT=9876
set CLAUDE_IPC_ENABLED=true

REM Start broker server in background
echo [1/3] Starting IPC Broker Server...
start /B python "%CLAUDE_IPC_HOME%\src\claude_ipc_server.py" 2> "%CLAUDE_IPC_HOME%\logs\broker_error.log"

REM Wait for broker to initialize
timeout /t 3 /nobreak >nul

REM Start global auto-registrar
echo [2/3] Starting Auto-Registration System...
start /B python "%CLAUDE_IPC_HOME%\global_auto_register.py" 2> "%CLAUDE_IPC_HOME%\logs\registrar_error.log"

REM Start monitoring (optional)
echo [3/3] Starting Status Monitor...
start /B python "%CLAUDE_IPC_HOME%\global_status.py" 2> "%CLAUDE_IPC_HOME%\logs\monitor_error.log"

echo ====================================
echo ✅ Global IPC System Started!
echo ====================================
echo.
echo Commands available:
echo   ipc_status     - Check system status
echo   ipc_test       - Test connectivity
echo   ipc_monitor    - Open monitoring dashboard
echo.
'@

$startupScript = $startupScript.Replace('__IPC_HOME__', $IPC_HOME)
$startupScript | Out-File -FilePath "$IPC_HOME\start_global_ipc.bat" -Encoding ASCII
Write-Host "✅ Created start_global_ipc.bat" -ForegroundColor Green

# Create Windows Task Scheduler task for auto-start
Write-Host "`n⏰ Setting up Windows Task Scheduler..." -ForegroundColor Yellow

$taskName = "ClaudeIPCGlobal"
$taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($taskExists) {
    Write-Host "ℹ️ Task already exists, removing old task..." -ForegroundColor Cyan
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -File `"$IPC_HOME\start_global_ipc.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogon
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
    Write-Host "✅ Windows Task Scheduler task created" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Could not create Task Scheduler task: $_" -ForegroundColor Yellow
}

# Create convenience commands
Write-Host "`n🎯 Creating global convenience commands..." -ForegroundColor Yellow

$commandsPath = "$IPC_HOME\global_commands"
if (-not (Test-Path $commandsPath)) {
    New-Item -ItemType Directory -Path $commandsPath -Force | Out-Null
}

# ipc_status.bat
@'
@echo off
python "%CLAUDE_IPC_HOME%\global_status.py" --once
'@ | Out-File -FilePath "$commandsPath\ipc_status.bat" -Encoding ASCII

# ipc_test.bat
@'
@echo off
python "%CLAUDE_IPC_HOME%\test_global_connection.py"
'@ | Out-File -FilePath "$commandsPath\ipc_test.bat" -Encoding ASCII

# ipc_monitor.bat
@'
@echo off
python "%CLAUDE_IPC_HOME%\global_status.py"
'@ | Out-File -FilePath "$commandsPath\ipc_monitor.bat" -Encoding ASCII

# Add commands directory to PATH
$currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($currentPath -notlike "*$commandsPath*") {
    $newPath = "$currentPath;$commandsPath"
    [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
    Write-Host "✅ Global commands added to PATH" -ForegroundColor Green
}

# Create Python requirements file
Write-Host "`n📦 Creating requirements file..." -ForegroundColor Yellow

$requirements = @'
# Required packages for IPC system
mcp
rich
'@

$requirements | Out-File -FilePath "$IPC_HOME\requirements-global.txt" -Encoding UTF8
Write-Host "✅ Created requirements-global.txt" -ForegroundColor Green

# Summary
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  ✅ Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Close and reopen your terminal" -ForegroundColor White
Write-Host "  2. Run: start_global_ipc.bat" -ForegroundColor White
Write-Host "  3. Test with: ipc_test" -ForegroundColor White
Write-Host "  4. Monitor with: ipc_monitor" -ForegroundColor White

Write-Host "`n🌐 Environment variables set:" -ForegroundColor Cyan
Write-Host "  CLAUDE_IPC_HOME = $IPC_HOME" -ForegroundColor White
Write-Host "  CLAUDE_IPC_DB = %USERPROFILE%\.claude-ipc-data\messages.db" -ForegroundColor White
Write-Host "  CLAUDE_IPC_PORT = 9876" -ForegroundColor White
Write-Host "  CLAUDE_IPC_ENABLED = true" -ForegroundColor White

Write-Host "`n⚠️ Important: Restart your terminal for changes to take effect!" -ForegroundColor Yellow