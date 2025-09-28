# IPC 4-Panel Monitor PowerShell Script
Write-Host "Starting IPC 4-Panel Monitor..." -ForegroundColor Green
Write-Host ""

# Change to project directory
Set-Location D:\claude-ipc-mcp

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python tools\ipc_manager.py init

# Register instances
Write-Host "Registering instances..." -ForegroundColor Yellow
python tools\ipc_manager.py register claude
python tools\ipc_manager.py register gemini
python tools\ipc_manager.py register codex
python tools\ipc_manager.py register lm

Write-Host ""
Write-Host "Starting Windows Terminal with 4 panels..." -ForegroundColor Green
Write-Host @"
+------------+------------+
| CLAUDE     | GEMINI     |
+------------+------------+
| CODEX      | LM         |
+------------+------------+
"@

# Start Windows Terminal with 4 panels
$wtCommand = @"
wt new-tab --title "IPC Monitor" `
cmd /k "cd /d D:\claude-ipc-mcp && color 0A && python tools\fixed_monitor.py claude" `; `
split-pane -H cmd /k "cd /d D:\claude-ipc-mcp && color 0B && python tools\fixed_monitor.py gemini" `; `
split-pane -V -t 0 cmd /k "cd /d D:\claude-ipc-mcp && color 0C && python tools\fixed_monitor.py codex" `; `
split-pane -V -t 2 cmd /k "cd /d D:\claude-ipc-mcp && color 0E && python tools\fixed_monitor.py lm"
"@

Invoke-Expression $wtCommand

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "4-Panel Monitor Started!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Send messages from another terminal:" -ForegroundColor Yellow
Write-Host "  python tools\ipc_manager.py send [from] [to] [message]"
Write-Host ""
Write-Host "Example:" -ForegroundColor Yellow
Write-Host '  python tools\ipc_manager.py send claude gemini "Hello!"'
Write-Host '  python tools\ipc_manager.py broadcast claude "Hello all!"'
Write-Host "================================" -ForegroundColor Cyan