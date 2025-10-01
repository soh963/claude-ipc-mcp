# Fix Gemini CLI TOML Files - Add prompt field correctly
# This script ensures all TOML files have the prompt field in the right location

$sourceDir = "D:\claude-ipc-mcp\scripts\gemini-commands"
$targetDir = "$env:USERPROFILE\.gemini\commands\ipc"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Fixing Gemini CLI TOML Files" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Ensure target directory exists
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "[CREATE] Target directory: $targetDir" -ForegroundColor Green
}

# Get all TOML files
$tomlFiles = Get-ChildItem -Path $sourceDir -Filter "*.toml" | Where-Object { $_.Name -ne "status-test.toml" }

foreach ($file in $tomlFiles) {
    Write-Host "`n[PROCESSING] $($file.Name)" -ForegroundColor Yellow

    # Read file content
    $content = Get-Content $file.FullName -Raw

    # Check if prompt field already exists
    if ($content -match 'prompt\s*=') {
        Write-Host "  - Prompt field found, checking location..." -ForegroundColor Gray

        # If prompt is NOT directly after description, fix it
        if ($content -notmatch 'description\s*=\s*"[^"]*"\s*\n\s*prompt\s*=') {
            Write-Host "  - Prompt field in wrong location, fixing..." -ForegroundColor Yellow

            # Remove existing prompt line
            $content = $content -replace '\s*prompt\s*=\s*"[^"]*"\s*\n', "`n"

            # Add prompt field right after description
            $content = $content -replace '(description\s*=\s*"[^"]*")', "`$1`nprompt = ""Execute IPC command"""

            # Write back to source file
            Set-Content -Path $file.FullName -Value $content -NoNewline
            Write-Host "  [FIXED] Prompt field repositioned" -ForegroundColor Green
        } else {
            Write-Host "  [OK] Prompt field in correct location" -ForegroundColor Green
        }
    } else {
        Write-Host "  - No prompt field found, adding..." -ForegroundColor Yellow

        # Add prompt field right after description
        $content = $content -replace '(description\s*=\s*"[^"]*")', "`$1`nprompt = ""Execute IPC command"""

        # Write back to source file
        Set-Content -Path $file.FullName -Value $content -NoNewline
        Write-Host "  [ADDED] Prompt field added" -ForegroundColor Green
    }

    # Copy to target directory
    $targetFile = Join-Path $targetDir $file.Name
    Copy-Item -Path $file.FullName -Destination $targetFile -Force
    Write-Host "  [COPIED] To $targetFile" -ForegroundColor Cyan
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total files processed: $($tomlFiles.Count)" -ForegroundColor White
Write-Host "Source: $sourceDir" -ForegroundColor White
Write-Host "Target: $targetDir" -ForegroundColor White

Write-Host "`n[NEXT STEPS]" -ForegroundColor Yellow
Write-Host "1. Close Gemini CLI completely (all windows)" -ForegroundColor White
Write-Host "2. Restart Gemini CLI" -ForegroundColor White
Write-Host "3. Type / to check if /ipc: commands appear" -ForegroundColor White
Write-Host ""
