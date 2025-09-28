# AI CLI Integration Environment Setup Script
# PowerShell 7+ recommended
# -*- coding: utf-8 -*-
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 AI CLI Integration Environment Setup Starting..." -ForegroundColor Green

# 1. Create global directories
$globalDirs = @(
    "D:\.ai-cli-ipc",
    "D:\.ai-cli-ipc\shared",
    "D:\.ai-cli-ipc\queue",
    "D:\.ai-cli-ipc\logs",
    "D:\.ai-cli-registry",
    "D:\.ai-cli-cache"
)

foreach ($dir in $globalDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Directory created: $dir" -ForegroundColor Yellow
    }
}

# 2. Set environment variables (user level)
function Set-PermanentEnvVar {
    param([string]$Name, [string]$Value)

    [System.Environment]::SetEnvironmentVariable($Name, $Value, [System.EnvironmentVariableTarget]::User)
    Write-Host "✅ Environment variable set: $Name = $Value" -ForegroundColor Cyan
}

Set-PermanentEnvVar "AI_CLI_HOME" "D:\.ai-cli-ipc"
Set-PermanentEnvVar "AI_CLI_REGISTRY" "D:\.ai-cli-registry"
Set-PermanentEnvVar "AI_CLI_CACHE" "D:\.ai-cli-cache"
Set-PermanentEnvVar "CLAUDE_CLI_PATH" "$PSScriptRoot"
Set-PermanentEnvVar "AI_CLI_IPC_ENABLED" "true"

# 3. Add to PATH
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)
$aiCliPath = "D:\claude-ipc-mcp;D:\.ai-cli-ipc"

if ($currentPath -notlike "*$aiCliPath*") {
    $newPath = "$currentPath;$aiCliPath"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, [System.EnvironmentVariableTarget]::User)
    Write-Host "✅ PATH update complete" -ForegroundColor Green
}

# 4. Apply environment variables immediately
$env:AI_CLI_HOME = "D:\.ai-cli-ipc"
$env:AI_CLI_REGISTRY = "D:\.ai-cli-registry"
$env:AI_CLI_CACHE = "D:\.ai-cli-cache"
$env:CLAUDE_CLI_PATH = $PSScriptRoot
$env:AI_CLI_IPC_ENABLED = "true"
$env:Path = "$env:Path;D:\claude-ipc-mcp;D:\.ai-cli-ipc"

Write-Host "`n✨ Environment setup complete!" -ForegroundColor Green
Write-Host "📝 Changes will be applied in a new terminal session." -ForegroundColor Yellow