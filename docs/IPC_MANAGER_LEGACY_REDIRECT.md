# IPC Manager Legacy Redirect

## 개요

`ipc_manager.py`는 레거시 호환성을 위해 유지되며, 모든 명령을 새로운 통합 CLI인 `ipc_global_command.py`로 리디렉션합니다.

## 문제 상황

Gemini AI가 `ipc_manager.py list --json`을 실행했을 때, 레거시 시스템의 `instances.json` 파일을 읽어서 8개의 오래된 인스턴스를 표시했습니다. 반면 Claude Code와 Codex는 `ipc_global_command.py`를 사용하여 글로벌 브로커의 현재 인스턴스 2개를 정확하게 표시했습니다.

### 왜 다른 결과가 나왔나?

**레거시 시스템 (`ipc_manager.py`)**:
- 데이터베이스: `~/.claude-ipc-data/instances.json` (JSON 파일)
- 글로벌 브로커와 분리된 별도 시스템
- 오래된 데이터 (2025-09-25 등록된 인스턴스들)

**글로벌 브로커 시스템 (`ipc_global_command.py`)**:
- 데이터베이스: `~/.claude-ipc-data/messages.db` (SQLite)
- TCP 브로커 (포트 9876)와 통합
- 현재 활성 인스턴스만 표시

## 해결 방법

`ipc_manager.py`를 리디렉션 스크립트로 변환하여, 모든 명령을 `ipc_global_command.py`로 자동 전달합니다.

### 명령어 변환 매핑

| 레거시 명령어 | 새 명령어 |
|---------------|-----------|
| `ipc_manager.py list` | `ipc_global_command.py instances list --full` |
| `ipc_manager.py register <id>` | `ipc_global_command.py register <id>` |
| `ipc_manager.py status` | `ipc_global_command.py status` |
| `ipc_manager.py check <id>` | `ipc_global_command.py messages check` |
| `ipc_manager.py send <from> <to> <msg>` | `ipc_global_command.py chat --to <to> <msg>` |

## 사용 예시

### 기본 사용

```bash
# 레거시 명령어 (자동으로 변환됨)
uv run python tools/ipc_manager.py list

# 출력:
# ⚠️  레거시 명령어 'list'가 새 명령어로 변환됩니다:
# 📌 instances list --full
#
# 📊 Unified Instance Status (2 instance(s)):
#   Instance: claude-debate
#     Broker:    ✓ Registered
#     Responder: ✗ Not running
#   Instance: test-tem-main
#     Broker:    ✓ Registered
#     Responder: ✗ Not running
```

### JSON 출력 (경고 메시지 숨김)

```bash
# --json 플래그 사용시 경고 메시지 출력 안함
uv run python tools/ipc_manager.py list --json

# 출력:
# 📊 Unified Instance Status (2 instance(s)):
#   Instance: claude-debate
#     Broker:    ✓ Registered
#     Responder: ✗ Not running
```

## 권장 사항

새로운 프로젝트나 스크립트에서는 `ipc_global_command.py`를 직접 사용하세요:

```bash
# 권장
uv run python tools/ipc_global_command.py instances list --full

# 또는 PATH에 등록된 경우
ipc instances list --full
```

## 레거시 데이터 정리

오래된 `instances.json` 파일은 더 이상 사용되지 않습니다:

```bash
# 확인
cat ~/.claude-ipc-data/instances.json

# 백업 후 제거 (선택사항)
mv ~/.claude-ipc-data/instances.json ~/.claude-ipc-data/instances.json.backup
```

## 기술 세부사항

### 구현 방식

1. **명령어 파싱**: `sys.argv`에서 레거시 명령어 추출
2. **명령어 변환**: `command_mapping` 딕셔너리를 사용한 변환
3. **플래그 처리**: `--json` 플래그 감지 및 제거
4. **프로세스 실행**: `subprocess.run()`으로 새 명령어 실행
5. **종료 코드 전달**: 원본 명령의 종료 코드 유지

### 파일 위치

- **리디렉션 스크립트**: `tools/ipc_manager.py`
- **통합 CLI**: `tools/ipc_global_command.py`
- **문서**: `docs/IPC_MANAGER_LEGACY_REDIRECT.md`

## 참고

- `ipc_manager.py`는 하위 호환성을 위해 유지됩니다
- 모든 새 기능은 `ipc_global_command.py`에 추가됩니다
- 레거시 시스템은 향후 완전히 제거될 수 있습니다
