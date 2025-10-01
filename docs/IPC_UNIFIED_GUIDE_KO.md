# IPC 통합 가이드 (한글)

이 문서는 프로젝트 전반의 "사용방법 순서"를 한 페이지에 통합합니다. 전역 설치부터 프로젝트별 실행, 통합 CLI, 자동응답기(Responder) 라이프사이클, 문제 해결까지 일관된 흐름으로 정리했습니다.

> 최신 변경 사항 요약 (2025-09-30)
> - ask: `--poll-interval`, `--corr` 옵션 추가, 기본 timeout 10초
> - responder status: `started_at`, `last_check_at`, `last_response_at`, `policy` 필드 노출
> - 메시지/인스턴스 관리: `messages clear --force`, `instances reset/delete` 멱등 처리

## 1) 전역 설치(1회)
- 요구 사항: Windows + PowerShell, Python 3.12+, Git, UV
- 설치:
  - 저장소 클론: `git clone https://github.com/soh963/claude-ipc-mcp.git`
  - 의존성 설치: `uv sync`
- (선택) PATH/프로필 통합: `scripts/install-global.ps1` 실행

## 2) 프로젝트 최초 세팅(반복)
```powershell
# 프로젝트 폴더에서
uv run python tools/ipc_global_command.py init
uv run python tools/ipc_global_command.py status
uv run python tools/ipc_global_command.py ping
```

## 3) 메시징과 자동응답(핵심)
- 단발 질문/응답(ask):
```powershell
uv run python tools/ipc_global_command.py ask --to gemini "상태 어때?" --timeout 10 --poll-interval 0.1
uv run python tools/ipc_global_command.py ask --to gemini --corr my-123 "테스트"
```
- 자동응답기(Responder):
```powershell
# 시작
uv run python tools/ipc_global_command.py responder start gemini --policy smart --detach
# 상태(JSON)
uv run python tools/ipc_global_command.py responder status gemini
# 중지
uv run python tools/ipc_global_command.py responder stop gemini
```
- 상태 파일(모니터링): `%USERPROFILE%\.claude-ipc-data\responders\<instance>.json`
  - 필드: started_at, last_check_at, last_response_at, policy

## 3.5) AI CLI 간 통신 시나리오

### 개념 이해
IPC(Inter-Process Communication)는 여러 AI 인스턴스(Claude, Gemini, Codex 등)가 서로 메시지를 주고받을 수 있게 해주는 시스템입니다. 중앙 브로커가 메시지를 중계하며, 각 AI는 고유한 인스턴스 ID로 등록됩니다.

### 시나리오 1: 인스턴스 등록
각 AI CLI는 브로커에 등록되어야 통신할 수 있습니다.

```powershell
# 기본 등록 (config 파일의 instance_id 사용)
ipc register

# 커스텀 ID로 등록 (다른 AI CLI에서 사용)
ipc register codex      # Codex AI를 'codex'로 등록
ipc register gemini     # Gemini AI를 'gemini'로 등록
ipc register cursor     # Cursor AI를 'cursor'로 등록

# 등록 확인
ipc instances list --full
```

**출력 예시:**
```
📊 Unified Instance Status (3 instance(s)):

  Instance: claude
    Broker:    ✓ Registered
    Responder: ✗ Not running

  Instance: codex
    Broker:    ✓ Registered
    Responder: ✗ Not running

  Instance: gemini
    Broker:    ✓ Registered
    Responder: ✓ Running
      PID: 12345
      Policy: smart
```

### 시나리오 2: 단방향 메시지 전송
한 AI가 다른 AI에게 메시지를 보냅니다 (응답 대기 안함).

```powershell
# Claude에서 Gemini로 메시지 전송
ipc chat --to gemini "프로젝트 빌드 완료했어"

# Codex에서 Claude로 코드 리뷰 요청
ipc chat --to claude "이 파일 리뷰 부탁: src/main.py"

# Gemini에서 모든 인스턴스에 브로드캐스트 (수동)
ipc chat --to claude "업데이트 완료"
ipc chat --to codex "업데이트 완료"
```

**출력 예시:**
```
to=gemini correlation=corr-74882 sent
```

### 시나리오 3: 양방향 통신 (ask 명령어)
메시지를 보내고 응답을 기다립니다. 상대방에 자동응답기가 실행 중이어야 합니다.

```powershell
# Gemini에 질문하고 10초 동안 응답 대기
ipc ask --to gemini "현재 작업 상태 알려줘" --timeout 10

# Codex에 빠른 질문 (0.1초마다 폴링)
ipc ask --to codex "테스트 통과했어?" --timeout 5 --poll-interval 0.1

# 상관관계 ID 지정 (요청 추적용)
ipc ask --to gemini --corr build-123 "빌드 결과 확인"
```

