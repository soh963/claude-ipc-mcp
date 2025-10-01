# IPC Cross-CLI Integration - Final Agreement

## 문제 정의

- Gemini CLI와 Codex CLI는 `ipc` 명령을 로컬 파일로 매핑하려고 시도하여 MCP 툴을 인식하지 못함
- 동일한 브로커에 연결해도 각 CLI가 다른 인스턴스 목록을 보고함
- 자동 응답(Responder) 활성화가 수동 작업으로 번거로움

## 최종 합의 사항 ✅

### 1. 글로벌 슬래시 명령어 표준화

**모든 CLI에서 `/ipc:*` 명령어 통일 사용**

| 명령어 | 기능 | 구현 상태 |
|--------|------|-----------|
| `/ipc:setup` | 원클릭 온보딩 (등록+자동응답) | ✅ Claude, 🔄 Gemini, 🔄 Codex |
| `/ipc:status` | 연결 상태 확인 | ✅ Claude, 🔄 Gemini, 🔄 Codex |
| `/ipc:list` | 인스턴스 목록 조회 | ✅ Claude, 🔄 Gemini, 🔄 Codex |
| `/ipc:send` | 메시지 전송 | ✅ Claude, 🔄 Gemini, 🔄 Codex |
| `/ipc:check` | 메시지 확인 | ✅ Claude, 🔄 Gemini, 🔄 Codex |
| `/ipc:doctor` | 문제 진단 및 수정 | ✅ Claude, 🔄 Gemini, 🔄 Codex |

### 2. 글로벌 설치 경로

**모든 프로젝트와 세션에서 사용 가능하도록 전역 설치**

- **Claude Code**: `%USERPROFILE%\.claude\commands\ipc\*.md`
- **Gemini CLI**: `%USERPROFILE%\.gemini\commands\ipc\*.toml`
- **Codex CLI**: `%USERPROFILE%\.codex\config.toml` + `AGENTS.md`

### 3. 단일 데이터베이스 사용

**모든 CLI가 동일한 DB 참조하여 인스턴스 목록 일치 보장**

```bash
# 환경 변수 설정 (모든 CLI 공통)
IPC_DB_PATH=%USERPROFILE%\.claude-ipc-data\messages.db
IPC_HOST=127.0.0.1
IPC_GLOBAL_PORT=9876
IPC_CHAT=D:\claude-ipc-mcp  # 프로젝트 경로
```

### 4. 자동 응답 기본 활성화

**`/ipc:setup` 실행 시 자동으로 responder 시작**

```bash
# 모든 CLI 동일한 동작
/ipc:setup myname
→ 브로커 시작 → 등록 → 세션 저장 → 자동응답 활성화 → 연결 테스트
```

## CLI별 구현 세부사항

### Gemini CLI (TOML 형식)

```toml
# %USERPROFILE%\.gemini\commands\ipc\setup.toml
[command]
name = "ipc:setup"
description = "🚀 Complete IPC setup (register + auto-responder)"
category = "ipc"

[command.parameters]
instance_name = { type = "string", required = true, prompt = "Enter instance name:" }

[command.execution]
type = "shell"
command = "uv run python %IPC_CHAT%\\tools\\ipc_onboard.py --name {instance_name} --policy smart"
working_directory = "%IPC_CHAT%"
```

**Gemini 팀 공식 답변**:
- ✅ TOML 기반 구조 확인 완료
- ✅ 전역 설치 방식 동의
- ✅ 백그라운드 responder 실행 동의 (리소스 제한 및 재시작 메커니즘 필요)
- ✅ JSON 형식 상태 출력 선호

### Codex CLI (config.toml + AGENTS.md)

```toml
# %USERPROFILE%\.codex\config.toml
[slash_commands]
"ipc:setup" = { 
  command = "uv run python %IPC_CHAT%\\tools\\ipc_onboard.py --name {args[0]} --policy smart", 
  description = "🚀 Complete IPC setup" 
}
"ipc:status" = { 
  command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py status --json", 
  description = "📊 Check IPC status" 
}
```

