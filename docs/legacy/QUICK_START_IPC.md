# 🚀 IPC 설정 빠른 시작 가이드

다중 AI 협업을 위한 IPC(Inter-Process Communication) 설정 완벽 가이드

## 📋 사전 준비사항

1. **Python 3.8+** 설치 완료
2. **Git** (IPC 저장소 복제용)
3. **여러 AI CLI 도구** (Claude Code, Gemini, Codex, Local LM)

## 🎯 새 프로젝트용 한 줄 명령 설정

### 옵션 1: 자동 설정 (권장)

```bash
# IPC 저장소 복제
git clone https://github.com/your-repo/claude-ipc-mcp.git
cd claude-ipc-mcp

# 프로젝트에 IPC 설정
python tools/setup_new_project_ipc.py /프로젝트/경로

# 자동으로 수행되는 작업:
# ✅ 필요한 모든 IPC 도구 복사
# ✅ 프로젝트별 설정 생성
# ✅ IPC 서버 시작
# ✅ 연결 테스트
# ✅ AI 인스턴스 등록
```

### 옵션 2: 수동 설정

```bash
# 1. 프로젝트로 이동
cd /프로젝트/경로

# 2. IPC 저장소에서 도구 복사
cp -r /경로/claude-ipc-mcp/tools ./tools
cp -r /경로/claude-ipc-mcp/src ./src

# 3. 설정 생성
python tools/config_loader.py create

# 4. IPC 서버 시작
python src/claude_ipc_server.py

# 5. AI 인스턴스 등록
python tools/auto_register_all.py
```

## ⚡ 최소 Quickstart (신규 CLI)

다음 3단계면 기본 동작을 바로 확인할 수 있습니다.

```powershell
# 1) 프로젝트 디렉터리에서 초기화
ipc init

# 2) 상태 확인
ipc status

# 3) 핑
ipc ping
```

메시지 전송은 다른 프로젝트에서도 동일하게 `ipc init` 후 아래처럼 사용할 수 있습니다.

```powershell
ipc chat --to <상대_프로젝트_폴더명> "Hello"
```

주의: 브로커는 필요 시 자동으로 기동되며, 최초 호출 직후 수백 ms 대기 후 준비됩니다. 보안을 위해 `IPC_SHARED_SECRET` 설정을 권장합니다. 설정 방법은 `docs/SECURITY.md`를 참고하세요.

## 🔧 필수 명령어

### IPC 시스템 시작

```bash
# 한 번에 모든 것 시작
python start_all_ai_ipc.py

# 또는 개별 구성 요소 시작:
python src/claude_ipc_server.py          # 서버 시작
python tools/auto_register_all.py        # 모든 AI 등록
python start_split_monitoring.py         # 모니터링 시작
```

### 기본 IPC 작업

```bash
# AI 인스턴스 등록
python tools/ipc_register.py [이름]

# 메시지 전송
python tools/ipc_send.py [발신자] [수신자] "메시지"

# 메시지 확인
python tools/ipc_check.py [이름]

# 활성 인스턴스 목록
python tools/ipc_list.py

# 상태 점검
python tools/ipc_health_check.py
```

## 📁 설정 후 프로젝트 구조

```
프로젝트/
├── .ipc_project.yml       # 자동 생성된 설정
├── tools/                 # IPC 통신 도구
│   ├── ipc_register.py   # AI 인스턴스 등록
│   ├── ipc_send.py       # 메시지 전송
│   ├── ipc_check.py      # 메시지 확인
│   ├── ipc_list.py       # 인스턴스 목록
│   └── ...
├── src/                   # IPC 서버 구성 요소
│   ├── claude_ipc_server.py
│   └── project_isolation_patch.py
└── test/                  # IPC 테스트 스위트
    ├── test_ipc_connection.py
    └── test_project_isolation.py
```

## 🔍 설정 세부사항

`.ipc_project.yml` 파일 내용:

```yaml
project:
  name: 프로젝트-이름
  id: proj_XXXXXXXX        # 고유 프로젝트 ID
  port: 9XXX               # 프로젝트별 포트
  isolation_mode: strict   # 프로젝트 격리

allowed_instances:
  - claude
  - gemini
  - codex
  - lm

settings:
  rate_limit: 100          # 분당 메시지 수
  auto_responder: false    # 테스트용 활성화
```

## 🧪 설정 테스트

### 1. 빠른 연결 테스트

```bash
# IPC 작동 확인
python test/test_ipc_connection.py

# 예상 출력:
✅ 서버 연결: 정상
✅ 인스턴스 등록: 정상
✅ 메시지 송수신: 정상
✅ 프로젝트 격리: 정상
```

### 2. 상태 점검

```bash
python tools/ipc_health_check.py

# 표시 내용:
# - 서버 상태
# - 포트 접근성
# - 데이터베이스 상태
# - 활성 인스턴스
# - 시스템 리소스
```

### 3. 테스트 메시지 전송

```bash
# Claude 등록
python tools/ipc_register.py claude

# 테스트 메시지 전송
python tools/ipc_send.py claude claude "안녕하세요, IPC 테스트 중입니다!"

# 메시지 확인
python tools/ipc_check.py claude
```

## 💡 실제 사용 예시

### 예시 1: 코드 리뷰 요청

