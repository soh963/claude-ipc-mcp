# 🔒 프로젝트 격리 구현 가이드
## AI CLI 간 통신을 동일 프로젝트로 제한하는 방법

---

## 📌 핵심 원칙

**"같은 프로젝트를 작업하는 AI CLI만 서로 통신할 수 있다"**

- ✅ 허용: 같은 프로젝트 디렉토리의 AI들끼리 통신
- ❌ 금지: 다른 프로젝트의 AI와 크로스 통신

---

## 🎯 추천 구현 방법 (우선순위 순)

### 방법 1: 프로젝트 경로 해시 (⭐ 가장 추천)

**자동으로 프로젝트 경로를 해시하여 격리**

#### 1. 프로젝트 ID 생성 함수
```python
# tools/project_utils.py
import hashlib
import os

def get_project_id():
    """현재 프로젝트 경로를 해시하여 고유 ID 생성"""
    project_path = os.path.abspath(os.getcwd())

    # Windows/Unix 경로 정규화
    project_path = project_path.replace('\\', '/').lower()

    # SHA-256 해시 생성
    hash_obj = hashlib.sha256(project_path.encode())
    project_id = hash_obj.hexdigest()[:8]  # 8자리만 사용

    return f"proj_{project_id}"

def get_project_port():
    """프로젝트별 고유 포트 생성 (9000-9999 범위)"""
    project_id = get_project_id()
    # 해시를 숫자로 변환하여 포트 생성
    port_offset = int(hashlib.md5(project_id.encode()).hexdigest()[:4], 16) % 1000
    return 9000 + port_offset
```

#### 2. 서버 시작 시 적용
```python
# src/claude_ipc_server.py 수정
from tools.project_utils import get_project_id, get_project_port

class MessageBroker:
    def __init__(self):
        self.project_id = get_project_id()
        self.port = get_project_port()
        self.host = "127.0.0.1"

        print(f"🔒 Project ID: {self.project_id}")
        print(f"🔌 Using port: {self.port}")
```

#### 3. 메시지 전송 시 검증
```python
def _process_request(self, request):
    # 프로젝트 ID 검증
    if request.get("project_id") != self.project_id:
        return {
            "status": "error",
            "message": f"Project mismatch. Expected: {self.project_id}"
        }

    # 기존 처리 로직...
```

---

### 방법 2: 설정 파일 사용 (.ipc_project.yml)

**프로젝트별 설정 파일로 명시적 격리**

#### 1. 프로젝트 설정 파일 생성
```yaml
# .ipc_project.yml (프로젝트 루트)
project:
  name: "my-awesome-project"
  id: "proj_2024_awesome"
  port: 9877  # 프로젝트 전용 포트

  # 허용된 인스턴스 목록 (선택사항)
  allowed_instances:
    - claude
    - gemini
    - codex

  # 프로젝트별 설정
  settings:
    max_message_size: 20480  # 20KB
    auto_responder: true
    rate_limit: 200  # 분당 200 요청
```

#### 2. 설정 로더 구현
```python
# tools/config_loader.py
import yaml
import os

def load_project_config():
    """프로젝트 설정 파일 로드"""
    config_path = os.path.join(os.getcwd(), '.ipc_project.yml')

    if not os.path.exists(config_path):
        # 기본 설정 생성
        return create_default_config()

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_default_config():
    """기본 설정 생성"""
    from tools.project_utils import get_project_id, get_project_port

    config = {
        'project': {
            'name': os.path.basename(os.getcwd()),
            'id': get_project_id(),
            'port': get_project_port()
        }
    }

    # 설정 파일 저장
    with open('.ipc_project.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    return config
```

---

### 방법 3: 환경 변수 격리

**환경 변수로 프로젝트 네임스페이스 설정**

#### 1. 프로젝트별 환경 설정
```bash
# .env 파일 (프로젝트 루트)
IPC_PROJECT_ID=my_project_2024
IPC_PROJECT_PORT=9877
IPC_PROJECT_NAME="My Awesome Project"
```

