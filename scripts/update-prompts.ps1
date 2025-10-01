# Update all TOML files with specific prompt messages
# Each command gets a descriptive prompt

$sourceDir = "D:\claude-ipc-mcp\scripts\gemini-commands"
$targetDir = "$env:USERPROFILE\.gemini\commands\ipc"

# Define specific prompts for each command
$prompts = @{
    "setup.toml" = "Setup IPC for this instance"
    "status.toml" = "Check IPC status"
    "list.toml" = "List all IPC instances"
    "send.toml" = "Send IPC message"
    "check.toml" = "Check IPC messages"
    "responder-start.toml" = "Start IPC responder"
    "responder-status.toml" = "Check IPC responder status"
    "responder-stop.toml" = "Stop IPC responder"
    "doctor.toml" = "Diagnose and fix IPC issues"
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Updating Gemini CLI TOML Prompts" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

foreach ($fileName in $prompts.Keys) {
    $filePath = Join-Path $sourceDir $fileName
    $newPrompt = $prompts[$fileName]

    Write-Host "[UPDATING] $fileName" -ForegroundColor Yellow
    Write-Host "  New prompt: $newPrompt" -ForegroundColor Gray

    # Read file
    $content = Get-Content $filePath -Raw

    # Replace existing prompt line
    $content = $content -replace 'prompt\s*=\s*"[^"]*"', "prompt = ""$newPrompt"""

    # Write back
    Set-Content -Path $filePath -Value $content -NoNewline

    # Copy to target
    $targetFile = Join-Path $targetDir $fileName
    Copy-Item -Path $filePath -Destination $targetFile -Force

    Write-Host "  [OK] Updated and copied" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "All files updated successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n[VERIFICATION]" -ForegroundColor Yellow
foreach ($fileName in $prompts.Keys) {
    $targetFile = Join-Path $targetDir $fileName
    $content = Get-Content $targetFile -Raw
    if ($content -match 'prompt\s*=\s*"([^"]*)"') {
        Write-Host "  $fileName : $($matches[1])" -ForegroundColor White
    }
}

Write-Host "`n[NEXT STEPS]" -ForegroundColor Yellow
Write-Host "1. COMPLETELY close Gemini CLI (all windows)" -ForegroundColor White
Write-Host "2. Kill any background processes:" -ForegroundColor White
Write-Host "   taskkill /F /IM gemini.exe" -ForegroundColor Gray
Write-Host "3. Clear cache if exists:" -ForegroundColor White
Write-Host "   Remove-Item `"$env:USERPROFILE\.gemini\cache`" -Recurse -Force" -ForegroundColor Gray
Write-Host "4. Restart Gemini CLI fresh" -ForegroundColor White
Write-Host "5. Type / and check for /ipc: commands" -ForegroundColor White
Write-Host ""
