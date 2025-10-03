# Gemini CLI IPC Commands Installation

이 디렉토리에는 Gemini CLI용 IPC slash 명령어들이 포함되어 있습니다.

**✅ 최근 업데이트 (2025-10-02)**:
- 모든 TOML 파일 템플릿 변수 수정 (`{{args}}` → `{args}`)
- 인용부호 문제 해결
- 검증 스크립트 추가 (`tools/validate_gemini_commands.py`)
- 23개 명령어 모두 검증 완료

## 설치 방법

### Windows (PowerShell)

```powershell
# Gemini commands 디렉토리 생성 (이미 존재할 수 있음)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\commands\ipc"

# 모든 TOML 파일 복사
Copy-Item "D:\claude-ipc-mcp\docs\gemini-commands\*.toml" "$env:USERPROFILE\.gemini\commands\ipc\"

# Gemini 재시작 필요
Write-Host "✅ 설치 완료! Gemini를 재시작하세요."
```

### Linux/Mac (Bash)

```bash
# Gemini commands 디렉토리 생성
mkdir -p ~/.gemini/commands/ipc

# 모든 TOML 파일 복사
cp /d/claude-ipc-mcp/docs/gemini-commands/*.toml ~/.gemini/commands/ipc/

# 완료 메시지
echo "✅ 설치 완료! Gemini를 재시작하세요."
```

## 설치 확인

설치 후 Gemini를 재시작하고 `/ipc`를 입력하여 모든 IPC 명령어가 표시되는지 확인하세요.

## 사용 가능한 명령어 (17개)

### 핵심 명령어
- `/ipc/init` - 프로젝트 IPC 구조 초기화
- `/ipc/ping` - 브로커 연결 테스트
- `/ipc/register <이름>` - 인스턴스 등록
- `/ipc/check` - 새 메시지 확인

### 통신 명령어
- `/ipc/ask <대상> <메시지> [타임아웃]` - 메시지 전송 및 응답 대기
- `/ipc/broadcast <메시지>` - 모든 인스턴스에 브로드캐스트

### 브로커 관리
- `/ipc/broker-start` - 글로벌 브로커 시작
- `/ipc/broker-stop` - 글로벌 브로커 종료
- `/ipc/broker-status` - 브로커 상태 확인

### 인스턴스 관리
- `/ipc/instances-delete <이름>` - 특정 인스턴스 삭제
- `/ipc/instances-reset` - 모든 인스턴스 초기화
- `/ipc/rename <옛이름> <새이름>` - 인스턴스 이름 변경 (1시간당 1회)

### 메시지 관리
- `/ipc/messages-clear` - 모든 메시지 삭제

### 세션 관리
- `/ipc/session` - 현재 세션 정보 표시
- `/ipc/session-clear` - 세션 데이터 삭제

### 자동 응답기
- `/ipc/responder-start-all` - 모든 응답기 시작
- `/ipc/responder-stop-all` - 모든 응답기 종료

## 명령어 사용 예시

### 기본 사용
```
/ipc/init                           # IPC 초기화
/ipc/register gemini-main           # gemini-main으로 등록
/ipc/check                          # 메시지 확인
```

### 메시지 전송
```
/ipc/ask claude "상태 보고"          # claude에게 메시지 전송 및 응답 대기
/ipc/broadcast "모두 안녕하세요"      # 모든 인스턴스에 브로드캐스트
```

### 브로커 관리
```
/ipc/broker-status                  # 브로커 상태 확인
/ipc/broker-start                   # 브로커 시작 (필요시)
```

## 중요 사항

### 절대 경로 사용
모든 명령어는 절대 경로를 사용하도록 수정되었습니다:
- `D:/claude-ipc-mcp/tools/ipc_global_command.py`
- 환경 변수 `%IPC_CHAT%`는 더 이상 필요하지 않습니다

### 매개변수 형식
명령어는 `{{args[0]}}`, `{{args[1]}}` 형식을 사용합니다:
- `{{args[0]}}` - 첫 번째 매개변수
- `{{args[1]}}` - 두 번째 매개변수
- `{{args[2]:-30}}` - 세 번째 매개변수 (기본값: 30)

### 플랫폼 호환성
- Windows와 Unix/Linux 모두 지원
- 슬래시(`/`) 경로 구분자 사용
- `uv run python` 명령어 사용

## 검증 및 테스트

### TOML 파일 검증
모든 명령어 파일이 올바른지 검증:
```powershell
uv run python D:/claude-ipc-mcp/tools/validate_gemini_commands.py
```

출력 예시:
```
🔍 Validating 23 Gemini TOML files

ask.toml                            ✅ OK
broadcast.toml                      ✅ OK
...
✨ All files are valid!
```

### 기본 테스트 절차
1. **설치 확인**
   ```
   /ipc/init                    # .ipc 디렉토리 생성
   /ipc/broker-status           # 브로커 상태 확인
   ```

2. **등록 테스트**
   ```
   /ipc/register gemini-test    # 인스턴스 등록
   /ipc/list                    # 인스턴스 목록 확인
   ```

3. **메시지 테스트**
   ```
   /ipc/send claude "Hello"     # 메시지 전송
   /ipc/check                   # 메시지 확인
   ```

4. **브로드캐스트 테스트**
   ```
   /ipc/broadcast "안녕하세요"    # 모두에게 전송
   ```

## 문제 해결

### 명령어가 표시되지 않는 경우
1. Gemini를 완전히 재시작
2. `~/.gemini/commands/ipc/` 디렉토리 확인
3. TOML 파일들이 올바르게 복사되었는지 확인
4. 검증 스크립트 실행: `uv run python tools/validate_gemini_commands.py`

### 명령어 실행 에러
1. `uv`가 설치되어 있는지 확인: `uv --version`
2. 프로젝트 경로가 정확한지 확인: `D:/claude-ipc-mcp`
3. 브로커가 실행 중인지 확인: `/ipc/broker-status`
4. Python 경로 확인: `uv run python --version`

### 매개변수 에러
- 명령어 사용 시 필요한 매개변수를 모두 제공했는지 확인
- 예: `/ipc/ask <대상> <메시지>` - 두 매개변수 모두 필요
- 공백이 포함된 메시지는 자동으로 인용부호 처리됨

### 템플릿 변수 에러
- ✅ 올바른 형식: `{args[0]}`, `{args[1]}`
- ❌ 잘못된 형식: `{{args[0]}}` (이중 중괄호)
- 모든 파일이 수정되었으므로 이 에러는 발생하지 않아야 함

## 고급 기능

### 브로커 자동 시작
브로커는 첫 IPC 작업 시 자동으로 시작됩니다. 수동 시작이 필요한 경우:
```
/ipc/broker-start
```

### 세션 관리
세션 토큰은 `.ipc/state/session.json`에 저장되며 24시간 동안 유효합니다:
```
/ipc/session              # 현재 세션 확인
/ipc/session-clear        # 세션 초기화
```

## 관련 문서

- **완전한 명령어 참조**: `docs/IPC_COMPLETE_COMMAND_REFERENCE.md`
- **통합 요약**: `docs/IPC_CLI_INTEGRATION_SUMMARY.md`
- **CLI 명령어**: `docs/ipc_cli_commands.md`
- **문제 해결**: `docs/TROUBLESHOOTING.md`

## 버전 정보

- **버전**: 2.0.0
- **마지막 업데이트**: 2025-10-02
- **변경사항**: 절대 경로 사용, 매개변수 형식 표준화, 환경 변수 제거
