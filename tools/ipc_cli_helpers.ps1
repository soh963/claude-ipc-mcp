param()

$script:ToolsPath = Split-Path -Parent $PSCommandPath

# Export helper environment variable so other CLI tools (Claude/Gemini/Codex) can call it directly
$env:IPC_CHAT = "python `"$ToolsPath\nl_auto_chat.py`""

function ipc-chat {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Args
    )
    python "$ToolsPath\nl_auto_chat.py" @Args
}

function ipc-ping {
    param(
        [string]$From = "codex",
        [string]$To = "gemini",
        [Parameter(Mandatory = $true)][string]$Message
    )
    python "$ToolsPath\chat_once.py" $From $To $Message --auto-responder --timeout 10
}

function ipc-responder-list {
    python "$ToolsPath\manage_responders.py"
}

function ipc-responder-stop {
    param([string]$Instance)
    if ($Instance) {
        python "$ToolsPath\manage_responders.py" --instance $Instance --stop
    }
    else {
        python "$ToolsPath\manage_responders.py" --stop-all
    }
}

Write-Host "IPC CLI helpers loaded. Tools path: $ToolsPath"