# IPC Wrapper 사용 가이드

Codex CLI는 커스텀 slash command를 지원하지 않기 때문에, 터미널에서 쉽게 IPC를 사용할 수 있는 wrapper 스크립트를 제공합니다.

## 설치 방법

### 1. Bash/Git Bash 사용자

`~/.bashrc` 또는 `~/.bash_profile`에 다음 줄 추가:

```bash
alias ipc='/d/claude-ipc-mcp/scripts/ipc-wrapper.sh'
```

터미널 재시작 또는:
```bash
source ~/.bashrc
```

### 2. PowerShell 사용자

`$PROFILE` 파일에 다음 줄 추가:

```powershell
Set-Alias -Name ipc -Value 'D:\claude-ipc-mcp\scripts\ipc-wrapper.bat'
```

터미널 재시작 또는:
```powershell
. $PROFILE
```

### 3. Alias 없이 직접 사용

```bash
# Bash/Git Bash
/d/claude-ipc-mcp/scripts/ipc-wrapper.sh <command>

# PowerShell/CMD
D:\claude-ipc-mcp\scripts\ipc-wrapper.bat <command>
```

## 사용법

### 📊 상태 확인
```bash
ipc status
```

브로커 연결 상태와 등록된 인스턴스 확인

### 📝 인스턴스 등록
```bash
ipc register my-instance
```

현재 터미널/프로젝트를 IPC 인스턴스로 등록

### 👥 인스턴스 목록 보기
```bash
ipc list
```

모든 활성 인스턴스와 자동응답 상태 확인

### 💬 메시지 보내기 (Fire and Forget)
```bash
ipc send gemini "빌드 완료했어요"
```

다른 인스턴스에게 메시지 전송 (응답 대기 안 함)

### 💬 메시지 보내고 응답 대기
```bash
ipc ask gemini "테스트 결과 어때?"
```

메시지 전송 후 10초간 응답 대기

### 📬 메시지 확인
```bash
ipc check
```

받은 메시지 목록 확인

### 🤖 자동응답 시작
```bash
ipc responder-start gemini
```

gemini 인스턴스에 대한 자동응답 프로세스 시작

### 📊 자동응답 상태 확인
```bash
ipc responder-status gemini
```

자동응답 프로세스가 실행 중인지 확인

### 🛑 자동응답 정지
```bash
ipc responder-stop gemini
```

자동응답 프로세스 종료

### 🏥 진단 및 수정
```bash
ipc doctor
```

IPC 시스템 상태 진단 및 자동 수정

## 실전 시나리오

### 시나리오 1: 기본 설정 및 메시지 교환

```bash
# 1. 상태 확인
ipc status

# 2. 현재 터미널을 'my-terminal'로 등록
ipc register my-terminal

# 3. gemini에게 메시지 전송
ipc send gemini "안녕하세요, 테스트 메시지입니다"

# 4. 응답 대기하며 질문
ipc ask gemini "현재 작업 상태는?"
```

### 시나리오 2: 자동응답 설정

```bash
# 1. gemini 인스턴스에 자동응답 시작
ipc responder-start gemini

# 2. 자동응답 상태 확인
ipc responder-status gemini

# 3. gemini에게 메시지 보내면 자동으로 응답 받음
ipc ask gemini "준비됐어?"

# 4. 작업 완료 후 자동응답 정지
ipc responder-stop gemini
```

### 시나리오 3: 팀 협업 워크플로

```bash
# Terminal 1 (Claude)
ipc register claude-main
ipc responder-start claude-main

# Terminal 2 (Gemini)
ipc register gemini-worker
ipc responder-start gemini-worker

# Terminal 3 (Coordinator)
ipc register coordinator
ipc ask claude-main "프론트엔드 작업 시작해줘"
ipc ask gemini-worker "백엔드 API 작업 시작해줘"

# 작업 완료 확인
ipc list
```

## 문제 해결

### Wrapper 실행이 안 됨
```bash
# 실행 권한 확인 (Bash)
chmod +x /d/claude-ipc-mcp/scripts/ipc-wrapper.sh

# 직접 경로로 실행 테스트
/d/claude-ipc-mcp/scripts/ipc-wrapper.sh status
```

### Broker 연결 실패
```bash
# 진단 실행
ipc doctor

# 수동으로 브로커 시작
cd /d/claude-ipc-mcp
uv run python tools/start_broker.py
```

### "command not found" 에러
```bash
# Alias 설정 확인
alias | grep ipc

# Alias 재설정
source ~/.bashrc  # Bash
. $PROFILE        # PowerShell
```

## Codex CLI vs IPC Wrapper 비교

| 기능 | Codex CLI | IPC Wrapper |
|------|-----------|-------------|
| Slash Command | `/mcp`, `/status` 등 내장 명령만 | `ipc <command>` 형태로 모든 IPC 명령 사용 |
| 사용 방법 | Codex 실행 후 내부에서 사용 | 터미널에서 직접 사용 가능 |
| 자동완성 | 없음 | Bash/PowerShell 자동완성 가능 |
| 스크립팅 | 어려움 | 쉽게 스크립트 작성 가능 |

## 고급 사용법

### Bash 스크립트에서 사용

```bash
#!/bin/bash

# 자동 빌드 및 알림 스크립트
echo "Building project..."
npm run build

if [ $? -eq 0 ]; then
    ipc send team "✅ Build successful!"
else
    ipc send team "❌ Build failed!"
fi
```

### PowerShell 스크립트에서 사용

```powershell
# 자동 테스트 및 알림 스크립트
Write-Host "Running tests..."
npm test

if ($LASTEXITCODE -eq 0) {
    ipc send team "✅ All tests passed!"
} else {
    ipc send team "❌ Tests failed!"
}
```

## 추가 정보

- 모든 IPC 명령은 `uv run python tools/ipc_global_command.py`를 통해 실행됩니다
- Wrapper는 명령어를 단순화하고 사용성을 향상시킵니다
- 원본 Python 명령어로도 동일한 작업 수행 가능

## 참고 문서

- [IPC 통합 가이드](IPC_UNIFIED_GUIDE_KO.md)
- [CLI 명령어 레퍼런스](ipc_cli_commands.md)
- [Codex CLI 설정](CODEX_CLI_SETUP.md)
