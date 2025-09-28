# IPC 환경 변수 설정 스크립트

# 현재 환경 변수 확인
Write-Host "===== 현재 환경 변수 확인 ====="
$currentIPC = [System.Environment]::GetEnvironmentVariable("IPC_BASE", "User")
$currentPython = [System.Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "IPC_BASE: $currentIPC"
Write-Host "PYTHONPATH: $currentPython"
Write-Host ""

# IPC_BASE 설정
Write-Host "===== IPC_BASE 설정 ====="
[System.Environment]::SetEnvironmentVariable("IPC_BASE", "D:\claude-ipc-mcp", "User")
Write-Host "✅ IPC_BASE = D:\claude-ipc-mcp"

# PYTHONPATH 설정
Write-Host ""
Write-Host "===== PYTHONPATH 설정 ====="
if ($currentPython) {
    # 기존 PYTHONPATH가 있고 IPC 경로가 없으면 추가
    if ($currentPython -notlike "*D:\claude-ipc-mcp*") {
        $newPythonPath = $currentPython + ";D:\claude-ipc-mcp"
        [System.Environment]::SetEnvironmentVariable("PYTHONPATH", $newPythonPath, "User")
        Write-Host "✅ PYTHONPATH에 D:\claude-ipc-mcp 추가됨"
    } else {
        Write-Host "⚠️ PYTHONPATH에 이미 IPC 경로가 있습니다"
    }
} else {
    # PYTHONPATH가 없으면 새로 생성
    [System.Environment]::SetEnvironmentVariable("PYTHONPATH", "D:\claude-ipc-mcp", "User")
    Write-Host "✅ PYTHONPATH = D:\claude-ipc-mcp"
}

# PATH 설정
Write-Host ""
Write-Host "===== PATH 설정 ====="
if ($currentPath -notlike "*D:\claude-ipc-mcp*") {
    $newPath = $currentPath + ";D:\claude-ipc-mcp;D:\claude-ipc-mcp\tools"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "✅ PATH에 다음 경로 추가됨:"
    Write-Host "   - D:\claude-ipc-mcp"
    Write-Host "   - D:\claude-ipc-mcp\tools"
} else {
    Write-Host "⚠️ PATH에 이미 IPC 경로가 있습니다"
}

# 현재 세션에도 적용
Write-Host ""
Write-Host "===== 현재 세션에 적용 ====="
$env:IPC_BASE = "D:\claude-ipc-mcp"
$env:PYTHONPATH = [System.Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "✅ 환경 변수가 설정되었습니다!"
Write-Host ""
Write-Host "===== 설정 확인 ====="
Write-Host "IPC_BASE: $env:IPC_BASE"
Write-Host "PYTHONPATH: $env:PYTHONPATH"
Write-Host ""
Write-Host "💡 새 터미널/PowerShell을 열어야 환경 변수가 완전히 적용됩니다."