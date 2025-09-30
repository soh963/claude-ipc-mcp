# 🔧 Claude IPC MCP - 전체 기능 상세 설명
## 2024-09-26

## 📌 프로젝트 개요
AI 인스턴스들이 서로 메시지를 주고받을 수 있게 하는 **AI 간 통신 시스템**

### 핵심 가치
- **비동기 통신**: 상대방이 오프라인이어도 메시지 전송 가능
- **영속성**: 메시지가 SQLite DB에 저장되어 재시작 후에도 유지
- **보안**: 세션 토큰 기반 인증, Rate Limiting
- **확장성**: 여러 AI 플랫폼 지원 (Claude, Gemini, ChatGPT 등)

---

## 🏗️ 핵심 아키텍처

### 1. TCP 브로커 시스템
```
[AI Instance A] ←→ [TCP Server :9876] ←→ [AI Instance B]
                           ↓
                    [SQLite Database]
```

---

## 📁 코드 구조 및 기능 설명

### 1️⃣ **핵심 서버: `src/claude_ipc_server.py`**

#### 주요 클래스 및 기능:

##### **RateLimiter 클래스**
```python
class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60)
```
- **기능**: API 남용 방지
- **제한**: 분당 100개 요청
- **구현**: 타임스탬프 기반 슬라이딩 윈도우

##### **MessageBroker 클래스**
```python
class MessageBroker:
    def __init__(self, host="127.0.0.1", port=9876)
```
**핵심 기능들:**
- **메시지 큐 관리**: 각 인스턴스별 메시지 큐
- **세션 관리**: SHA-256 해싱된 토큰으로 보안
- **데이터베이스 영속성**: SQLite에 모든 메시지 저장
- **이름 변경 추적**: 2시간 동안 이전 이름으로 메시지 포워딩

**주요 메서드:**
- `_init_database()`: 4개 테이블 생성 (messages, instances, sessions, name_history)
- `_process_request()`: 모든 요청 처리 (register, send, check, list, rename)
- `_hash_token()`: SHA-256으로 토큰 해싱
- `_handle_large_message()`: 10KB 이상 메시지 파일로 저장

##### **BrokerClient 클래스**
```python
class BrokerClient:
    def __init__(self, instance_id: str, host="127.0.0.1", port=9876)
```
- **기능**: 브로커와 통신하는 클라이언트
- **메서드**: `connect()`, `register()`, `send_message()`, `check_messages()`

##### **ClaudeIPCServer (MCP Server)**
- Claude Code와 통합되는 MCP 서버
- 자연어 명령 처리 ("Register as alice", "Send to bob: Hello")

---

### 2️⃣ **IPC 도구들: `tools/` 디렉토리**

#### **기본 IPC 명령 도구**

##### `ipc_register.py`
```python
def register(instance_id: str) -> str
```
- **기능**: AI 인스턴스를 시스템에 등록
- **반환**: 세션 토큰
- **사용**: `python ipc_register.py myai`

##### `ipc_send.py`
```python
def send(from_id: str, to_id: str, message: str)
```
- **기능**: 메시지 전송
- **특징**: 수신자가 등록되지 않아도 전송 가능
- **사용**: `python ipc_send.py alice bob "Hello"`

##### `ipc_check.py`
```python
def check(instance_id: str) -> List[Message]
```
- **기능**: 읽지 않은 메시지 확인
- **동작**: 메시지를 읽으면 read_flag = 1로 표시
- **사용**: `python ipc_check.py myai`

##### `ipc_list.py`
```python
def list() -> List[Instance]
```
- **기능**: 현재 등록된 모든 인스턴스 목록
- **정보**: 인스턴스 이름, 마지막 활동 시간
- **사용**: `python ipc_list.py`

##### `ipc_rename.py`
```python
def rename(old_name: str, new_name: str)
```
- **기능**: 인스턴스 이름 변경
- **특징**: 2시간 동안 이전 이름으로도 메시지 수신
- **제한**: 시간당 1회만 가능
- **사용**: `python ipc_rename.py oldname newname`

#### **고급 관리 도구**

##### `ipc_manager.py` (통합 관리자)
```python
class IPCManager:
    def register_instance(instance_id: str)
    def send_message(from_id: str, to_id: str, content: str)
    def check_messages(instance_id: str)
    def list_instances()
    def show_stats()
    def cleanup_old_messages(days: int)
```
- **기능**: 모든 IPC 기능을 하나의 도구로 관리
- **특징**:
  - 인터랙티브 모드 지원
  - 통계 및 분석 기능
  - 오래된 메시지 정리
- **사용**:
  ```bash
  python ipc_manager.py --help
  python ipc_manager.py register myai
  python ipc_manager.py send myai otherai "message"
  python ipc_manager.py stats
  ```

##### `auto_responder.py`
```python
class AutoResponder:
    def __init__(self, instance_id="claude")
    def check_for_requests()
    def generate_response(message: str)
    def run()
```
- **기능**: 자동으로 메시지에 응답
- **응답 패턴**:
  - "도움", "help" → 사용 가이드 제공
  - "상태", "status" → 시스템 상태 보고
  - "시간", "time" → 현재 시간 알림
  - 기본 → 지능적 응답 생성
- **사용**: `python auto_responder.py`

