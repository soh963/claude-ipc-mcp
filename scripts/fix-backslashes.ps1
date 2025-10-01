# Fix backslash escaping in Gemini CLI TOML files

$commands = @{
    "status.toml" = @{
        description = "📊 Check IPC connection status"
        prompt = @"
Check the IPC system status:

!{uv run python %IPC_CHAT%\\tools\\ipc_global_command.py status --json}

This shows:
- Broker connection status
- Your instance registration
- Auto-responder status
- Recent activity
"@
    }
    "list.toml" = @{
        description = "📋 List all IPC instances"
        prompt = @"
List all registered IPC instances:

!{uv run python %IPC_CHAT%\\tools\\ipc_global_command.py instances --json}

Shows all active instances that can receive messages.
"@
    }
    "send.toml" = @{
        description = "💬 Send message to another instance"
        prompt = @"
Send an IPC message. Provide arguments as: from_instance to_instance "message"

!{uv run python %IPC_CHAT%\\tools\\chat_once.py {{args}}}

Example usage:
/ipc:send gemini-main claude-worker "Can you review the API design?"

The message will be queued in the broker and delivered to the target instance.
"@
    }
    "check.toml" = @{
        description = "📬 Check for new messages"
        prompt = @"
Check for new IPC messages. Provide your instance name:

!{uv run python %IPC_CHAT%\\tools\\ipc_global_command.py messages check --instance {{args}}}

Example: /ipc:check gemini-main

Shows all unread messages sent to your instance.
"@
    }
    "responder-start.toml" = @{
        description = "🤖 Start auto-responder"
        prompt = @"
Start the auto-responder for your instance. Provide instance name and optionally policy (simple or smart):

!{uv run python %IPC_CHAT%\\tools\\ipc_global_command.py responder start {{args}} --detach}

Example: /ipc:responder-start gemini-main smart

The responder runs in background and automatically replies to incoming messages.
"@
    }
    "responder-status.toml" = @{
        description = "📊 Check responder status"
        prompt = @"
Check auto-responder status for your instance. Provide instance name:

!{uv run python %IPC_CHAT%\\tools\\ipc_global_command.py responder status {{args}} --json}

Example: /ipc:responder-status gemini-main

Shows if responder is running, when it was started, and last activity.
"@
    }
    "responder-stop.toml" = @{
        description = "🛑 Stop auto-responder"
        prompt = @"
Stop the auto-responder for your instance. Provide instance name:

!{uv run python %IPC_CHAT%\\tools\\ipc_global_command.py responder stop {{args}} --json}

Example: /ipc:responder-stop gemini-main

The background responder process will be terminated.
"@
    }
    "doctor.toml" = @{
        description = "🏥 Diagnose and fix IPC issues"
        prompt = @"
Run IPC diagnostics and automatically fix common issues:

!{uv run python %IPC_CHAT%\\tools\\ipc_doctor.py --auto-fix --json}

Checks:
- Broker connectivity
- Database integrity
- Session token validity
- File permissions

Automatically fixes detected issues.
"@
    }
}

$targetDir = "D:\claude-ipc-mcp\scripts\gemini-commands-simple"

Write-Host "Fixing backslash escaping in TOML files..." -ForegroundColor Cyan
Write-Host "Target: $targetDir`n"

foreach ($fileName in $commands.Keys) {
    $cmd = $commands[$fileName]
    $filePath = Join-Path $targetDir $fileName

    $content = @"
# IPC Command for Gemini CLI

description = "$($cmd.description)"
prompt = """
$($cmd.prompt)
"""
"@

    Set-Content -Path $filePath -Value $content -NoNewline
    Write-Host "[UPDATED] $fileName" -ForegroundColor Green
}

Write-Host "`n✓ All files updated with escaped backslashes!" -ForegroundColor Green
Write-Host "`nNext: Copy to Gemini CLI directory:" -ForegroundColor Yellow
Write-Host "  Copy-Item '$targetDir\*.toml' 'C:\Users\lovecat\.gemini\commands\ipc\' -Force" -ForegroundColor White
