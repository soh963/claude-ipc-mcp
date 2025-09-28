# 🚀 다중 AI CLI 협업을 위한 IPC 설정 가이드

## 📋 목차
1. [개요](#개요)
2. [사전 준비사항](#사전-준비사항)
3. [새 프로젝트 설정](#새-프로젝트-설정)
4. [AI CLI 등록](#ai-cli-등록)
5. [연결 확인](#연결-확인)
6. [실제 사용 예시](#실제-사용-예시)
7. [문제 해결](#문제-해결)

---

## 🌟 개요

IPC(Inter-Process Communication) 시스템은 여러 AI CLI 인스턴스가 서로 통신하고 협업할 수 있게 해주는 시스템입니다. 각 AI는 고유한 능력을 가지고 있습니다:

- **Claude** (`claude`): 프로젝트 설계, 코드 리뷰, 문서화
- **Gemini** (`gemini`): 다중 모달 분석, 창의적 솔루션, 테스팅
- **Codex** (`codex`): 코드 생성, 최적화, 알고리즘
- **Local LM** (`lm`): 로컬 처리, 프라이버시 우선 작업

### 주요 특징

- **프로젝트 격리**: 각 프로젝트는 고유한 네임스페이스를 가짐
- **자동 설정**: 프로젝트 경로 기반 자동 ID 생성
- **실시간 통신**: TCP 소켓 기반 메시지 큐
- **영구 저장**: SQLite 데이터베이스 메시지 보관
- **보안**: 프로젝트간 통신 차단 (기본값)

---

## 📦 사전 준비사항

### 1. 시스템 요구사항
```bash
# 필수 소프트웨어
- Python 3.8 이상
- Git
- Node.js (일부 도구용, 선택사항)

# Python 패키지
pip install pyyaml
pip install psutil
pip install aiofiles
```

### 2. IPC 저장소 복제
```bash
# IPC 시스템 복제
git clone https://github.com/your-repo/claude-ipc-mcp.git
cd claude-ipc-mcp

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
# .bashrc 또는 .zshrc에 추가
export IPC_BASE_PATH="$HOME/claude-ipc-mcp"
export PYTHONPATH="$IPC_BASE_PATH:$PYTHONPATH"
```

---

## 🆕 새 프로젝트 설정

### 방법 1: 자동 설정 (권장)

```bash
# 한 줄로 모든 설정 완료!
python $IPC_BASE_PATH/tools/setup_new_project_ipc.py /경로/프로젝트

# 자동으로 수행되는 작업:
# ✅ 디렉토리 구조 생성
# ✅ IPC 도구 복사
# ✅ 프로젝트별 설정 생성
# ✅ 서버 시작
# ✅ 연결 테스트
# ✅ AI 인스턴스 등록
```

### 방법 2: 수동 설정

#### 1단계: 프로젝트 디렉토리 생성
```bash
# 새 프로젝트 생성
mkdir ~/내_프로젝트
cd ~/내_프로젝트

# Git 초기화 (권장)
git init
```

#### 2단계: IPC 도구 복사
```bash
# 필수 IPC 도구 복사
cp -r $IPC_BASE_PATH/tools ./tools
cp -r $IPC_BASE_PATH/src ./src
cp $IPC_BASE_PATH/requirements.txt ./

# 프로젝트 의존성 설치
pip install -r requirements.txt
```

#### 3단계: 프로젝트 설정 생성
```bash
# 프로젝트별 IPC 설정 생성
python tools/config_loader.py create
```

이렇게 하면 `.ipc_project.yml` 파일이 생성됩니다:
```yaml
project:
  name: 내_프로젝트
  id: proj_a1b2c3d4    # 경로에서 자동 생성
  port: 9234            # 프로젝트별 포트
  isolation_mode: strict
```

#### 4단계: IPC 서버 시작
```bash
# 프로젝트 격리 모드로 IPC 서버 시작
python src/claude_ipc_server.py

# 또는 한번에 모든 것을 시작 (권장)
python $IPC_BASE_PATH/start_all_ai_ipc.py
```

출력 예시:
```
🚀 IPC 서버 시작 중...
🔒 프로젝트 격리 활성: proj_a1b2c3d4 포트 9234
✅ 서버가 연결을 기다리고 있습니다
```

---

## 👥 AI CLI 등록

### 방법 1: 자동 등록 (권장)
```bash
# 프로젝트 디렉토리에서 실행:
python tools/auto_register_all.py
```

이 명령은 모든 AI 인스턴스를 자동으로 등록합니다.

### 방법 2: 각 AI별 수동 등록

#### Claude 등록
```python
# Claude Code CLI에서
from tools.ipc_register import register_instance
register_instance("claude")
```

#### Gemini 등록
```python
# Gemini CLI에서
from tools.ipc_register import register_instance
register_instance("gemini")
```

#### Codex 등록
```python
# Codex CLI에서
from tools.ipc_register import register_instance
register_instance("codex")
```

#### Local LM 등록
```python
# Local LM CLI에서
from tools.ipc_register import register_instance
register_instance("lm")
```

### 방법 3: 명령줄 사용
```bash
# 각 AI를 명령줄에서 등록
python tools/ipc_register.py claude
python tools/ipc_register.py gemini
python tools/ipc_register.py codex
python tools/ipc_register.py lm
```

---

## ✅ 연결 확인

### 1. 등록된 인스턴스 확인
```bash
python tools/ipc_list.py
```

예상 출력:
```
📋 활성 IPC 인스턴스:
  - claude@proj_a1b2c3d4 (온라인)
  - gemini@proj_a1b2c3d4 (온라인)
  - codex@proj_a1b2c3d4 (온라인)
  - lm@proj_a1b2c3d4 (온라인)
```

### 2. 통신 테스트
```bash
# 테스트 메시지 전송
python tools/ipc_send.py claude gemini "안녕하세요, 연결 테스트입니다"

# 메시지 확인
python tools/ipc_check.py gemini
```

### 3. 연결 테스트 스위트 실행
```bash
python test/test_ipc_connection.py
```

예상 결과:
```
✅ 서버 연결: 정상
✅ 인스턴스 등록: 정상
✅ 메시지 송수신: 정상
✅ 프로젝트 격리: 정상
🎉 모든 테스트 통과!
```

### 4. 시스템 상태 점검
```bash
python tools/ipc_health_check.py
```

출력 예시:
```
🏥 IPC 상태 점검 시작...
==================================================
🔍 서버 프로세스 확인...
  ✅ 서버 프로세스 발견 (PIDs: [1234])
🔌 포트 9234 접근성 확인...
  ✅ 포트 9234 접근 가능
💾 데이터베이스 상태 확인...
  ✅ 모든 필수 테이블 존재
  ✅ 데이터베이스 무결성 검사 통과
⚙️ 설정 확인...
  ✅ 설정 구조 유효
  ✅ 프로젝트 ID 일치: proj_a1b2c3d4
==================================================
🟢 전체 상태: 정상 (100%)
```

---

## 💼 실제 사용 예시

### 예시 1: 코드 리뷰 워크플로우
```python
# claude_code_review.py
from tools.ipc_client import IPCClient

# Claude 초기화
claude = IPCClient("claude")

# 리뷰할 코드
code_to_review = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
"""

# 다른 AI들에게 리뷰 요청
claude.send("gemini", f"이 코드를 리뷰해주세요:\n{code_to_review}")
claude.send("codex", f"최적화 제안을 해주세요:\n{code_to_review}")

# 피드백 수집
gemini_feedback = claude.check_messages()
codex_suggestions = claude.check_messages()

print("리뷰 결과:")
print(f"Gemini: {gemini_feedback}")
print(f"Codex: {codex_suggestions}")
```

### 예시 2: 협업 기능 개발
```python
# collaborative_development.py
from tools.ipc_client import IPCClient
import json

class ProjectCollaborator:
    def __init__(self, ai_name):
        self.client = IPCClient(ai_name)
        self.ai_name = ai_name

    def request_task(self, task_type, details):
        """다른 AI에게 특정 작업 요청"""
        message = json.dumps({
            "task": task_type,
            "details": details,
            "from": self.ai_name
        })
        return message

    def coordinate_feature(self):
        """AI 간 기능 개발 조정"""

        # Claude: 아키텍처 설계
        if self.ai_name == "claude":
            arch_design = "사용자 인증 시스템 설계"
            self.client.send("codex", self.request_task("구현", arch_design))
            self.client.send("gemini", self.request_task("테스트_계획", arch_design))
            self.client.send("lm", self.request_task("문서화", arch_design))

        # Codex: 구현
        elif self.ai_name == "codex":
            implementation = "JWT 인증 구현"
            self.client.send("claude", self.request_task("리뷰", implementation))
            self.client.send("gemini", self.request_task("테스트", implementation))

        # Gemini: 테스팅
        elif self.ai_name == "gemini":
            test_results = "모든 인증 테스트 통과"
            self.client.send("claude", self.request_task("검증", test_results))
            self.client.send("lm", self.request_task("문서_업데이트", test_results))

        # LM: 문서화
        elif self.ai_name == "lm":
            docs = "인증 문서 작성 완료"
            self.client.send("claude", self.request_task("최종_리뷰", docs))

# 협업자 초기화
claude_collab = ProjectCollaborator("claude")
claude_collab.coordinate_feature()
```

### 예시 3: 병렬 작업 실행
```python
# parallel_tasks.py
import asyncio
from tools.ipc_client import IPCClient

async def distribute_tasks():
    """여러 AI에게 작업을 병렬로 분배"""

    claude = IPCClient("claude")

    tasks = [
        ("gemini", "대시보드용 사용자 요구사항 분석"),
        ("codex", "사용자 관리용 API 엔드포인트 생성"),
        ("lm", "제품용 데이터베이스 스키마 작성"),
    ]

    # 모든 작업을 병렬로 전송
    for ai, task in tasks:
        claude.send(ai, task)
        print(f"📤 {ai}에게 전송: {task}")

    # 응답 대기
    await asyncio.sleep(5)

    # 결과 수집
    results = {}
    for ai, _ in tasks:
        messages = claude.check_messages_from(ai)
        if messages:
            results[ai] = messages[-1]['content']

    return results

# 병렬 작업 실행
results = asyncio.run(distribute_tasks())
print("📊 병렬 실행 결과:")
for ai, result in results.items():
    print(f"  {ai}: {result}")
```

### 예시 4: 실시간 모니터링 대시보드
```python
# monitoring_dashboard.py
import time
from tools.ipc_client import IPCClient

class IPCMonitor:
    def __init__(self):
        self.monitor = IPCClient("monitor")

    def display_dashboard(self):
        """실시간 IPC 활동 표시"""
        while True:
            print("\033[2J\033[H")  # 화면 지우기
            print("=" * 60)
            print("📊 IPC 모니터링 대시보드")
            print("=" * 60)

            # 모든 AI의 상태 가져오기
            instances = self.monitor.list_instances()

            for instance in instances:
                name = instance['name']
                status = "🟢 활성" if instance.get('active') else "🔴 비활성"
                last_seen = instance.get('last_seen', '없음')

                print(f"\n{name}:")
                print(f"  상태: {status}")
                print(f"  마지막 활동: {last_seen}")

                # 대기 중인 메시지 확인
                messages = self.monitor.check_messages_for(name)
                if messages:
                    print(f"  📬 대기 메시지: {len(messages)}개")

            print("\n" + "=" * 60)
            print("종료하려면 Ctrl+C를 누르세요")
            time.sleep(2)

# 모니터링 시작
monitor = IPCMonitor()
monitor.display_dashboard()
```

---

## 🛠️ 고급 설정

### 1. 프로젝트 간 통신 활성화
```yaml
# .ipc_project.yml - 프로젝트 간 통신 허용
project:
  isolation_mode: relaxed  # 'strict'에서 변경

permissions:
  allow_cross_project: true
  trusted_projects:
    - proj_xyz789  # 신뢰할 프로젝트 ID 추가
```

### 2. 사용자 정의 포트 설정
```yaml
# .ipc_project.yml - 사용자 정의 포트
network:
  host: 127.0.0.1
  port: 9500  # 사용자 정의 포트 (기본값: 자동 생성)
```

### 3. 속도 제한 조정
```yaml
# .ipc_project.yml - 속도 제한 조정
settings:
  rate_limit: 200  # 분당 메시지 수
  max_message_size: 40960  # 40KB
```

---

## 🔍 문제 해결

### 일반적인 문제와 해결책

#### 1. 연결 거부
```bash
# 서버가 실행 중인지 확인
ps aux | grep claude_ipc_server

# 서버 재시작
pkill -f claude_ipc_server
python src/claude_ipc_server.py
```

#### 2. 프로젝트 격리로 인한 메시지 차단
```bash
# 프로젝트 ID 확인
python tools/project_utils.py info

# 두 AI가 같은 프로젝트에 있는지 확인
python tools/ipc_list.py
```

#### 3. 포트가 이미 사용 중
```bash
# 포트를 사용하는 프로세스 찾기
netstat -an | grep 9234

# 프로세스 종료 또는 포트 변경
kill -9 <PID>
# 또는 .ipc_project.yml을 편집하여 다른 포트 사용
```

#### 4. 메시지가 수신되지 않음
```bash
# 메시지 큐 확인
sqlite3 ~/.claude-ipc-data/messages.db
sqlite> SELECT * FROM messages WHERE recipient='gemini' AND read_flag=0;
```

#### 5. 전체 시스템 리셋
```bash
# 모든 IPC 프로세스 초기화
python tools/reset_all_ipc.py

# 프로젝트 메시지만 삭제
python tools/clear_project_messages.py

# 데이터베이스 복구
python tools/fix_database.py
```

---

## 📡 모니터링 도구

### 1. 실시간 모니터
```bash
# 4-패널 모니터링 시작
python $IPC_BASE_PATH/start_split_monitoring.py
```

### 2. 메시지 기록
```bash
# 모든 메시지 보기
python tools/ipc_history.py --last 50
```

### 3. 성능 통계
```bash
# IPC 통계 보기
python tools/ipc_stats.py
```

---

## 🎯 모범 사례

1. **항상 프로젝트 격리 사용** - 프로젝트 간 간섭 방지
2. **시작 시 AI 등록** - 협업 전 가용성 보장
3. **타임아웃 구현** - 무한 대기 방지
4. **구조화된 메시지 사용** - 복잡한 데이터는 JSON 형식
5. **중요한 작업 로깅** - 디버깅에 도움
6. **오래된 메시지 정리** - 데이터베이스 팽창 방지
7. **속도 제한 모니터링** - 과도한 사용 시 제한 방지

---

## 📚 추가 자료

- [프로젝트 격리 가이드](PROJECT_ISOLATION_GUIDE.md)
- [IPC API 참조](API_REFERENCE.md)
- [보안 모범 사례](SECURITY.md)
- [성능 튜닝](PERFORMANCE.md)

---

**최종 업데이트**: 2025-09-28
**버전**: 1.0.0
**상태**: ✅ 프로덕션 준비 완료