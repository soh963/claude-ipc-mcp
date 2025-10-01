# 글로벌 IPC 사용 가이드 (한글)

> 이 문서는 통합 한국어 가이드로 대체되었습니다. 최신 정보는 다음을 확인하세요:
> - IPC 통합 가이드 (KO): [IPC_UNIFIED_GUIDE_KO.md](IPC_UNIFIED_GUIDE_KO.md)
> - 설치: [INSTALL.md](INSTALL.md)
> - 트러블슈팅: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

아래 내용은 보관용이며 일부 정보가 최신과 다를 수 있습니다.

이 문서는 "전역 설치 한 번 → 모든 프로젝트에서 사용"을 목표로, Windows PowerShell 기준으로 아주 쉽게 정리한 사용법입니다. `ipc` 래퍼가 PATH에 없다면 `./ipc.bat` 또는 `uv run python tools/ipc_global_command.py`로 동일하게 실행하세요.

참고: 브로커 관리 전역 명령어가 추가되었습니다.
- `ipc broker status` / `ipc broker start` / `ipc broker stop`
- 환경변수 `IPC_HOST`, `IPC_GLOBAL_PORT`(또는 `IPC_PORT`)로 호스트/포트를 제어할 수 있습니다.
 - 상태 확인(`list` 액션)은 인증이 필요 없습니다. 최신 코드에서는 공개로 열려 있어 `ipc broker status`가 세션 없이 동작합니다.

## 0) 준비물
- Windows + PowerShell
- Python 3.12 이상, Git, UV(패키지 매니저)

설치 확인:
```powershell
python --version
git --version
uv --version
```

## 1) 전역 설치(한 번만)
```powershell
# 중앙 위치에 설치
cd D:\
git clone https://github.com/soh963/claude-ipc-mcp.git
cd claude-ipc-mcp

# 의존성 설치
uv sync
```

선택) 전역 래퍼 등록(편의):
```powershell
# PATH에 등록되어 있다면 어디서든 'ipc' 바로 사용 가능
# 미등록이면 아래처럼 직접 실행해도 됩니다
# .\ipc.bat <cmd>
# uv run python tools/ipc_global_command.py <cmd>
```

자세한 전역 설치 안내: `docs/GLOBAL_IPC_SETUP_GUIDE.md`

## 2) 1분 퀵스타트(어디서든 실행)
```powershell
# 새/기존 프로젝트 폴더로 이동
cd D:\my-project

# 초기화 → 상태 → 핑(연결 확인)
ipc init
ipc status
ipc ping
```
정상이라면 각 명령이 0 종료코드로 끝나고, 짧은 진단/상태 메시지가 표시됩니다.

## 3) 전역 명령어 모음

### 프로젝트 관리
```powershell
ipc init                 # 프로젝트 초기화 (.ipc/ 설정, 포트 할당)
ipc init --minimal       # 최소 설정만 생성
ipc init --port 9456     # 원하는 포트 지정
ipc start                # 현재 프로젝트용 IPC 서버 시작
ipc stop                 # 현재 프로젝트용 IPC 서버 중지
```

### 상태/점검
```powershell
ipc status               # 현재 프로젝트 상태 요약
ipc ping                 # 연결/계약 출력 확인
ipc health               # 건강 상태 점검(확장 진단)
ipc doctor               # 종합 점검(권장)
```

### 인스턴스/메시지
```powershell
ipc register alice                       # 내 인스턴스 이름 등록
ipc chat --to bob "안녕! IPC 테스트"     # 자연어 채팅 스타일(권장)
ipc send alice bob "스키마 검토 부탁"   # 주소지 스타일(from/to)
ipc list                                  # 등록된 인스턴스 목록
ipc check alice                           # alice의 메시지 확인
```

Tip: `ipc --help`, `ipc <subcommand> --help`로 사용법을 볼 수 있습니다.

## 4) 빠른 동작 확인(계약 기준)
```powershell
ipc init
ipc ping
ipc chat --to self "헬로우 IPC"
```
정상 시 출력에 “ack/acknowledgment/sent” 같은 확인 문구와 `correlation=`이 함께 표시됩니다.

## 5) 문제 해결 빠른 체크
- 초기화 오류: 먼저 `ipc init` 실행 여부 확인
- 보안(선택): 양쪽 동일한 비밀키 필요
```powershell
$env:IPC_SHARED_SECRET = "같은-비밀키"
```
- 로그 보기: `logs/` 폴더 확인
- 계속 안 될 때: `ipc doctor` 결과를 이슈에 첨부

### 브로커 느림/상태가 항상 false일 때
다음 순서로 “캐시/재시작”을 수행하면 대부분 해결됩니다.

```powershell
# 1) 브로커 중지(여러 번 호출해도 안전)
ipc broker stop

# 2) 파이썬 캐시 폴더(__pycache__) 정리
$root = "D:\claude-ipc-mcp\src"
Get-ChildItem $root -Recurse -Directory -Filter "__pycache__" |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 3) 브로커 재시작 및 상태 확인
ipc broker start
ipc broker status

# 4) 포트가 실제로 열렸는지 확인(기본 9876)
Test-NetConnection 127.0.0.1 -Port 9876
```

참고: `ipc broker status`는 인증이 필요 없으므로, 서버 코드가 최신(공개 `list` 적용)으로 실행 중이라면 `{"running": true, "port": 9876}` 형태로 표시됩니다. 여전히 느리다면 PowerShell에서 실행하세요(Git Bash 환경은 소켓 타임아웃이 길어질 수 있음).

## 6) 자주 묻는 질문(FAQ)
- Q. `ipc` 명령이 인식되지 않아요.
  - A. PATH에 등록되지 않았다면 `./ipc.bat` 혹은 `uv run python tools/ipc_global_command.py`로 실행하세요.
- Q. Windows에서 심볼릭 링크가 안 돼요.
  - A. 개발자 모드 활성화 또는 관리자 권한 필요. 자세한 내용은 `docs/GLOBAL_IPC_SETUP_GUIDE.md` 참고.
- Q. 포트가 이미 사용 중이라고 나와요.
  - A. 다른 포트를 지정하세요: `ipc init --port 9999`

## 7) 참고 문서
- `README.md` (개요/배지/기능)
- `INSTALL.md`, `docs/INSTALL_UV.md` (설치)
- `docs/GLOBAL_IPC_SETUP_GUIDE.md` (전역 설정 상세)
- `TROUBLESHOOTING.md` (문제 해결)

---
이제 어떤 프로젝트 폴더에서도 `ipc` 명령어로 AI-간 메시징을 시작해보세요! 🚀