##### `monitor_instance.py`
```python
class InstanceMonitor:
    def __init__(self, instance_id: str)
    def display_messages()
    def run()
```
- **기능**: 실시간 메시지 모니터링
- **특징**:
  - 컬러 출력 (받은/보낸 메시지 구분)
  - 1초마다 새 메시지 확인
  - 통계 표시
- **사용**: `python monitor_instance.py myai`

##### `fix_database.py`
```python
def fix_database():
    # 데이터베이스 무결성 검사
    # 누락된 테이블/컬럼 복구
    # 인덱스 재구축
```
- **기능**: 데이터베이스 복구 도구
- **사용 시점**: DB 오류 발생 시

---

### 3️⃣ **모니터링 시스템: `start_split_monitoring.py`**

```python
class SplitMonitor:
    def create_terminal_layout()
    def monitor_instance(instance_id: str, color: str)
    def run_4_panel()
```

**4-Panel 모니터링 기능:**
- **레이아웃**: 2x2 그리드로 4개 인스턴스 동시 모니터
- **색상 구분**:
  - Claude: 초록색
  - Gemini: 시안색
  - Codex: 빨간색
  - LM: 노란색
- **실시간 업데이트**: 각 패널이 독립적으로 메시지 확인
- **사용**: `python start_split_monitoring.py`

---

## 🔐 보안 기능

### 1. 세션 토큰 시스템
```python
def _generate_session_token() -> str:
    return secrets.token_urlsafe(32)

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
```
- **생성**: 32바이트 암호학적 안전 토큰
- **저장**: SHA-256 해시만 DB에 저장
- **만료**: 24시간 후 자동 만료

### 2. Rate Limiting
- **인스턴스별**: 분당 100개 요청 제한
- **이름 변경**: 시간당 1회 제한
- **메시지 큐**: 수신자당 100개 제한

### 3. 파일 시스템 보안
- DB 디렉토리: 0o700 권한 (소유자만)
- DB 파일: 0o600 권한 (소유자 읽기/쓰기만)

---

## 💾 데이터베이스 구조

### 테이블 스키마

#### messages 테이블
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT,  -- JSON 추가 데이터
    summary TEXT,  -- 대용량 메시지 요약
    large_file_path TEXT,  -- 10KB+ 메시지 파일 경로
    read_flag INTEGER DEFAULT 0
)
```

#### instances 테이블
```sql
CREATE TABLE instances (
    instance_id TEXT PRIMARY KEY,
    last_seen TEXT NOT NULL
)
```

#### sessions 테이블
```sql
CREATE TABLE sessions (
    session_token_hash TEXT PRIMARY KEY,
    instance_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
)
```

#### name_history 테이블
```sql
CREATE TABLE name_history (
    old_name TEXT PRIMARY KEY,
    new_name TEXT NOT NULL,
    changed_at TEXT NOT NULL
)
```

---

## 🚀 시작 스크립트

### `start_ipc_system.bat`
```batch
@echo off
echo Starting IPC System...
cd /d D:\claude-ipc-mcp
python src/claude_ipc_server.py
```
- **기능**: MCP 서버 시작
- **용도**: Claude Code와 통합 시 사용

### `Start-IPCSystem.ps1`
```powershell
$instances = @("claude", "gemini", "codex", "lm")
foreach ($instance in $instances) {
    Start-Process python -ArgumentList "tools/auto_responder.py", $instance
}
```
- **기능**: 여러 자동 응답기 동시 실행
- **용도**: 멀티 인스턴스 환경 설정

---

## 📊 주요 기능 요약

| 기능 | 설명 | 구현 위치 |
|------|------|-----------|
| **메시지 전송** | 비동기 메시지 큐잉 | `MessageBroker._process_request()` |
| **영속성** | SQLite DB 저장 | `MessageBroker._init_database()` |
| **보안** | 토큰 기반 인증 | `MessageBroker._validate_session()` |
| **Rate Limiting** | 요청 제한 | `RateLimiter.is_allowed()` |
| **자동 응답** | 패턴 기반 응답 | `AutoResponder.generate_response()` |
| **모니터링** | 실시간 메시지 추적 | `InstanceMonitor.display_messages()` |
| **이름 변경** | 2시간 포워딩 | `MessageBroker._resolve_instance_name()` |
| **대용량 메시지** | 파일 저장 (10KB+) | `MessageBroker._handle_large_message()` |

---

## 🎯 사용 시나리오

### 1. 기본 메시징
```bash
# Alice 등록
python tools/ipc_register.py alice

# Bob에게 메시지 전송 (Bob이 오프라인이어도 OK)
python tools/ipc_send.py alice bob "Hey Bob!"

# Bob이 나중에 메시지 확인
python tools/ipc_register.py bob
python tools/ipc_check.py bob
> "Hey Bob!" - from alice
```

### 2. 자동 응답 시스템
```bash
# 자동 응답기 시작
python tools/auto_responder.py claude

# 다른 인스턴스에서 메시지 전송
python tools/ipc_send.py gemini claude "help"

# Claude가 자동으로 도움말 응답
```

### 3. 모니터링
```bash
# 4-panel 모니터 시작
python start_split_monitoring.py

# 실시간으로 4개 인스턴스의 메시지 활동 관찰
```

이것이 Claude IPC MCP 프로젝트의 전체 기능과 구현 상세입니다!