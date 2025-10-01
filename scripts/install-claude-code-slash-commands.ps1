# Install IPC Slash Commands for Claude Code CLI
# This script registers all IPC commands as slash commands in Claude Code

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IPC Slash Commands Installer for Claude Code" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Create Claude Code slash commands directory if it doesn't exist
$claudeDir = "$env:USERPROFILE\.claude"
$commandsDir = "$claudeDir\commands"

if (-not (Test-Path $commandsDir)) {
    Write-Host "Creating commands directory: $commandsDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $commandsDir -Force | Out-Null
}

# Define all IPC slash commands
$commands = @{
    "ipc-status" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" status"
        description = "📊 Check IPC broker connection status"
        category = "ipc"
    }
    "ipc-register" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" register {args[0]}"
        description = "📝 Register this instance with IPC broker"
        category = "ipc"
        requires_args = 1
        arg_names = @("instance_name")
    }
    "ipc-list" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" instances list --full"
        description = "👥 List all registered IPC instances"
        category = "ipc"
    }
    "ipc-send" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" chat --to {args[0]} `"{args[1]}`""
        description = "💬 Send message to another instance"
        category = "ipc"
        requires_args = 2
        arg_names = @("target_instance", "message")
    }
    "ipc-ask" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" ask --to {args[0]} `"{args[1]}`" --timeout 10"
        description = "❓ Send message and wait for response (10s timeout)"
        category = "ipc"
        requires_args = 2
        arg_names = @("target_instance", "message")
    }
    "ipc-check" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" messages list"
        description = "📬 Check messages for this instance"
        category = "ipc"
    }
    "ipc-broadcast" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" broadcast `"{args[0]}`""
        description = "📢 Broadcast message to all instances"
        category = "ipc"
        requires_args = 1
        arg_names = @("message")
    }
    "ipc-responder-start" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" responder start {args[0]} --policy smart --detach"
        description = "🤖 Start auto-responder for instance"
        category = "ipc"
        requires_args = 1
        arg_names = @("instance_name")
    }
    "ipc-responder-status" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" responder status {args[0]}"
        description = "📊 Check auto-responder status"
        category = "ipc"
        requires_args = 1
        arg_names = @("instance_name")
    }
    "ipc-responder-stop" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" responder stop {args[0]}"
        description = "🛑 Stop auto-responder for instance"
        category = "ipc"
        requires_args = 1
        arg_names = @("instance_name")
    }
    "ipc-doctor" = @{
        command = "uv run python `"$projectRoot\tools\ipc_doctor.py`" --auto-fix"
        description = "🏥 Run IPC diagnostics and auto-fix issues"
        category = "ipc"
    }
    "ipc-init" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" init"
        description = "🚀 Initialize IPC in current project"
        category = "ipc"
    }
    "ipc-ping" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" ping"
        description = "🏓 Ping IPC broker to test connectivity"
        category = "ipc"
    }
    "ipc-rename" = @{
        command = "uv run python `"$projectRoot\tools\ipc_global_command.py`" rename --from {args[0]} --to {args[1]}"
        description = "✏️ Rename an IPC instance (rate limited: 1/hour)"
        category = "ipc"
        requires_args = 2
        arg_names = @("old_name", "new_name")
    }
    "ipc-setup" = @{
        command = "uv run python `"$projectRoot\tools\ipc_onboard.py`" --name {args[0]} --policy smart"
        description = "🎯 Complete IPC setup (register + auto-responder)"
        category = "ipc"
        requires_args = 1
        arg_names = @("instance_name")
    }
}

# Create command files
Write-Host "Installing IPC slash commands..." -ForegroundColor Green
$installed = 0

foreach ($cmdName in $commands.Keys) {
    $cmdData = $commands[$cmdName]
    $cmdFile = "$commandsDir\$cmdName.json"

    $cmdJson = @{
        command = $cmdData.command
        description = $cmdData.description
        category = $cmdData.category
    }

    if ($cmdData.requires_args) {
        $cmdJson.requires_args = $cmdData.requires_args
        $cmdJson.arg_names = $cmdData.arg_names
    }

    $cmdJson | ConvertTo-Json -Depth 10 | Out-File -FilePath $cmdFile -Encoding UTF8
    Write-Host "  ✓ Installed: /$cmdName" -ForegroundColor Gray
    $installed++
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installed $installed IPC slash commands" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage in Claude Code CLI:" -ForegroundColor Yellow
Write-Host "  /ipc-status              - Check broker status" -ForegroundColor White
Write-Host "  /ipc-register myname     - Register instance" -ForegroundColor White
Write-Host "  /ipc-send gemini 'Hi!'   - Send message" -ForegroundColor White
Write-Host "  /ipc-ask gemini 'How?'   - Ask and wait for reply" -ForegroundColor White
Write-Host "  /ipc-check               - Check messages" -ForegroundColor White
Write-Host "  /ipc-responder-start gem - Start auto-responder" -ForegroundColor White
Write-Host ""
Write-Host "Restart Claude Code to see the new commands!" -ForegroundColor Yellow
Write-Host ""
