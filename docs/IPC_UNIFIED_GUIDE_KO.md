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

## 4) 유지보수/청소
```powershell
# 메시지 정리(멱등)
uv run python tools/ipc_global_command.py messages clear --force
# 인스턴스 세션 초기화/삭제(멱등)
uv run python tools/ipc_global_command.py instances reset
uv run python tools/ipc_global_command.py instances delete codex
# 진단
uv run python tools/ipc_global_command.py doctor
```

## 5) 정책/보안 팁
- 자동응답 정책: `IPC_RESPONDER_POLICY`(전역) 또는 `responder start --policy`(개별)
- 보안 비밀키(선택): `IPC_SHARED_SECRET`가 양쪽에서 동일해야 등록이 허용됩니다.

## 6) 자주 묻는 질문
- ipc 명령이 없을 때: `./ipc.bat` 또는 `uv run python tools/ipc_global_command.py` 사용
- 브로커 미응답: `tools/start_broker.py` 실행 또는 `ipc doctor`로 점검
- 포트 충돌: `ipc init --port <다른포트>`

## 7) 참고 문서
- `docs/ipc_cli_commands.md` — 통합 CLI 세부 사용법(한글)
- `specs/001-description-ipc-root/contracts/cli-contracts.md` — CLI 계약(출력/종료 코드)
- `docs/GLOBAL_USAGE_KO.md` — 전역 사용 가이드(한글)
- `TROUBLESHOOTING.md` — 문제 해결

---
이 가이드를 팀/조직의 표준 온보딩 문서로 사용하면, 어떤 프로젝트에서도 동일한 절차로 IPC 메시징을 시작할 수 있습니다. 🚀
