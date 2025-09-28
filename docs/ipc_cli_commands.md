# IPC MCP Command Guide

이 문서는 `claude-ipc-mcp` 리포지토리의 IPC 브로커와 클라이언트 도구를 다른 프로젝트 폴더에서도 안정적으로 활용하기 위한 명령어 모음과 초기화 순서를 정리합니다.

## 사전 준비

- `scripts/install-global.ps1`을 한 번 실행하면 PowerShell 프로필에 `tools/ipc_cli_helpers.ps1`이 자동으로 등록되어 `ipc-chat`, `ipc-ping`, `ipc-responder-*` 별칭과 `IPC_CHAT` 환경변수, 그리고 이 문서에 등장하는 `python tools/...`, `uv run python tools/...`, `powershell -File scripts/...`, `bash scripts/...` 명령이 어느 위치에서든 작동하도록 경로를 보정하는 래퍼가 준비됩니다. 직접 설정하려면 PowerShell 프로필에서 `tools/ipc_cli_helpers.ps1`를 dot-source 하세요.
- `PATH`에 `D:\claude-ipc-mcp\tools`와 `D:\claude-ipc-mcp\scripts`가 포함되어 있는지 확인합니다. (기본 제공 스크립트가 이미 추가해 둔 상태라면 다른 디렉터리에서도 명령을 사용할 수 있습니다.)
- Python 3.12 이상과 `uv`가 설치되어 있다면 `uv run …` 형태로 의존성 정리와 실행을 할 수 있습니다. 별도 가상환경을 쓰지 않을 경우에는 `python …`으로 직접 실행해도 됩니다.

## IPC 사용 순서

1. **(선택) 의존성 동기화**: `uv sync`
2. **브로커 기동 확인**: `uv run python tools/start_broker.py`
   - PowerShell 헬퍼를 사용한다면 `ipc-chat`이나 `ipc-ping` 호출 시 `start_broker.py`를 먼저 실행하도록 구성할 수 있습니다.
3. **인스턴스 등록** (최초 1회 또는 새 이름 필요 시)
   ```powershell
   uv run python tools/ipc_register.py codex --no-default
   ```
   - 기본 인스턴스로 쓰려면 `--no-default` 옵션을 빼주세요.
4. **채팅/모니터링 명령 실행**: `ipc-chat`, `ipc-ping`, `uv run python tools/chat_once.py …` 등
5. **상태 점검 및 유지보수**: 필요 시 `python tools/ipc_list.py`, `uv run python tools/ipc_doctor.py`, `python tools/reset_all_ipc.py` 등을 사용합니다.

## 명령어 레퍼런스

### 브로커 & 세션 관리

| 명령어 | 위치 | 설명 | 예시 |
| --- | --- | --- | --- |
| `start_broker.py` | `tools/start_broker.py` | 브로커 실행 여부를 확인하고 필요 시 싱글톤으로 기동 | `uv run python tools/start_broker.py` |
| `ipc_register.py` | `tools/ipc_register.py` | 신규 인스턴스 등록 또는 토큰 재발급 | `uv run python tools/ipc_register.py codex --no-default` |
| `ipc_list.py` | `tools/ipc_list.py` | 현재 활성화된 인스턴스 목록 확인 | `python tools/ipc_list.py` |
| `ipc_check.py` | `tools/ipc_check.py` | 브로커와 세션 기본 진단 | `uv run python tools/ipc_check.py` |
| `ipc_doctor.py` | `tools/ipc_doctor.py` | 브로커/세션/데이터베이스 종합 점검 | `uv run python tools/ipc_doctor.py` |
| `ipc_manager.py` | `tools/ipc_manager.py` | 인스턴스, 브로커, 세션을 통합적으로 관리하는 CLI | `uv run python tools/ipc_manager.py --help` |
| `reset_all_ipc.py` | `tools/reset_all_ipc.py` | 세션/DB 초기화(브로커 중지 후 사용 권장) | `python tools/reset_all_ipc.py` |
| `fix_database.py` | `tools/fix_database.py` | SQLite 데이터베이스 복구 스크립트 | `uv run python tools/fix_database.py` |
| `fix_all_schema.py` | `tools/fix_all_schema.py` | DB 스키마 정합성 검사 및 수정 | `uv run python tools/fix_all_schema.py` |
| `db_compat.py` | `tools/db_compat.py` | 이전 버전 DB 호환성 검사 | `python tools/db_compat.py --analyze` |

### 채팅 & 메시징