#### 2. 자동 환경 설정 스크립트
```bash
# setup_project_ipc.sh
#!/bin/bash

# 프로젝트 경로 기반 자동 ID 생성
PROJECT_PATH=$(pwd)
PROJECT_HASH=$(echo -n "$PROJECT_PATH" | sha256sum | cut -c1-8)
PROJECT_ID="proj_${PROJECT_HASH}"

# 포트 계산 (9000-9999)
PORT_OFFSET=$(echo -n "$PROJECT_ID" | md5sum | cut -c1-4)
PORT=$((9000 + (0x$PORT_OFFSET % 1000)))

# 환경 변수 설정
export IPC_PROJECT_ID=$PROJECT_ID
export IPC_PROJECT_PORT=$PORT

echo "🔒 Project IPC configured:"
echo "   ID: $PROJECT_ID"
echo "   Port: $PORT"
```

#### 3. Python에서 환경 변수 읽기
```python
import os

class ProjectConfig:
    @staticmethod
    def get_project_id():
        return os.environ.get('IPC_PROJECT_ID', 'default_project')

    @staticmethod
    def get_project_port():
        return int(os.environ.get('IPC_PROJECT_PORT', 9876))
```

---

### 방법 4: Git 기반 격리

**Git 저장소를 프로젝트 식별자로 사용**

```python
# tools/git_project.py
import subprocess
import hashlib

def get_git_project_id():
    """Git remote URL을 기반으로 프로젝트 ID 생성"""
    try:
        # Git remote URL 가져오기
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            remote_url = result.stdout.strip()
            # URL 해시
            hash_obj = hashlib.sha256(remote_url.encode())
            return f"git_{hash_obj.hexdigest()[:8]}"
    except:
        pass

    # Git이 없으면 경로 해시 사용
    from tools.project_utils import get_project_id
    return get_project_id()
```

---

## 🚀 빠른 시작 가이드

### ⚡ 원클릭 전체 환경 구성 (가장 추천)
```bash
# 한 번의 명령으로 모든 AI CLI IPC 환경 활성화
python start_all_ai_ipc.py

# 이 명령이 수행하는 작업:
# 1. 프로젝트별 고유 ID 자동 생성
# 2. 프로젝트 전용 포트로 IPC 서버 시작
# 3. Claude, Gemini, Codex 등 모든 AI 인스턴스 자동 등록
# 4. 4-panel 모니터링 시스템 자동 실행
# 5. 실제 AI 응답만 사용하는 auto-responder 활성화
# 6. 프로젝트 격리 네임스페이스 설정
```

### 수동 단계별 시작 (디버깅용)

#### 1단계: 프로젝트 격리 초기화
```bash
# 프로젝트 루트에서 실행
python tools/init_project_isolation.py
```

#### 2단계: 격리된 IPC 서버 시작
```bash
# 프로젝트별 포트로 자동 시작
python src/claude_ipc_server.py --project-isolated
```

#### 3단계: AI 인스턴스 등록
```python
# 프로젝트 ID가 자동 포함됨
python tools/ipc_register.py claude
# → 등록: claude@proj_abc123
```

---

## 🔍 격리 상태 확인

### 현재 프로젝트 정보 확인
```bash
python tools/show_project_info.py
```

출력 예시:
```
🔒 Project Isolation Status
━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Path: D:\my-project
Project ID: proj_a1b2c3d4
Project Port: 9234
Active Instances: 3
  - claude@proj_a1b2c3d4
  - gemini@proj_a1b2c3d4
  - codex@proj_a1b2c3d4
```

---

## 🔧 프로세스 관리

### 모든 IPC 프로세스 초기화
```bash
# 실행 중인 모든 IPC 관련 프로세스 종료 및 재시작
python tools/reset_all_ipc.py

# 수동 프로세스 종료 (필요시)
pkill -f claude_ipc_server
pkill -f monitor_instance
pkill -f auto_responder
pkill -f start_split_monitoring

# 프로세스 상태 확인
ps aux | grep -E "claude_ipc|monitor|responder"
```

### 프로젝트 메시지 초기화
```bash
# 현재 프로젝트의 모든 메시지 삭제
python tools/clear_project_messages.py

# 특정 프로젝트 ID의 메시지만 삭제
python tools/clear_project_messages.py --project-id proj_abc123

# 데이터베이스 직접 초기화 (주의: 모든 프로젝트 메시지 삭제)
sqlite3 ~/.claude-ipc-data/messages.db "DELETE FROM messages;"
```

