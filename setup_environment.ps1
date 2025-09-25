# ============================================================
# Setup Environment Variables for Claude IPC MCP
# Run this script as Administrator in PowerShell
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setting up IPC Environment Variables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define environment variables
$variables = @{
    "CLAUDE_IPC_HOME" = "D:\claude-ipc-mcp"
    "CLAUDE_IPC_DB" = "$env:USERPROFILE\.claude-ipc-data\messages.db"
    "CLAUDE_IPC_ENABLED" = "true"
    "CLAUDE_IPC_AUTO_RESPONDER" = "true"
    "CLAUDE_IPC_MONITOR_CMD" = "ipc-monitor"
    "CLAUDE_IPC_PYTHON" = "python"
}

# Set system environment variables (permanent)
foreach ($key in $variables.Keys) {
    $value = $variables[$key]

    Write-Host "Setting $key = $value" -ForegroundColor Green

    # Set for current session
    [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)

    # Set permanently for user
    [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::User)

    # Optional: Set system-wide (requires admin)
    try {
        [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Machine)
        Write-Host "  ✓ Set system-wide" -ForegroundColor Green
    } catch {
        Write-Host "  ! Could not set system-wide (requires admin)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating Path Shortcuts" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Add scripts directory to PATH
$scriptsPath = "D:\claude-ipc-mcp\scripts"
$currentPath = [System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::User)

if ($currentPath -notlike "*$scriptsPath*") {
    $newPath = "$currentPath;$scriptsPath"
    [System.Environment]::SetEnvironmentVariable("PATH", $newPath, [System.EnvironmentVariableTarget]::User)
    Write-Host "Added $scriptsPath to PATH" -ForegroundColor Green
} else {
    Write-Host "Scripts path already in PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Environment Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment variables set:" -ForegroundColor White

foreach ($key in $variables.Keys) {
    $value = [System.Environment]::GetEnvironmentVariable($key, [System.EnvironmentVariableTarget]::User)
    Write-Host "  $key = $value" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Please restart your terminal for changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")