```python
# Claude CLI에서
from tools.ipc_client import IPCClient

claude = IPCClient("claude")
claude.send("gemini", "이 React 컴포넌트의 UX 개선점을 검토해주세요")
claude.send("codex", "이 API 엔드포인트의 보안 문제를 확인해주세요")
```

### 예시 2: 협업 기능 개발

```bash
# Claude가 아키텍처 설계
python tools/ipc_send.py claude all "아키텍처 준비 완료: REST API를 사용한 MVC 패턴"

# Gemini가 프론트엔드 구현
python tools/ipc_send.py gemini claude "프론트엔드 컴포넌트 완성"

# Codex가 백엔드 구현
python tools/ipc_send.py codex gemini "API 엔드포인트 준비 완료: /api/v1/*"

# LM이 테스트 작성
python tools/ipc_send.py lm all "테스트 커버리지 95%"
```

### 예시 3: 자동화된 워크플로우

```python
# collaborative_workflow.py
import time
from tools.ipc_client import IPCClient

def coordinate_feature_development(feature_name):
    claude = IPCClient("claude")

    # 1단계: 설계
    claude.send("all", f"{feature_name}의 설계 시작")
    time.sleep(5)

    # 2단계: 병렬 구현
    claude.send("gemini", "UI 컴포넌트 구현")
    claude.send("codex", "백엔드 로직 구현")
    claude.send("lm", "테스트 케이스 준비")

    # 3단계: 통합
    time.sleep(10)
    claude.send("all", "통합 테스팅 시작")

    # 4단계: 리뷰
    claude.send("all", "머지 전 코드 리뷰 필요")
```

## 🛠️ 문제 해결

### 일반적인 문제와 해결책

| 문제 | 해결책 |
|------|--------|
| 서버가 시작되지 않음 | 포트 가용성 확인: `netstat -an \| grep 9XXX` |
| 등록 실패 | 서버 실행 확인: `ps aux \| grep claude_ipc_server` |
| 메시지가 수신되지 않음 | 프로젝트 격리 확인: 같은 프로젝트만 가능 |
| 연결 거부 | 방화벽이 로컬호스트 연결을 허용하는지 확인 |
| 데이터베이스 오류 | 실행: `python tools/fix_database.py` |

### 모든 것 초기화

```bash
# 완전 초기화
python tools/reset_all_ipc.py

# 메시지만 삭제
python tools/clear_project_messages.py

# 데이터베이스 복구
python tools/fix_database.py
```

## 📊 모니터링

### 4-패널 모니터 시작

```bash
python start_split_monitoring.py

# 표시 내용:
# - 서버 상태 (왼쪽 상단)
# - 활성 인스턴스 (오른쪽 상단)
# - 메시지 흐름 (왼쪽 하단)
# - 시스템 리소스 (오른쪽 하단)
```

### 특정 인스턴스 확인

```bash
python tools/monitor_instance.py claude
```

## 🎯 모범 사례

1. **항상 프로젝트 격리 사용** - 프로젝트 간 메시지 유출 방지
2. **시작 시 등록** - 작업 전 AI 가용성 보장
3. **타임아웃 구현** - 무한 대기 방지
4. **복잡한 데이터는 JSON 사용** - 메시지 구조화
5. **속도 제한 모니터링** - 분당 100 메시지 이내 유지
6. **오래된 메시지 정리** - 주기적으로 정리 실행
7. **프로덕션 전 테스트** - 테스트 메시지로 설정 확인

## 📚 고급 기능

### 프로젝트 간 통신 (선택사항)

`.ipc_project.yml` 편집:

```yaml
project:
  isolation_mode: relaxed  # 또는 'disabled'

permissions:
  allow_cross_project: true
  trusted_projects:
    - proj_ABC12345
    - proj_XYZ67890
```

### 사용자 정의 자동 응답기

```python
# tools/custom_responder.py
from tools.simple_auto_responder import AutoResponder

class CustomResponder(AutoResponder):
    def generate_response(self, message):
        # 사용자 정의 로직
        return f"사용자 정의 응답: {message}"

responder = CustomResponder("custom_ai")
responder.run()
```

### 일괄 작업

```python
# 여러 수신자에게 전송
from tools.ipc_client import IPCClient

client = IPCClient("claude")
recipients = ["gemini", "codex", "lm"]
for recipient in recipients:
    client.send(recipient, "브로드캐스트 메시지")
```

## 🚀 다음 단계

1. **예제 프로젝트 시도**: `examples/todo_app_with_ipc/`
2. **설정 사용자 정의**: `.ipc_project.yml` 편집
3. **협업 워크플로우 구축**: 오케스트레이션 스크립트 작성
4. **확장**: 필요에 따라 더 많은 AI 인스턴스 추가
5. **성능 모니터링**: 상태 점검 및 모니터링 도구 사용

## 📞 도움 받기

- **문서**: `docs/IPC_설정_가이드.md`
- **상태 점검**: `python tools/ipc_health_check.py`
- **진단**: `python tools/ipc_health_check.py --verbose`
- **예제**: `examples/` 디렉토리 확인
- **초기화**: `python tools/reset_all_ipc.py`

---

**시작할 준비가 되셨나요?** 프로젝트 디렉토리에서 `python tools/setup_new_project_ipc.py .`를 실행하세요!