# PowerShell script to restart broker
Write-Host "Stopping broker..."

# Read PID from lock file
$lockFile = "$env:USERPROFILE\.claude-ipc-data\broker.lock"
if (Test-Path $lockFile) {
    $pid = Get-Content $lockFile
    Write-Host "Killing process $pid..."
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start new broker
Write-Host "Starting new broker..."
$brokerScript = "D:\claude-ipc-mcp\src\claude_ipc_server.py"
$logFile = "D:\claude-ipc-mcp\broker.log"

# Start broker in background
$process = Start-Process python -ArgumentList $brokerScript -PassThru -WindowStyle Hidden
Out-File -FilePath $logFile -InputObject "Broker started with PID: $($process.Id)" -Encoding UTF8

Write-Host "Broker started with PID: $($process.Id)"
Write-Host "Waiting for broker to initialize..."
Start-Sleep -Seconds 5

# Test status
Write-Host "Testing broker status..."
python -c "import sys; sys.path.insert(0, 'D:/claude-ipc-mcp/src'); from core import broker_client; import json; print(json.dumps(broker_client.status(), indent=2))"