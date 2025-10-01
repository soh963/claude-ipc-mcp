# Claude Code Slash Commands Guide

Claude Code CLI에서 IPC 명령을 slash command로 사용하는 가이드입니다.

## 설치 방법

### Windows (PowerShell)

```powershell
cd D:\claude-ipc-mcp
.\scripts\install-claude-code-slash-commands.ps1
```

### Linux/Mac (Bash)

```bash
cd /path/to/claude-ipc-mcp
bash scripts/install-claude-code-slash-commands.sh
```

설치 후 **Claude Code를 재시작**해야 새로운 slash command가 활성화됩니다.

## 사용 가능한 Slash Commands

### 📊 상태 확인

#### `/ipc-status`
브로커 연결 상태 확인
```
/ipc-status
```

#### `/ipc-ping`
브로커와의 연결 테스트
```
/ipc-ping
```

### 📝 인스턴스 관리

#### `/ipc-register`
현재 인스턴스를 IPC 시스템에 등록
```
/ipc-register my-instance-name
```

#### `/ipc-list`
등록된 모든 인스턴스 목록 보기
```
/ipc-list
```

#### `/ipc-rename`
인스턴스 이름 변경 (rate limited: 1시간에 1회)
```
/ipc-rename old-name new-name
```

### 💬 메시지 전송

#### `/ipc-send`
다른 인스턴스에게 메시지 전송 (응답 대기 안 함)
```
/ipc-send target-instance "안녕하세요!"
```

#### `/ipc-ask`
메시지 전송 후 10초간 응답 대기
```
/ipc-ask gemini "현재 작업 상태 알려줘"
```

#### `/ipc-broadcast`
모든 인스턴스에게 메시지 전송
```
/ipc-broadcast "빌드가 완료되었습니다"
```

### 📬 메시지 확인

#### `/ipc-check`
받은 메시지 확인
```
/ipc-check
```

### 🤖 자동응답 관리

#### `/ipc-responder-start`
인스턴스에 대한 자동응답 프로세스 시작
```
/ipc-responder-start gemini
```

#### `/ipc-responder-status`
자동응답 프로세스 상태 확인
```
/ipc-responder-status gemini
```

#### `/ipc-responder-stop`
자동응답 프로세스 정지
```
/ipc-responder-stop gemini
```

### 🚀 프로젝트 설정

#### `/ipc-init`
현재 프로젝트에 IPC 초기화 (`.ipc/` 디렉토리 생성)
```
/ipc-init
```

#### `/ipc-setup`
완전한 IPC 설정 (등록 + 자동응답 시작)
```
/ipc-setup my-instance
```

### 🏥 진단 및 수정

#### `/ipc-doctor`
IPC 시스템 진단 및 자동 수정
```
/ipc-doctor
```

## 사용 예시

### 시나리오 1: 기본 설정 및 메시지 교환

```bash
# 1. 브로커 상태 확인
/ipc-status

# 2. 현재 인스턴스 등록
/ipc-register claude-main

# 3. 다른 인스턴스 목록 확인
/ipc-list

# 4. gemini에게 메시지 전송
/ipc-send gemini "프론트엔드 작업 시작했어"

# 5. 메시지 확인
/ipc-check

# 6. 응답 대기하며 질문
/ipc-ask gemini "백엔드 API 준비됐어?"
```

### 시나리오 2: 자동응답 설정

```bash
# 1. gemini 인스턴스에 자동응답 시작
/ipc-responder-start gemini

# 2. 자동응답 상태 확인
/ipc-responder-status gemini

# 3. gemini에게 메시지 (자동으로 응답 받음)
/ipc-ask gemini "준비됐어?"

# 4. 작업 완료 후 자동응답 정지
/ipc-responder-stop gemini
```

### 시나리오 3: 팀 협업 워크플로

```bash
# Claude Code 인스턴스 1
/ipc-setup claude-frontend

# Claude Code 인스턴스 2
/ipc-setup claude-backend

# Coordinator
/ipc-register coordinator
/ipc-ask claude-frontend "UI 컴포넌트 작업 시작해줘"
/ipc-ask claude-backend "API 엔드포인트 작업 시작해줘"
```

## 문제 해결

### Slash Command가 보이지 않음

1. Claude Code 완전 재시작
2. 설치 스크립트 재실행
3. `~/.claude/commands/` 디렉토리에 JSON 파일들이 있는지 확인

```bash
ls -la ~/.claude/commands/ipc-*.json
```

### 명령 실행 시 에러

1. 브로커가 실행 중인지 확인: `/ipc-status`
2. uv와 Python이 설치되어 있는지 확인
3. 프로젝트 경로가 올바른지 확인

### "command not found" 에러

설치 스크립트의 `PROJECT_ROOT` 경로가 올바른지 확인:
```bash
cat ~/.claude/commands/ipc-status.json
```

경로가 잘못되었다면 설치 스크립트를 올바른 프로젝트 디렉토리에서 다시 실행하세요.

## vs IPC Wrapper

| 기능 | Claude Code Slash Commands | IPC Wrapper (터미널) |
|------|---------------------------|---------------------|
| 사용 위치 | Claude Code 내부 | 터미널 (Bash/PowerShell) |
| 명령 형식 | `/ipc-status` | `ipc status` |
| 자동완성 | Claude Code 지원 | Shell 자동완성 |
| 스크립팅 | 제한적 | 쉽게 스크립트 작성 가능 |
| 설치 | JSON 파일 생성 | Alias 설정 |

두 가지 방법 모두 사용 가능하며, Claude Code 내부에서는 slash command가, 터미널에서는 wrapper가 더 편리합니다.

## 참고 문서

- [IPC Wrapper Guide](IPC_WRAPPER_GUIDE.md) - 터미널 사용 가이드
- [IPC Unified Guide (Korean)](IPC_UNIFIED_GUIDE_KO.md) - 통합 가이드
- [CLI Commands Reference](ipc_cli_commands.md) - 명령어 레퍼런스
