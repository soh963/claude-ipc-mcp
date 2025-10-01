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

# Create command files (.md format for Claude Code)
Write-Host "Installing IPC slash commands..." -ForegroundColor Green
$installed = 0

# Helper function to create .md command file
function Create-CommandFile {
    param($name, $desc, $cmd, $args_desc = $null, $example = $null)

    $content = @"
---
allowed-tools: [Bash]
description: "$desc"
---

# /$name - $($desc -replace '📊|📝|👥|💬|❓|📬|📢|🤖|📊|🛑|🏥|🚀|🏓|✏️|🎯', '' -replace '^\s+', '')

## Purpose
$(if ($args_desc) { $args_desc } else { $desc })

## Usage
``````
/$name$(if ($args_desc) { " <args>" } else { "" })
``````

## Execution
``````bash
cd $projectRoot
$cmd
``````
$(if ($example) { @"

## Example
``````
$example
``````
"@ } else { "" })
"@

    $content | Out-File -FilePath "$commandsDir\$name.md" -Encoding UTF8 -NoNewline
}

# Create all command files
Create-CommandFile "ipc-status" "Check IPC broker connection status" "uv run python tools\ipc_global_command.py status"

Create-CommandFile "ipc-register" "Register this instance with IPC broker" "uv run python tools\ipc_global_command.py register [INSTANCE]" `
    "Register this Claude Code instance with the IPC message broker" "/ipc-register my-instance"

Create-CommandFile "ipc-list" "List all registered IPC instances" "uv run python tools\ipc_global_command.py instances list --full"

Create-CommandFile "ipc-send" "Send message to another instance" "uv run python tools\ipc_global_command.py chat --to [TARGET] `"[MESSAGE]`"" `
    "Send a message without waiting for response" "/ipc-send gemini `"Build complete`""

Create-CommandFile "ipc-ask" "Send message and wait for response" "uv run python tools\ipc_global_command.py ask --to [TARGET] `"[MESSAGE]`" --timeout 10" `
    "Send message and wait up to 10 seconds for response" "/ipc-ask gemini `"Status?`""

Create-CommandFile "ipc-check" "Check messages for this instance" "uv run python tools\ipc_global_command.py messages list"

Create-CommandFile "ipc-broadcast" "Broadcast message to all instances" "uv run python tools\ipc_global_command.py broadcast `"[MESSAGE]`"" `
    "Send message to all registered instances" "/ipc-broadcast `"System restart in 5 min`""

Create-CommandFile "ipc-responder-start" "Start auto-responder for instance" "uv run python tools\ipc_global_command.py responder start [INSTANCE] --policy smart --detach" `
    "Start automatic responder process" "/ipc-responder-start gemini"

Create-CommandFile "ipc-responder-status" "Check auto-responder status" "uv run python tools\ipc_global_command.py responder status [INSTANCE]" `
    "Check if auto-responder is running" "/ipc-responder-status gemini"

Create-CommandFile "ipc-responder-stop" "Stop auto-responder for instance" "uv run python tools\ipc_global_command.py responder stop [INSTANCE]" `
    "Stop auto-responder process" "/ipc-responder-stop gemini"

Create-CommandFile "ipc-doctor" "Run IPC diagnostics and auto-fix issues" "uv run python tools\ipc_doctor.py --auto-fix"

Create-CommandFile "ipc-init" "Initialize IPC in current project" "uv run python tools\ipc_global_command.py init"

Create-CommandFile "ipc-ping" "Ping IPC broker to test connectivity" "uv run python tools\ipc_global_command.py ping"

Create-CommandFile "ipc-rename" "Rename an IPC instance" "uv run python tools\ipc_global_command.py rename --from [OLD] --to [NEW]" `
    "Rename instance (rate limited: 1/hour)" "/ipc-rename old-name new-name"

Create-CommandFile "ipc-setup" "Complete IPC setup" "uv run python tools\ipc_onboard.py --name [INSTANCE] --policy smart" `
    "Register instance and start auto-responder" "/ipc-setup my-instance"

$installed = 15
Write-Host "  ✓ Created 15 IPC command files (.md format)" -ForegroundColor Gray

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
