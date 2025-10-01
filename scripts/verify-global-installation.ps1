# ================================================================================
# IPC Global Installation Verification Script
# Verifies that IPC slash commands are correctly installed for all AI CLIs
# Platform: Windows PowerShell
# ================================================================================

$ErrorActionPreference = "Continue"

# Colors
$GREEN = "Green"
$YELLOW = "Yellow"
$RED = "Red"
$BLUE = "Cyan"

Write-Host ""
Write-Host "========================================" -ForegroundColor $BLUE
Write-Host " IPC Installation Verification" -ForegroundColor $BLUE
Write-Host "========================================" -ForegroundColor $BLUE
Write-Host ""

# ================================================================================
# Verification Functions
# ================================================================================

function Test-DirectoryExists {
    param([string]$Path, [string]$Name)

    if (Test-Path $Path) {
        Write-Host "✓ $Name directory exists: $Path" -ForegroundColor $GREEN
        return $true
    } else {
        Write-Host "✗ $Name directory NOT found: $Path" -ForegroundColor $RED
        return $false
    }
}

function Test-FilesExist {
    param([string]$Path, [string]$Pattern, [int]$ExpectedCount, [string]$Name)

    if (Test-Path $Path) {
        $files = Get-ChildItem -Path $Path -Filter $Pattern -ErrorAction SilentlyContinue
        $count = $files.Count

        if ($count -eq $ExpectedCount) {
            Write-Host "✓ $Name: $count/$ExpectedCount files found" -ForegroundColor $GREEN
            return $true
        } elseif ($count -gt 0) {
            Write-Host "⚠ $Name: $count/$ExpectedCount files found (incomplete)" -ForegroundColor $YELLOW
            return $false
        } else {
            Write-Host "✗ $Name: No files found" -ForegroundColor $RED
            return $false
        }
    } else {
        Write-Host "✗ $Name: Directory does not exist" -ForegroundColor $RED
        return $false
    }
}

function Test-EnvironmentVariable {
    param([string]$VarName, [string]$ExpectedPattern)

    $value = [Environment]::GetEnvironmentVariable($VarName, "User")

    if ($value) {
        if ($ExpectedPattern) {
            if ($value -match $ExpectedPattern) {
                Write-Host "✓ $VarName=$value" -ForegroundColor $GREEN
                return $true
            } else {
                Write-Host "⚠ $VarName=$value (unexpected value)" -ForegroundColor $YELLOW
                return $false
            }
        } else {
            Write-Host "✓ $VarName=$value" -ForegroundColor $GREEN
            return $true
        }
    } else {
        Write-Host "✗ $VarName not set" -ForegroundColor $RED
        return $false
    }
}

# ================================================================================
# Verification: Claude Code
# ================================================================================

Write-Host ""
Write-Host "[1/4] Verifying Claude Code installation..." -ForegroundColor $BLUE
Write-Host ""

$claudeDir = "$env:USERPROFILE\.claude\commands\ipc"
$claudeOk = $true

$claudeOk = $claudeOk -and (Test-DirectoryExists $claudeDir "Claude Code")
$claudeOk = $claudeOk -and (Test-FilesExist $claudeDir "*.md" 9 "Claude Code commands")

if ($claudeOk) {
    Write-Host "✓ Claude Code installation: PASS" -ForegroundColor $GREEN
} else {
    Write-Host "✗ Claude Code installation: FAIL" -ForegroundColor $RED
}

# ================================================================================
# Verification: Gemini CLI
# ================================================================================

Write-Host ""
Write-Host "[2/4] Verifying Gemini CLI installation..." -ForegroundColor $BLUE
Write-Host ""

$geminiDir = "$env:USERPROFILE\.gemini\commands\ipc"
$geminiOk = $true

$geminiOk = $geminiOk -and (Test-DirectoryExists $geminiDir "Gemini CLI")
$geminiOk = $geminiOk -and (Test-FilesExist $geminiDir "*.toml" 9 "Gemini CLI commands")

if ($geminiOk) {
    Write-Host "✓ Gemini CLI installation: PASS" -ForegroundColor $GREEN
} else {
    Write-Host "✗ Gemini CLI installation: FAIL" -ForegroundColor $RED
}

# ================================================================================
# Verification: Codex CLI
# ================================================================================

Write-Host ""
Write-Host "[3/4] Verifying Codex CLI installation..." -ForegroundColor $BLUE
Write-Host ""

$codexDir = "$env:USERPROFILE\.codex"
$codexConfig = "$codexDir\config.toml"
$codexAgents = "$codexDir\AGENTS.md"
$codexOk = $true

$codexOk = $codexOk -and (Test-DirectoryExists $codexDir "Codex CLI")

