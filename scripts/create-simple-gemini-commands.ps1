# Create Simple Gemini CLI TOML Files
# Following official Gemini CLI format: only 'description' and 'prompt' fields

$targetDir = "scripts\gemini-commands-simple"

# Create directory if needed
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

# Define all commands with simple format
$commands = @{
    "status.toml" = @{
        description = "📊 Check IPC connection status"
        prompt = @"
Check the IPC system status:

!{uv run python %IPC_CHAT%\tools\ipc_global_command.py status --json}

This shows:
- Broker connection status
- Your instance registration
- Auto-responder status
- Recent activity
"@
    }

    "list.toml" = @{
        description = "👥 List all active IPC instances"
        prompt = @"
List all instances connected to the IPC broker:

!{uv run python %IPC_CHAT%\tools\ipc_global_command.py instances --format json}

Shows all registered AI instances and their last activity.
"@
    }

    "send.toml" = @{
        description = "💬 Send message to another instance"
        prompt = @"
Send an IPC message. Provide arguments as: from_instance to_instance "message"

!{uv run python %IPC_CHAT%\tools\chat_once.py {{args}}}

Example usage:
/ipc:send gemini-main claude-worker "Can you review the API design?"

The message will be queued in the broker and delivered to the target instance.
"@
    }

    "check.toml" = @{
        description = "📬 Check for new messages"
        prompt = @"
Check messages for your instance. Provide your instance name as argument:

!{uv run python %IPC_CHAT%\tools\ipc_global_command.py messages check --instance {{args}} --json}

Example: /ipc:check gemini-main

Shows all unread messages sent to your instance.
"@
    }

    "responder-start.toml" = @{
        description = "🤖 Start auto-responder"
        prompt = @"
Start the auto-responder for your instance. Provide instance name and optionally policy (simple or smart):

!{uv run python %IPC_CHAT%\tools\ipc_global_command.py responder start {{args}} --detach}

Example: /ipc:responder-start gemini-main smart

The responder runs in background and automatically replies to incoming messages.
"@
    }

    "responder-status.toml" = @{
        description = "📊 Check responder status"
        prompt = @"
Check if auto-responder is running. Provide your instance name:

!{uv run python %IPC_CHAT%\tools\ipc_global_command.py responder status {{args}} --json}

Example: /ipc:responder-status gemini-main

Shows responder state, PID, policy, and last activity.
"@
    }

    "responder-stop.toml" = @{
        description = "🛑 Stop auto-responder"
        prompt = @"
Stop the auto-responder for your instance. Provide instance name:

!{uv run python %IPC_CHAT%\tools\ipc_global_command.py responder stop {{args}} --json}

Example: /ipc:responder-stop gemini-main

The background responder process will be terminated.
"@
    }

    "doctor.toml" = @{
        description = "🏥 Diagnose and fix IPC issues"
        prompt = @"
Run IPC diagnostics and automatically fix common issues:

!{uv run python %IPC_CHAT%\tools\ipc_doctor.py --auto-fix --json}

Checks:
- Broker connectivity
- Database integrity
- Session token validity
- File permissions

Automatically fixes detected issues.
"@
    }
}

Write-Host "`nCreating Simple Gemini CLI TOML Files..." -ForegroundColor Cyan
Write-Host "Target: $targetDir`n" -ForegroundColor Gray

foreach ($fileName in $commands.Keys) {
    $filePath = Join-Path $targetDir $fileName
    $cmd = $commands[$fileName]

    $content = @"
# IPC Command for Gemini CLI

description = "$($cmd.description)"
prompt = """
$($cmd.prompt)
"""
"@

    Set-Content -Path $filePath -Value $content -NoNewline
    Write-Host "[CREATED] $fileName" -ForegroundColor Green
}

Write-Host "`n✓ All files created successfully!" -ForegroundColor Green
Write-Host "`nNext: Copy to Gemini CLI directory:" -ForegroundColor Yellow
Write-Host "  Copy-Item '$targetDir\*.toml' '`$env:USERPROFILE\.gemini\commands\ipc\' -Force" -ForegroundColor Gray
