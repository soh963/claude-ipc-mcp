# Codex CLI Slash Commands - 문제 해결 완료

## 문제 발견

Codex CLI에서 IPC slash 명령어가 작동하지 않는 문제가 있었습니다:

```bash
codex: /ipc:status
error: unrecognized arguments: --json
```

## 근본 원인

`~/.codex/config.toml`의 slash 명령어가 지원하지 않는 `--json` 플래그를 사용하고 있었습니다:

```toml
# ❌ 잘못된 설정 (before)
[slash_commands."ipc:status"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py status --json"

# ❌ 다른 문제들
[slash_commands."ipc:list"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py instances --format json"

[slash_commands."ipc:check"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py messages check --instance {args[0]} --json"
```

## 해결 방법

### 1. 지원하지 않는 `--json` 플래그 제거

```toml
# ✅ 수정된 설정 (after)
[slash_commands."ipc:status"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py status"

[slash_commands."ipc:responder-status"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py responder status {args[0]}"

[slash_commands."ipc:responder-stop"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py responder stop {args[0]}"

[slash_commands."ipc:doctor"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_doctor.py --auto-fix"
```

### 2. 잘못된 하위 명령어 수정

```toml
# ✅ instances 명령어 수정
[slash_commands."ipc:list"]
command = "uv run python %IPC_CHAT%\\tools\\ipc_global_command.py instances list --full"

# ✅ check 명령어 수정 (별도 스크립트 사용)
[slash_commands."ipc:check"]
command = "uv run python %IPC_CHAT%\\tools\\check_messages.py {args[0]}"
```

## 설치 방법

### 옵션 1: 수동 복사

```powershell
# 1. 수정된 템플릿을 사용자 config로 복사
copy config\codex-config.toml %USERPROFILE%\.codex\config.toml

# 2. IPC_CHAT 경로 업데이트 (필요시)
notepad %USERPROFILE%\.codex\config.toml
# [environment] 섹션에서 IPC_CHAT 경로를 실제 프로젝트 경로로 수정

# 3. Codex CLI 재시작
```

### 옵션 2: 기존 config.toml에 병합

기존 Codex 설정이 있다면:

```powershell
# 1. 백업
copy %USERPROFILE%\.codex\config.toml %USERPROFILE%\.codex\config.toml.backup

# 2. config\codex-config.toml 내용을 기존 파일에 병합
notepad %USERPROFILE%\.codex\config.toml
```

## 테스트

```powershell
# 테스트 스크립트 실행
scripts\test-codex-commands.bat
```

또는 직접 테스트:

```powershell
# 1. Broker 상태 확인
uv run python tools\ipc_global_command.py status

# 2. 인스턴스 목록
uv run python tools\ipc_global_command.py instances list --full

# 3. 시스템 진단
uv run python tools\ipc_doctor.py --auto-fix
```

## 수정된 명령어 목록

| Slash Command | 올바른 CLI 명령어 | 변경 사항 |
|---------------|------------------|----------|
| `/ipc:status` | `ipc status` | `--json` 제거 |
| `/ipc:list` | `ipc instances list --full` | `--format json` → `list --full` |
| `/ipc:check` | `check_messages.py {instance}` | 별도 스크립트 사용 |
| `/ipc:responder-status` | `ipc responder status {instance}` | `--json` 제거 |
| `/ipc:responder-stop` | `ipc responder stop {instance}` | `--json` 제거 |
| `/ipc:doctor` | `ipc_doctor.py --auto-fix` | `--json` 제거 |

## 확인 방법

Codex CLI에서 다음 명령어들을 실행해보세요:

```bash
/ipc:status              # Broker 상태 확인
/ipc:list                # 인스턴스 목록
/ipc:doctor              # 시스템 진단
```

모든 명령어가 정상적으로 실행되어야 합니다.

## 관련 파일

- `config/codex-config.toml` - 수정된 Codex 설정 템플릿
- `scripts/test-codex-commands.bat` - 테스트 스크립트
- `~/.codex/config.toml` - 사용자 Codex 설정 (수동 업데이트 필요)

## 참고

- CLI 명령어 인터페이스는 `tools/ipc_global_command.py --help`로 확인 가능
- 각 하위 명령어 도움말: `ipc <command> --help`