**출력 예시:**
```
✅ Sent message to gemini
⏳ Waiting for response (timeout: 10s)...
💬 Response from gemini: "작업 진행 중이야. 80% 완료됐어."
```

### 시나리오 4: 자동응답기 설정
특정 인스턴스가 자동으로 메시지에 응답하도록 설정합니다.

```powershell
# Gemini에 스마트 자동응답기 시작
ipc responder start gemini --policy smart --detach

# 모든 등록된 인스턴스에 자동응답기 시작
ipc responder start-all --policy smart

# 자동응답기 상태 확인
ipc responder status gemini

# 특정 자동응답기 중지
ipc responder stop gemini

# 모든 자동응답기 중지
ipc responder stop-all
```

**자동응답 정책:**
- `simple`: 받은 메시지를 그대로 에코 (테스트용)
- `smart`: 컨텍스트 인식 응답 (프로덕션용)

### 시나리오 5: 실전 워크플로우

**시나리오 A: 코드 리뷰 협업**
```powershell
# 1. Claude가 코드 작성 완료 후 Codex에 리뷰 요청
ipc chat --to codex "src/api/auth.py 리뷰 부탁"

# 2. Codex가 자동응답기로 리뷰 결과 전송 (백그라운드)
# (Codex에서 자동응답기가 실행 중이면 자동으로 응답)

# 3. Claude가 Codex의 피드백 확인
ipc ask --to codex "리뷰 완료됐어?" --timeout 30
```

**시나리오 B: 프로젝트 빌드 알림**
```powershell
# 1. CI/CD에서 Gemini가 빌드 시작 알림
ipc chat --to claude "프로젝트 빌드 시작"
ipc chat --to codex "프로젝트 빌드 시작"

# 2. 빌드 완료 후 결과 공유
ipc chat --to claude "빌드 성공: v1.2.3"
ipc chat --to codex "빌드 성공: v1.2.3"
```

**시나리오 C: 실시간 협업**
```powershell
# 터미널 1 (Claude)
ipc responder start claude --policy smart --detach
ipc ask --to gemini "현재 작업 상태는?" --timeout 10

# 터미널 2 (Gemini)
ipc responder start gemini --policy smart --detach
# 자동으로 Claude의 질문에 응답
```

### 주요 명령어 요약

| 명령어 | 용도 | 예시 |
|--------|------|------|
| `ipc register <id>` | AI 인스턴스 등록 | `ipc register codex` |
| `ipc instances list --full` | 등록된 인스턴스 확인 | - |
| `ipc chat --to <id> <msg>` | 단방향 메시지 전송 | `ipc chat --to gemini "안녕"` |
| `ipc ask --to <id> <msg>` | 양방향 통신 (응답 대기) | `ipc ask --to gemini "상태는?"` |
| `ipc responder start <id>` | 자동응답기 시작 | `ipc responder start gemini` |
| `ipc responder status <id>` | 자동응답기 상태 확인 | `ipc responder status gemini` |
| `ipc responder stop <id>` | 자동응답기 중지 | `ipc responder stop gemini` |
| `ipc responder start-all` | 모든 자동응답기 시작 | - |
| `ipc responder stop-all` | 모든 자동응답기 중지 | - |

### 환경 변수

```powershell
# 브로커 호스트/포트
set IPC_HOST=127.0.0.1
set IPC_GLOBAL_PORT=9876

# 자동응답기 기본 정책
set IPC_RESPONDER_POLICY=smart

# 보안 인증 (선택사항)
set IPC_SHARED_SECRET=your-secret-key
```

### 문제 해결

**"인스턴스를 찾을 수 없습니다"**
```powershell
# 인스턴스 등록 확인
ipc instances list --full

# 미등록 시 등록
ipc register <instance-id>
```

**"브로커에 연결할 수 없습니다"**
```powershell
# 브로커 상태 확인
ipc status

# 브로커 시작
ipc broker start
```

**"응답 시간 초과"**
- 상대방 인스턴스에 자동응답기가 실행 중인지 확인
- `--timeout` 값을 늘려서 재시도
- 상대방 인스턴스가 브로커에 등록되어 있는지 확인

## 3.6) 브로커 실행(필수 아닐 때가 많음)
- 보통은 `status`/`ping`으로 응답이 오면 브로커가 이미 동작 중이라 별도 실행이 필요 없습니다. 미응답일 때 아래 순서로 점검/실행하세요.

1) 상태 확인(우선)
```powershell
uv run python tools/ipc_global_command.py status
uv run python tools/ipc_global_command.py ping
ipc broker status
```

2) 전역 명령으로 실행(권장)
```powershell
ipc broker start
```