| 명령어 | 위치 | 설명 | 예시 |
| --- | --- | --- | --- |
| `ipc-chat` | PowerShell 함수 (`tools/ipc_cli_helpers.ps1`) | 자연어 프롬프트로 빠르게 IPC 대화 실행 (`nl_auto_chat.py` 래핑) | `ipc-chat "codex가 gemini에게 '업데이트 상황 보고' 전달"` |
| `ipc-ping` | PowerShell 함수 | 단발 메시지 전송 (`chat_once.py` 래핑) | `ipc-ping -Message "상태 점검"` |
| `chat_once.py` | `tools/chat_once.py` | 명시적 파라미터로 단발 메시지 전송 | `uv run python tools/chat_once.py codex gemini "테스트" --auto-responder --timeout 10` |
| `nl_auto_chat.py` | `tools/nl_auto_chat.py` | 자연어 프롬프트 해석 후 `chat_once.py` 또는 `auto_chat_demo.py` 호출 | `python tools/nl_auto_chat.py "codex가 gemini에게 '빌드 결과' 공유"` |
| `auto_chat_demo.py` | `tools/auto_chat_demo.py` | 장시간 자동 대화 시나리오 실행 | `uv run python tools/auto_chat_demo.py codex gemini --message "Ping" --duration 60 --max-turns 20` |
| `auto_responder.py` / `simple_auto_responder.py` / `nl_auto_chat.py` | `tools/` | 자동 응답기 스크립트 (별도 실행으로 상주) | `uv run python tools/auto_responder.py codex gemini` |
| `ipc_send.py` | `tools/ipc_send.py` | 큐 기반 메시지 전송 또는 예약 전송 | `uv run python tools/ipc_send.py --from codex --to gemini --message "로그 정리"` |
| `scripts/ipc.bat` | `scripts/ipc.bat` | Windows용 빠른 실행 배치, 내부적으로 Python 스크립트를 호출 | `ipc.bat codex gemini "테스트"` |
| `scripts/ipc-send.bat` | `scripts/ipc-send.bat` | 큐 전송용 배치 | `ipc-send.bat codex gemini "보고서 요청"` |
| `scripts/ipc-monitor.bat` | `scripts/ipc-monitor.bat` | 모니터링 배치 실행 | `ipc-monitor.bat codex gemini` |

### 응답기 & 모니터링

| 명령어 | 위치 | 설명 | 예시 |
| --- | --- | --- | --- |
| `ipc-responder-list` | PowerShell 함수 | 현재 실행 중인 자동 응답기 세션 나열 | `ipc-responder-list` |
| `ipc-responder-stop` | PowerShell 함수 | 특정 또는 모든 자동 응답기 중지 | `ipc-responder-stop codex`, `ipc-responder-stop` |
| `manage_responders.py` | `tools/manage_responders.py` | 자동 응답기 등록/중지/모니터링 | `uv run python tools/manage_responders.py --stop-all` |
| `instance_monitor.py` / `monitor_instance.py` | `tools/` | 특정 인스턴스 상태 모니터링 스크립트 | `uv run python tools/monitor_instance.py codex` |
| `auto_chat_demo.py --monitor` | `tools/auto_chat_demo.py` | 대화 진행 상황을 실시간 출력 | `uv run python tools/auto_chat_demo.py codex gemini --message "Ping" --monitor` |
| `tools/start_broker.py` + 모니터 | `scripts/ipc-monitor.bat` | 브로커 기동 + 모니터링 통합 실행 | `ipc-monitor.bat codex gemini` |

### 보조 도구 & 환경 설정

| 명령어 | 위치 | 설명 | 예시 |
| --- | --- | --- | --- |
| `ipc_cli_helpers.ps1` | `tools/ipc_cli_helpers.ps1` | PowerShell 별칭/환경 변수 로더 (`ipc-chat`, `ipc-ping` 등) | `. D:/claude-ipc-mcp/tools/ipc_cli_helpers.ps1` |
| `install-global.ps1` | `scripts/install-global.ps1` | PATH/프로필 등록 자동화 | `powershell -ExecutionPolicy Bypass -File scripts/install-global.ps1` |
| `install-mcp.sh` / `.bat` | `scripts/install-mcp.*` | 다양한 셸에서 IPC 도구 설치 | `bash scripts/install-mcp.sh` |
| `ipc-cli` 헬퍼 함수 | PowerShell 프로필 | `$env:IPC_CHAT`, `ipc-chat` 등 alias가 전역에서 사용 가능하도록 설정 | PowerShell 프로필에 함수 추가 |
| `session_utils.py` | `tools/session_utils.py` | 세션 파일 로드/관리 함수 모음 (다른 스크립트에서 내부 사용) | 라이브러리용 모듈 |

## TIP

- `scripts/install-global.ps1`이 등록한 경로 보정 래퍼 덕분에 이 문서의 모든 명령은 현재 작업 디렉터리에 관계없이 그대로 실행됩니다.
- `IPC_CHAT` 환경 변수를 활용하면 다른 프로젝트 폴더에서도 `Invoke-Expression $env:IPC_CHAT --dry-run "codex가 gemini에게 '상태 보고' 요청"`처럼 자연어 기반 실행이 가능합니다.
- PowerShell alias가 적용된 상태라면 `ipc-chat`, `ipc-ping`, `ipc-responder-*` 명령을 어느 위치에서든 사용할 수 있습니다.
- 브로커가 응답하지 않을 때는 `tools/start_broker.py`를 다시 실행하거나 `tools/ipc_doctor.py`로 원인을 파악하세요.
- `broker_test_*` 인스턴스는 브로커 자동 헬스체크에서 생성됩니다. 목록을 정리하고 싶다면 브로커를 재시작하거나 `reset_all_ipc.py`를 실행하세요.
