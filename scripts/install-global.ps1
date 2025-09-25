# ============================================================
# Claude IPC MCP Global Environment Setup
# This script sets up global environment variables for all sessions
# Run as Administrator: powershell -ExecutionPolicy Bypass -File install-global.ps1
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Claude IPC MCP Global Setup" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "⚠️  This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run as Administrator." -ForegroundColor Yellow
    pause
    exit 1
}

# Define all environment variables
$globalVars = @{
    # Core IPC variables
    "CLAUDE_IPC_HOME" = "D:\claude-ipc-mcp"
    "CLAUDE_IPC_DB" = "$env:USERPROFILE\.claude-ipc-data\messages.db"
    "CLAUDE_IPC_ENABLED" = "true"
    "CLAUDE_IPC_AUTO_RESPONDER" = "true"

    # Command shortcuts
    "IPC_MONITOR" = "D:\claude-ipc-mcp\scripts\ipc-monitor.bat"
    "IPC_SEND" = "D:\claude-ipc-mcp\scripts\ipc-send.bat"
    "IPC_CHECK" = "python D:\claude-ipc-mcp\tools\ipc_manager.py check"
    "IPC_LIST" = "python D:\claude-ipc-mcp\tools\ipc_manager.py list"

    # Natural language commands
    "IPC_모니터링" = "D:\claude-ipc-mcp\scripts\ipc-monitor.bat"
    "IPC_메시지" = "D:\claude-ipc-mcp\scripts\ipc-send.bat"
    "IPC_확인" = "python D:\claude-ipc-mcp\tools\ipc_manager.py check"

    # Instance identifiers
    "IPC_INSTANCES" = "claude,gemini,codex,codex-local,lm"
    "IPC_DEFAULT_INSTANCE" = "claude"

    # Python path for IPC
    "IPC_PYTHON" = "python"
}

Write-Host "Setting Global Environment Variables..." -ForegroundColor Green
Write-Host ""

foreach ($key in $globalVars.Keys) {
    $value = $globalVars[$key]

    Write-Host "  Setting $key" -ForegroundColor Yellow

    # Set for Machine (System-wide)
    try {
        [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Machine)
        Write-Host "    ✓ System-wide" -ForegroundColor Green
    } catch {
        Write-Host "    ✗ Failed to set system-wide" -ForegroundColor Red
    }

    # Also set for User
    [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::User)
    Write-Host "    ✓ User-level" -ForegroundColor Green

    # Set for current session
    [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Adding to System PATH" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Add scripts directory to PATH
$scriptsPath = "D:\claude-ipc-mcp\scripts"
$toolsPath = "D:\claude-ipc-mcp\tools"

# Get current system PATH
$machinePath = [System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::Machine)

# Add scripts path if not already there
if ($machinePath -notlike "*$scriptsPath*") {
    $newPath = "$machinePath;$scriptsPath;$toolsPath"
    [System.Environment]::SetEnvironmentVariable("PATH", $newPath, [System.EnvironmentVariableTarget]::Machine)
    Write-Host "  ✓ Added $scriptsPath to System PATH" -ForegroundColor Green
    Write-Host "  ✓ Added $toolsPath to System PATH" -ForegroundColor Green
} else {
    Write-Host "  ℹ Paths already in System PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating Command Aliases" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create batch files for easy commands
$aliasCommands = @{
    "모니터링.bat" = "@echo off`n%IPC_MONITOR%"
    "monitoring.bat" = "@echo off`n%IPC_MONITOR%"
    "ipc.bat" = "@echo off`npython D:\claude-ipc-mcp\tools\ipc_manager.py %*"
}

foreach ($filename in $aliasCommands.Keys) {
    $content = $aliasCommands[$filename]
    $filepath = "D:\claude-ipc-mcp\scripts\$filename"

    Set-Content -Path $filepath -Value $content -Encoding ASCII
    Write-Host "  ✓ Created $filename" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing to Windows Startup" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Copy startup script to Windows Startup folder
$startupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$startupScript = "D:\claude-ipc-mcp\auto_start_ipc.bat"
$startupDest = "$startupFolder\claude_ipc_startup.bat"

if (Test-Path $startupScript) {
    Copy-Item -Path $startupScript -Destination $startupDest -Force
    Write-Host "  ✓ Installed to Windows Startup" -ForegroundColor Green
    Write-Host "    Location: $startupDest" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Startup script not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verification" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify environment variables
Write-Host "Verifying environment variables:" -ForegroundColor White
foreach ($key in $globalVars.Keys) {
    $value = [System.Environment]::GetEnvironmentVariable($key, [System.EnvironmentVariableTarget]::Machine)
    if ($value) {
        Write-Host "  ✓ $key = $value" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $key not set" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Available Commands" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "From any terminal or project:" -ForegroundColor White
Write-Host "  모니터링        - Start 4-panel monitoring" -ForegroundColor Gray
Write-Host "  monitoring     - Start 4-panel monitoring" -ForegroundColor Gray
Write-Host "  ipc send       - Send message between instances" -ForegroundColor Gray
Write-Host "  ipc check      - Check messages" -ForegroundColor Gray
Write-Host "  ipc list       - List all instances" -ForegroundColor Gray
Write-Host "  ipc-monitor    - Start monitoring" -ForegroundColor Gray
Write-Host "  ipc-send       - Send message" -ForegroundColor Gray
Write-Host ""
Write-Host "Environment Variables (accessible everywhere):" -ForegroundColor White
Write-Host "  %CLAUDE_IPC_HOME%     - IPC home directory" -ForegroundColor Gray
Write-Host "  %CLAUDE_IPC_DB%       - Database location" -ForegroundColor Gray
Write-Host "  %IPC_MONITOR%         - Monitoring command" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  IMPORTANT: Please restart your computer or log out and back in" -ForegroundColor Yellow
Write-Host "   for the environment variables to take effect globally." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")