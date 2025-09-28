# Windows Terminal 4분할 IPC Interactive Clients 실행 스크립트

Write-Host "Starting Windows Terminal 4-split IPC Interactive Clients..." -ForegroundColor Green
Write-Host ""

# 작업 디렉토리 설정
$WorkDir = "D:\claude-ipc-mcp"
Set-Location $WorkDir

# 데이터베이스 초기화
Write-Host "Initializing database..." -ForegroundColor Yellow
python tools\ipc_manager.py init

# 인스턴스 등록
Write-Host "Registering instances..." -ForegroundColor Yellow
python tools\ipc_manager.py register claude
python tools\ipc_manager.py register gemini
python tools\ipc_manager.py register codex
python tools\ipc_manager.py register lm
Write-Host ""

# Windows Terminal 실행
$WtPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\wt.exe"

if (Test-Path $WtPath) {
    Write-Host "Starting Windows Terminal with 4 panes..." -ForegroundColor Green

    # Windows Terminal 2x2 분할 명령 구성
    # 레이아웃:
    # [claude] [gemini]
    # [codex ] [lm    ]
    $wtCommand = @"
$WtPath -w 0 nt --title "IPC 2x2" --startingDirectory "$WorkDir" -- cmd /c "python tools\interactive_client.py claude" `; ``
split-pane -H -s 0.5 --startingDirectory "$WorkDir" -- cmd /c "python tools\interactive_client.py gemini" `; ``
split-pane -V -t 0 -s 0.5 --startingDirectory "$WorkDir" -- cmd /c "python tools\interactive_client.py codex" `; ``
move-focus -t 1 `; ``
split-pane -V -s 0.5 --startingDirectory "$WorkDir" -- cmd /c "python tools\interactive_client.py lm"
"@

    # 명령 실행
    Invoke-Expression $wtCommand
}
else {
    Write-Host "Windows Terminal not found. Opening 4 separate windows..." -ForegroundColor Yellow

    # 4개의 별도 창으로 실행
    Start-Process cmd -ArgumentList "/k", "cd /d $WorkDir && python tools\interactive_client.py claude" -WindowStyle Normal
    Start-Sleep -Seconds 1

    Start-Process cmd -ArgumentList "/k", "cd /d $WorkDir && python tools\interactive_client.py gemini" -WindowStyle Normal
    Start-Sleep -Seconds 1

    Start-Process cmd -ArgumentList "/k", "cd /d $WorkDir && python tools\interactive_client.py codex" -WindowStyle Normal
    Start-Sleep -Seconds 1

    Start-Process cmd -ArgumentList "/k", "cd /d $WorkDir && python tools\interactive_client.py lm" -WindowStyle Normal
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Interactive clients started!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands in each terminal:" -ForegroundColor Yellow
Write-Host "  Register this instance as [name]   (Auto-registered)"
Write-Host "  Send message to [name]: [message]"
Write-Host "  Check messages"
Write-Host "  List instances"
Write-Host "  Help"
Write-Host "================================" -ForegroundColor Cyan