### 전체 시스템 리셋
```bash
# 완전한 시스템 초기화 (모든 데이터 삭제)
python tools/full_system_reset.py

# 이 명령이 수행하는 작업:
# 1. 모든 IPC 프로세스 종료
# 2. 데이터베이스 초기화
# 3. 세션 정보 삭제
# 4. 캐시 파일 정리
# 5. 로그 파일 초기화
```

---

## 🧪 테스트 가이드

### 1. 기본 연결 테스트
```bash
# 단일 프로젝트 내 통신 테스트
python test/test_basic_ipc.py

# 예상 결과:
# ✅ 서버 시작 성공
# ✅ 인스턴스 등록 성공
# ✅ 메시지 전송/수신 성공
```

### 2. 프로젝트 격리 검증
```bash
# 다른 프로젝트 간 통신 차단 테스트
python test/test_project_isolation.py

# 테스트 시나리오:
# 1. 프로젝트 A에서 AI 인스턴스 생성
# 2. 프로젝트 B에서 AI 인스턴스 생성
# 3. A→B 메시지 전송 시도 (차단되어야 함)
# 4. A→A 메시지 전송 (성공해야 함)
```

### 3. 다중 AI 인스턴스 통신
```bash
# 여러 AI가 동시에 통신하는 시나리오
python test/test_multi_ai.py

# 테스트 내용:
# - Claude ↔ Gemini 양방향 통신
# - 3개 이상 인스턴스 동시 메시징
# - 브로드캐스트 메시지
# - 대용량 메시지 처리
```

### 4. 실제 응답 테스트 (NO Dummy Text)
```bash
# 더미 텍스트 없이 실제 AI 응답만 사용
python test/test_real_responses.py

# 검증 항목:
# ❌ "Lorem ipsum" 같은 더미 텍스트 금지
# ❌ "Test message 123" 같은 의미없는 텍스트 금지
# ✅ 컨텍스트 기반 실제 응답만 허용
# ✅ AI별 고유한 응답 스타일 유지
```

### 5. 전체 테스트 스위트
```bash
# pytest를 사용한 전체 테스트
python -m pytest test/ -v --tb=short

# 커버리지 포함 테스트
python -m pytest test/ --cov=src --cov-report=html

# 병렬 테스트 실행 (빠른 실행)
python -m pytest test/ -n auto
```

### 6. 통합 테스트
```bash
# 실제 AI CLI 환경 시뮬레이션
bash test/integration/test_full_workflow.sh

# 워크플로우:
# 1. 프로젝트 격리 설정
# 2. 다중 AI 인스턴스 시작
# 3. 복잡한 대화 시나리오 실행
# 4. 모니터링 검증
# 5. 자동 정리
```

---

## ⚠️ 주의사항

1. **프로젝트 이동 시**
   - 프로젝트 경로가 변경되면 ID도 변경됨
   - 기존 메시지는 접근 불가능해짐
   - 새 프로젝트 ID로 재등록 필요

2. **멀티 프로젝트 작업**
   - 각 프로젝트마다 별도 포트 사용
   - 동시에 여러 프로젝트 IPC 실행 가능
   - 프로젝트 간 통신은 불가능

3. **보안 고려사항**
   - 프로젝트 ID는 경로 해시이므로 예측 가능
   - 높은 보안이 필요하면 추가 인증 구현
   - 네트워크 격리는 localhost에만 바인딩

---

## 📝 구현 체크리스트

- [ ] 프로젝트 ID 생성 로직 구현
- [ ] 메시지에 project_id 필드 추가
- [ ] 서버에서 project_id 검증
- [ ] 프로젝트별 포트 할당
- [ ] 설정 파일 자동 생성
- [ ] 격리 상태 모니터링 도구
- [x] 문서 업데이트

---

## 🔧 문제 해결

### "Project mismatch" 오류
```bash
# 현재 프로젝트 ID 확인
python -c "from tools.project_utils import get_project_id; print(get_project_id())"

# IPC 서버 재시작
python src/claude_ipc_server.py --reset
```

### 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -an | grep 9[0-9][0-9][0-9]

# 다른 포트로 강제 지정
export IPC_PROJECT_PORT=9888
```

### 프로젝트 ID 재설정
```bash
# 설정 파일 삭제 후 재생성
rm .ipc_project.yml
python tools/init_project_isolation.py
```