**Codex 팀 공식 답변**:
- ✅ 다음 스프린트에서 `/ipc-*` 명령어 기본 번들 포함
- ✅ JSON 출력만 신뢰 원천으로 사용, 캐시 제거
- ✅ MCP 설정 파일: `%APPDATA%\Codex\settings.json`
- ✅ PowerShell 실행 정책 체크 추가 예정
- 📅 2월 1주차: Slash 명령 배포 완료 목표
- 📅 2월 2주차: `ipc doctor` 개선 반영 예정

## 설치 방법

### 자동 설치 (권장)

```powershell
# Windows - 모든 CLI 한번에 설치
cd D:\claude-ipc-mcp
.\scripts\install-all-clis.bat

# Linux/macOS
cd ~/claude-ipc-mcp
./scripts/install-all-clis.sh
```

### 개별 설치

```powershell
# Claude Code만
.\scripts\install-slash-commands.bat
→ [1] User-wide 선택

# Gemini CLI만
.\scripts\install-slash-commands-gemini.bat global

# Codex CLI만
.\scripts\install-slash-commands-codex.bat global
```

### 설치 검증

```powershell
# 설치 확인
.\scripts\verify-global-installation.ps1

# CLI 재시작 후 테스트
/ipc:setup test-instance
/ipc:status
/ipc:list
```

## 사용 예제

### 크로스 CLI 통신

```bash
# Claude Code
/ipc:setup claude-main
/ipc:send claude-main gemini-worker "Can you review the API design?"

# Gemini CLI
/ipc:setup gemini-worker
/ipc:check gemini-worker
→ 📬 "Can you review the API design?" from claude-main

/ipc:send gemini-worker codex-tester "Generate API tests"

# Codex CLI
/ipc:setup codex-tester
/ipc:check codex-tester
→ 📬 "Generate API tests" from gemini-worker

/ipc:send codex-tester claude-main "Tests complete"

# Claude Code
/ipc:check claude-main
→ 📬 "Tests complete" from codex-tester
```

## 문제 해결

### 브로커 연결 실패
```bash
/ipc:doctor
→ 자동으로 브로커 시작, DB 경로 수정, 권한 설정
```

### 인스턴스 목록 불일치
```bash
# 환경 변수 확인
echo %IPC_DB_PATH%
→ C:\Users\username\.claude-ipc-data\messages.db

# 모든 CLI에서 동일한 경로 사용 확인
```

### 자동 응답 미작동
```bash
/ipc:responder-status myname
→ PID, 정책, 마지막 활동 시간 확인

/ipc:responder-start myname smart
→ 수동 재시작
```

## 다음 단계

### 즉시 구현 필요 (Priority 1)
- [ ] Gemini용 TOML 파일 9개 생성
- [ ] Codex용 config.toml 템플릿 생성
- [ ] `install-all-clis.bat/sh` 스크립트 실제 구현
- [ ] `verify-global-installation.ps1` 검증 스크립트 구현

### 2월 1주차 목표 (Codex 팀과 동기화)
- [ ] Codex CLI에 `/ipc-*` 명령어 배포
- [ ] Gemini CLI 슬래시 명령어 설치 테스트
- [ ] 크로스 CLI 통신 E2E 테스트

### 2월 2주차 목표
- [ ] `ipc doctor` 개선 (3개 CLI 통합 진단)
- [ ] 공식 문서 작성 (`docs/platform-guides/CROSS_CLI_IPC.md`)
- [ ] 설치 가이드 및 트러블슈팅 완성

## 참고 문서

- **Claude Code 구현**: `docs/platform-guides/CLAUDE_CODE_SETUP.md`
- **통합 CLI 가이드**: `docs/IPC_UNIFIED_GUIDE_KO.md`
- **설치된 스크립트**: `scripts/install-slash-commands.*`
- **온보딩 도구**: `tools/ipc_onboard.py`
