# ================================================================
#  UNIFIED IPC SYSTEM LAUNCHER (PowerShell)
#  모든 인스턴스 등록 + 자동응답 실행
# ================================================================

Write-Host @"
╔══════════════════════════════════════════════════════════╗
║     UNIFIED IPC SYSTEM WITH AUTO-RESPONDERS             ║
║                                                          ║
║  Starting all instances with auto-responders...         ║
╚══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Change to the correct directory
Set-Location -Path "D:\claude-ipc-mcp"

# Start the unified system
try {
    python start_all_instances_with_autoresponder.py

    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Error occurred while running the IPC system" -ForegroundColor Red
        Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit $LASTEXITCODE
    }
}
catch {
    Write-Host "`n❌ Exception occurred: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Keep window open
Read-Host "`nPress Enter to exit"