3) 스크립트로 직접 실행(레거시/대안)
```powershell
uv run python tools/start_broker.py
```

4) 서버 엔트리로 실행
```powershell
uv run python src/claude_ipc_server.py
```

5) 배치/일괄 스크립트(Windows)
```powershell
./start_ipc_system.bat
# 또는 도구/응답기까지 포함
uv run python .\start_all_ai_ipc.py
```

실행 후 검증:
```powershell
uv run python tools/ipc_global_command.py status
uv run python tools/ipc_global_command.py ping
ipc broker status
```

문제 해결 팁:
- 포트 충돌 시: `init --port <다른포트>`로 재초기화 후 재시도
- 로그 확인: `logs/` 폴더
- 자동 점검: `uv run python tools/ipc_global_command.py doctor`

## 4) 유지보수/청소

### 메시지 관리
```powershell
# 모든 메시지 삭제 (확인 없이 강제 실행)
ipc messages clear --force

# 진단 도구로 시스템 상태 점검
ipc doctor
```

### 인스턴스 관리

#### 모든 인스턴스 삭제
브로커에 등록된 모든 인스턴스를 삭제합니다.

```powershell
# 모든 인스턴스 삭제 (세션 초기화)
ipc instances reset
```

**사용 시나리오:**
- 개발 환경 초기화
- 테스트 후 정리 작업
- 시스템 완전 재설정

**주의사항:**
- ⚠️ 모든 등록된 인스턴스가 삭제됩니다
- 실행 중인 자동응답기는 자동으로 중지되지 않으므로 별도로 중지 필요
- 메시지는 삭제되지 않고 인스턴스 세션만 삭제됨

**출력 예시:**
```
✅ Reset 7 instance(s)
```

#### 특정 인스턴스 삭제
특정 인스턴스만 선택적으로 삭제합니다.

```powershell
# 특정 인스턴스 삭제
ipc instances delete codex
ipc instances delete test-instance
```

**사용 시나리오:**
- 특정 AI CLI만 재등록이 필요할 때
- 테스트용 임시 인스턴스 제거
- 더 이상 사용하지 않는 인스턴스 정리

**주의사항:**
- 해당 인스턴스로 전송된 메시지는 삭제되지 않음
- 자동응답기가 실행 중이면 별도로 중지 필요
- 삭제 후 재등록하려면 `ipc register <id>` 실행

**출력 예시:**
```
✅ Deleted instance 'codex'
```

#### 인스턴스 삭제 vs 리셋

| 명령어 | 대상 | 용도 | 메시지 영향 |
|--------|------|------|------------|
| `ipc instances reset` | 모든 인스턴스 | 전체 시스템 초기화 | 메시지 유지 |
| `ipc instances delete <id>` | 특정 인스턴스 | 선택적 제거 | 메시지 유지 |
| `ipc messages clear --force` | - | 메시지 삭제 | 모든 메시지 삭제 |

#### 완전 초기화 워크플로우
시스템을 완전히 초기화하려면:

```powershell
# 1. 모든 자동응답기 중지
ipc responder stop-all

# 2. 모든 인스턴스 삭제
ipc instances reset

# 3. 모든 메시지 삭제
ipc messages clear --force

# 4. 시스템 상태 확인
ipc status

# 5. 필요 시 브로커 재시작
ipc broker stop
ipc broker start
```

## 5) 정책/보안 팁
- 자동응답 정책: `IPC_RESPONDER_POLICY`(전역) 또는 `responder start --policy`(개별)
- 보안 비밀키(선택): `IPC_SHARED_SECRET`가 양쪽에서 동일해야 등록이 허용됩니다.

## 6) 자주 묻는 질문
- ipc 명령이 없을 때: `./ipc.bat` 또는 `uv run python tools/ipc_global_command.py` 사용
- 브로커 미응답: `ipc broker start`로 재기동하거나 `ipc doctor`로 점검
- 포트/호스트 제어: `IPC_HOST`, `IPC_GLOBAL_PORT`(또는 `IPC_PORT`) 환경변수로 조정 가능. 클라이언트/런처가 동일 설정을 사용합니다.
- 포트 충돌: `ipc init --port <다른포트>`

## 7) 참고 문서
- `docs/ipc_cli_commands.md` — 통합 CLI 세부 사용법(한글)
- `specs/001-description-ipc-root/contracts/cli-contracts.md` — CLI 계약(출력/종료 코드)
- `docs/GLOBAL_USAGE_KO.md` — 전역 사용 가이드(한글)
- `TROUBLESHOOTING.md` — 문제 해결

---
이 가이드를 팀/조직의 표준 온보딩 문서로 사용하면, 어떤 프로젝트에서도 동일한 절차로 IPC 메시징을 시작할 수 있습니다. 🚀
