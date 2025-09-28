param()

$script:ToolsPath = Split-Path -Parent $PSCommandPath
$script:RepoRoot = Split-Path -Parent $script:ToolsPath

$script:PythonExecutable = (Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue)
if (-not $script:PythonExecutable) {
    $script:PythonExecutable = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
}
$script:PythonExecutable = $script:PythonExecutable?.Source

$script:UvExecutable = (Get-Command uv.exe -CommandType Application -ErrorAction SilentlyContinue)
if (-not $script:UvExecutable) {
    $script:UvExecutable = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue
}
$script:UvExecutable = $script:UvExecutable?.Source

$script:PowershellExecutable = (Get-Command powershell.exe -CommandType Application -ErrorAction SilentlyContinue)
$script:PwshExecutable = (Get-Command pwsh.exe -CommandType Application -ErrorAction SilentlyContinue)
$script:BashExecutable = (Get-Command bash.exe -CommandType Application -ErrorAction SilentlyContinue)

function Resolve-IPCRelativePath {
    param([string]$Candidate)

    if (-not $Candidate) {
        return $null
    }

    $trimmed = $Candidate.Trim('"')

    if ([System.IO.Path]::IsPathRooted($trimmed)) {
        return $null
    }

    if ($trimmed.StartsWith('./') -or $trimmed.StartsWith('.\\')) {
        $trimmed = $trimmed.Substring(2)
    }

    $normalized = $trimmed -replace '/', '\\'
    $fullPath = Join-Path $script:RepoRoot $normalized

    if (Test-Path $fullPath) {
        return $fullPath
    }

    return $null
}

function Invoke-IPCExecutable {
    param(
        [string]$Executable,
        [string[]]$Arguments,
        [switch]$ForceRepoLocation
    )

    if (-not $Executable) {
        throw "Required executable for IPC helpers could not be located on PATH."
    }

    if ($ForceRepoLocation) {
        Push-Location $script:RepoRoot
    }

    try {
        & $Executable @Arguments
    }
    finally {
        if ($ForceRepoLocation) {
            Pop-Location
        }
    }
}

function python {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $resolved = $null
    if ($Args.Count -gt 0) {
        $resolved = Resolve-IPCRelativePath -Candidate $Args[0]
        if ($resolved) {
            $Args[0] = $resolved
        }
    }

    Invoke-IPCExecutable -Executable $script:PythonExecutable -Arguments $Args -ForceRepoLocation:([bool]$resolved)
}

function uv {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $shouldPush = $false

    if ($Args.Count -eq 1 -and $Args[0] -eq 'sync') {
        $shouldPush = $true
    }

    if ($Args.Count -ge 3 -and $Args[0] -eq 'run' -and $Args[1] -eq 'python') {
        $resolved = Resolve-IPCRelativePath -Candidate $Args[2]
        if ($resolved) {
            $Args[2] = $resolved
            $shouldPush = $true
        }
    }

    Invoke-IPCExecutable -Executable $script:UvExecutable -Arguments $Args -ForceRepoLocation:$shouldPush
}

function powershell {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $processed = @()
    $shouldPush = $false
    $index = 0

    while ($index -lt $Args.Count) {
        $current = $Args[$index]
        $processed += $current

        if ($current -eq '-File' -and ($index + 1) -lt $Args.Count) {
            $candidate = $Args[$index + 1]
            $resolved = Resolve-IPCRelativePath -Candidate $candidate
            if ($resolved) {
                $processed += $resolved
                $shouldPush = $true
                $index += 2
                continue
            }
        }

        $index += 1
    }

    $executable = $script:PowershellExecutable?.Source
    if (-not $executable) {
        throw "powershell.exe was not found."
    }

    Invoke-IPCExecutable -Executable $executable -Arguments $processed -ForceRepoLocation:$shouldPush
}

function pwsh {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    if (-not $script:PwshExecutable) {
        throw "pwsh.exe was not found. Install PowerShell 7 to use pwsh commands."
    }

    $processed = @()
    $shouldPush = $false
    $index = 0

    while ($index -lt $Args.Count) {
        $current = $Args[$index]
        $processed += $current

        if ($current -eq '-File' -and ($index + 1) -lt $Args.Count) {
            $candidate = $Args[$index + 1]
            $resolved = Resolve-IPCRelativePath -Candidate $candidate
            if ($resolved) {
                $processed += $resolved
                $shouldPush = $true
                $index += 2
                continue
            }
        }

        $index += 1
    }

    Invoke-IPCExecutable -Executable $script:PwshExecutable.Source -Arguments $processed -ForceRepoLocation:$shouldPush
}

function bash {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    if (-not $script:BashExecutable) {
        throw "bash.exe was not found. Install Git Bash or WSL to use bash commands."
    }

    $shouldPush = $false
    if ($Args.Count -gt 0) {
        $resolved = Resolve-IPCRelativePath -Candidate $Args[0]
        if ($resolved) {
            $Args[0] = $resolved
            $shouldPush = $true
        }
    }

    Invoke-IPCExecutable -Executable $script:BashExecutable.Source -Arguments $Args -ForceRepoLocation:$shouldPush
}

$env:IPC_CHAT = "python `"$script:ToolsPath\nl_auto_chat.py`""

function ipc-chat {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Args
    )
    python "$script:ToolsPath\nl_auto_chat.py" @Args
}

function ipc-ping {
    param(
        [string]$From = "codex",
        [string]$To = "gemini",
        [Parameter(Mandatory = $true)][string]$Message
    )
    python "$script:ToolsPath\chat_once.py" $From $To $Message --auto-responder --timeout 10
}

function ipc-responder-list {
    python "$script:ToolsPath\manage_responders.py"
}

function ipc-responder-stop {
    param([string]$Instance)
    if ($Instance) {
        python "$script:ToolsPath\manage_responders.py" --instance $Instance --stop
    }
    else {
        python "$script:ToolsPath\manage_responders.py" --stop-all
    }
}

Write-Host "IPC CLI helpers loaded. Tools path: $script:ToolsPath"