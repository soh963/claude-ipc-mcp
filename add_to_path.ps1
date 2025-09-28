# 현재 세션의 PATH에 IPC 경로 추가
$env:PATH += ";D:\claude-ipc-mcp;D:\claude-ipc-mcp\tools"

Write-Host "✅ PATH 업데이트 완료!" -ForegroundColor Green
Write-Host ""

# PATH 확인
Write-Host "현재 PATH에 IPC 경로 확인:" -ForegroundColor Cyan
if ($env:PATH -like "*claude-ipc-mcp*") {
    Write-Host "✅ IPC 경로가 PATH에 포함되었습니다" -ForegroundColor Green

    # PATH를 ;로 분리해서 IPC 관련 경로만 표시
    $paths = $env:PATH -split ';'
    $ipcPaths = $paths | Where-Object { $_ -like "*claude-ipc-mcp*" }

    Write-Host ""
    Write-Host "추가된 IPC 경로:" -ForegroundColor Yellow
    foreach ($path in $ipcPaths) {
        Write-Host "  - $path"
    }
} else {
    Write-Host "❌ IPC 경로가 PATH에 없습니다" -ForegroundColor Red
}

Write-Host ""
Write-Host "IPC 명령 테스트:" -ForegroundColor Cyan

# ipc.bat 파일 확인
if (Test-Path "D:\claude-ipc-mcp\ipc.bat") {
    Write-Host "✅ ipc.bat 파일 존재" -ForegroundColor Green

    # 현재 위치에서 ipc 명령 사용 가능한지 테스트
    try {
        $testOutput = & D:\claude-ipc-mcp\ipc.bat --help 2>&1
        if ($LASTEXITCODE -eq 0 -or $testOutput -like "*usage*") {
            Write-Host "✅ IPC 명령이 정상적으로 작동합니다" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️ IPC 명령 실행 중 오류가 발생했습니다" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ ipc.bat 파일을 찾을 수 없습니다" -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 팁: 새 터미널/PowerShell을 열면 영구적으로 적용됩니다" -ForegroundColor Magenta