# Gemini CLI IPC Commands Installation

이 디렉토리에는 Gemini CLI용 IPC slash 명령어들이 포함되어 있습니다.

## 설치 방법

### Windows (PowerShell)

```powershell
# Gemini commands 디렉토리 생성 (이미 존재할 수 있음)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\commands\ipc"

# 모든 TOML 파일 복사
Copy-Item "D:\claude-ipc-mcp\docs\gemini-commands\*.toml" "$env:USERPROFILE\.gemini\commands\ipc\"
```

### Linux/Mac (Bash)

```bash
# Gemini commands 디렉토리 생성
mkdir -p ~/.gemini/commands/ipc

# 모든 TOML 파일 복사
cp D:/claude-ipc-mcp/docs/gemini-commands/*.toml ~/.gemini/commands/ipc/
```

## 설치 확인

설치 후 Gemini를 재시작하고 `/ipc`를 입력하여 모든 IPC 명령어가 표시되는지 확인하세요.

## 사용 가능한 명령어 (25개)

### 핵심 명령어
- `/ipc/init` - 프로젝트 IPC 구조 초기화
- `/ipc/status` - IPC 시스템 상태 확인
- `/ipc/ping` - 브로커 연결 테스트
- `/ipc/register` - 인스턴스 등록
- `/ipc/doctor` - 시스템 진단

### 통신 명령어
- `/ipc/send` - 메시지 전송 (fire-and-forget)
- `/ipc/ask` - 메시지 전송 및 응답 대기
- `/ipc/check` - 새 메시지 확인
- `/ipc/broadcast` - 모든 인스턴스에 브로드캐스트
- `/ipc/list` - 모든 인스턴스 목록

### 브로커 관리
- `/ipc/broker-start` - 글로벌 브로커 시작
- `/ipc/broker-stop` - 글로벌 브로커 종료
- `/ipc/broker-status` - 브로커 상태 확인

### 인스턴스 관리
- `/ipc/instances-delete` - 특정 인스턴스 삭제
- `/ipc/instances-reset` - 모든 인스턴스 초기화

### 메시지 관리
- `/ipc/messages-clear` - 모든 메시지 삭제

### 세션 관리
- `/ipc/session` - 현재 세션 정보 표시
- `/ipc/session-clear` - 세션 데이터 삭제

### 자동 응답기
- `/ipc/responder-start` - 자동 응답기 시작
- `/ipc/responder-start-all` - 모든 응답기 시작
- `/ipc/responder-stop` - 자동 응답기 종료
- `/ipc/responder-stop-all` - 모든 응답기 종료
- `/ipc/responder-status` - 응답기 상태 확인

### 고급 기능
- `/ipc/setup` - 완전한 설정 마법사

## 환경 변수

Gemini CLI는 다음 환경 변수를 사용합니다:

```bash
IPC_CHAT=D:\claude-ipc-mcp  # IPC 프로젝트 경로
IPC_HOST=127.0.0.1          # 브로커 호스트
IPC_GLOBAL_PORT=9876        # 브로커 포트
```

PowerShell에서 설정:
```powershell
$env:IPC_CHAT="D:\claude-ipc-mcp"
```

## 주의사항

- 모든 명령어는 글로벌 IPC 브로커를 사용합니다 (포트 9876)
- IPC 작업 전에 브로커가 실행 중이어야 합니다
- 세션 토큰은 프로젝트 `.ipc/` 디렉토리에 저장됩니다
- 명령어는 자연어 매개변수를 지원합니다

## 문제 해결

명령어가 작동하지 않는 경우:

1. `IPC_CHAT` 환경 변수가 올바르게 설정되었는지 확인
2. 브로커가 실행 중인지 확인: `/ipc/broker-status`
3. Gemini를 재시작
4. 시스템 진단 실행: `/ipc/doctor`

## 관련 문서

- **완전한 명령어 참조**: `docs/IPC_COMPLETE_COMMAND_REFERENCE.md`
- **통합 요약**: `docs/IPC_CLI_INTEGRATION_SUMMARY.md`
- **CLI 명령어**: `docs/ipc_cli_commands.md`