if (Test-Path $codexConfig) {
    Write-Host "✓ Codex config.toml exists" -ForegroundColor $GREEN

    # Check if config contains IPC commands
    $configContent = Get-Content $codexConfig -Raw
    if ($configContent -match "ipc:setup") {
        Write-Host "✓ Codex config.toml contains IPC commands" -ForegroundColor $GREEN
    } else {
        Write-Host "⚠ Codex config.toml missing IPC commands" -ForegroundColor $YELLOW
        $codexOk = $false
    }
} else {
    Write-Host "✗ Codex config.toml NOT found" -ForegroundColor $RED
    $codexOk = $false
}

if (Test-Path $codexAgents) {
    Write-Host "✓ Codex AGENTS.md exists" -ForegroundColor $GREEN
} else {
    Write-Host "✗ Codex AGENTS.md NOT found" -ForegroundColor $RED
    $codexOk = $false
}

if ($codexOk) {
    Write-Host "✓ Codex CLI installation: PASS" -ForegroundColor $GREEN
} else {
    Write-Host "✗ Codex CLI installation: FAIL" -ForegroundColor $RED
}

# ================================================================================
# Verification: Environment Variables
# ================================================================================

Write-Host ""
Write-Host "[4/4] Verifying environment variables..." -ForegroundColor $BLUE
Write-Host ""

$envOk = $true

$envOk = $envOk -and (Test-EnvironmentVariable "IPC_CHAT" "claude-ipc-mcp")
$envOk = $envOk -and (Test-EnvironmentVariable "IPC_DB_PATH" "\.claude-ipc-data\\messages\.db")
$envOk = $envOk -and (Test-EnvironmentVariable "IPC_HOST" "127\.0\.0\.1")
$envOk = $envOk -and (Test-EnvironmentVariable "IPC_GLOBAL_PORT" "9876")

if ($envOk) {
    Write-Host "✓ Environment variables: PASS" -ForegroundColor $GREEN
} else {
    Write-Host "✗ Environment variables: FAIL" -ForegroundColor $RED
}

# ================================================================================
# Overall Summary
# ================================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor $BLUE
Write-Host " Verification Summary" -ForegroundColor $BLUE
Write-Host "========================================" -ForegroundColor $BLUE
Write-Host ""

$allOk = $claudeOk -and $geminiOk -and $codexOk -and $envOk

if ($allOk) {
    Write-Host "🎉 All checks PASSED!" -ForegroundColor $GREEN
    Write-Host ""
    Write-Host "You can now use IPC slash commands in all AI CLIs:" -ForegroundColor $GREEN
    Write-Host "  /ipc:setup myname" -ForegroundColor $GREEN
    Write-Host "  /ipc:status" -ForegroundColor $GREEN
    Write-Host "  /ipc:list" -ForegroundColor $GREEN
    Write-Host ""
} else {
    Write-Host "⚠ Some checks FAILED" -ForegroundColor $YELLOW
    Write-Host ""
    Write-Host "Results:" -ForegroundColor $YELLOW
    Write-Host "  Claude Code: $(if ($claudeOk) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($claudeOk) { $GREEN } else { $RED })
    Write-Host "  Gemini CLI:  $(if ($geminiOk) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($geminiOk) { $GREEN } else { $RED })
    Write-Host "  Codex CLI:   $(if ($codexOk) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($codexOk) { $GREEN } else { $RED })
    Write-Host "  Environment: $(if ($envOk) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($envOk) { $GREEN } else { $RED })
    Write-Host ""
    Write-Host "Please run: .\scripts\install-all-clis.bat" -ForegroundColor $YELLOW
    Write-Host ""
}

# ================================================================================
# Detailed File Listing (if requested)
# ================================================================================

$showDetails = Read-Host "`nShow detailed file listing? (y/N)"

if ($showDetails -eq 'y' -or $showDetails -eq 'Y') {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor $BLUE
    Write-Host " Detailed File Listing" -ForegroundColor $BLUE
    Write-Host "========================================" -ForegroundColor $BLUE

    Write-Host ""
    Write-Host "Claude Code files:" -ForegroundColor $BLUE
    if (Test-Path $claudeDir) {
        Get-ChildItem -Path $claudeDir -Filter *.md | ForEach-Object { Write-Host "  $_" }
    }

    Write-Host ""
    Write-Host "Gemini CLI files:" -ForegroundColor $BLUE
    if (Test-Path $geminiDir) {
        Get-ChildItem -Path $geminiDir -Filter *.toml | ForEach-Object { Write-Host "  $_" }
    }

    Write-Host ""
    Write-Host "Codex CLI files:" -ForegroundColor $BLUE
    if (Test-Path $codexDir) {
        Get-ChildItem -Path $codexDir -Filter *.toml,*.md | ForEach-Object { Write-Host "  $_" }
    }
}

Write-Host ""
Write-Host "Verification complete!" -ForegroundColor $BLUE
Write-Host ""
