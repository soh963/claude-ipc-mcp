# 프로젝트 로컬 IPC 데이터 통합 설계

## 🎯 목표

모든 IPC 관련 데이터를 프로젝트 루트의 `.ipc/` 폴더에 저장하여, 해당 프로젝트에서 작업하는 모든 AI CLI가 항상 같은 정보와 상태를 공유하도록 함.

## 📁 새로운 디렉토리 구조

```
{project_root}/.ipc/
├── config/
│   ├── broker.json          # 브로커 설정 (호스트, 포트)
│   └── project.json         # 프로젝트 메타데이터
├── data/
│   ├── messages.db         # 메시지 저장소 (SQLite)
│   ├── instances.db        # 인스턴스 등록 정보
│   └── sessions.db         # 세션 토큰 관리
├── logs/
│   ├── broker.log          # 브로커 로그
│   ├── {instance_id}.log   # 각 인스턴스별 로그
│   └── audit.log           # 감사 로그
├── state/
│   ├── broker.pid          # 브로커 프로세스 ID
│   ├── broker.lock         # 브로커 잠금 파일
│   └── session.json        # 현재 세션 상태
└── secret/
    └── shared_secret.key   # 인증용 공유 시크릿 (옵션)
```

## 🔄 변경 사항

### 1. 데이터베이스 통합

**기존**: 3곳에 분산
- `~/.claude-ipc-data/messages.db` (전역)
- `~/.claude-ipc-data/broker.db` (전역)
- `.ipc/state/messages.db` (프로젝트, 사용 안 함)

**신규**: 1곳에 통합
- `.ipc/data/ipc.db` (단일 데이터베이스)

### 2. 단일 데이터베이스 스키마

```sql
-- 인스턴스 테이블
CREATE TABLE instances (
    instance_id TEXT PRIMARY KEY,
    project_root TEXT NOT NULL,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME NOT NULL
);

-- 세션 테이블
CREATE TABLE sessions (
    session_token_hash TEXT PRIMARY KEY,
    instance_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id)
);

-- 메시지 테이블
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    delivered INTEGER DEFAULT 0,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 이름 변경 이력
CREATE TABLE name_history (
    old_name TEXT PRIMARY KEY,
    new_name TEXT NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 브로커 초기화 프로세스

```python
def init_project_ipc(project_root: Path) -> Path:
    """프로젝트 IPC 디렉토리 초기화"""
    ipc_dir = project_root / ".ipc"

    # 디렉토리 생성
    (ipc_dir / "config").mkdir(parents=True, exist_ok=True)
    (ipc_dir / "data").mkdir(parents=True, exist_ok=True)
    (ipc_dir / "logs").mkdir(parents=True, exist_ok=True)
    (ipc_dir / "state").mkdir(parents=True, exist_ok=True)
    (ipc_dir / "secret").mkdir(parents=True, exist_ok=True)

    # 데이터베이스 초기화
    db_path = ipc_dir / "data" / "ipc.db"
    if not db_path.exists():
        init_database(db_path)

    # 설정 파일 생성
    config = {
        "project_root": str(project_root),
        "broker_host": "127.0.0.1",
        "broker_port": 9876,
        "created_at": datetime.now().isoformat()
    }
    (ipc_dir / "config" / "project.json").write_text(
        json.dumps(config, indent=2)
    )

    return ipc_dir
```

### 4. 프로젝트 감지 로직

```python
def detect_project_root() -> Path:
    """현재 작업 디렉토리에서 프로젝트 루트 찾기"""
    current = Path.cwd()

    # .git, .ipc, pyproject.toml 등으로 프로젝트 루트 감지
    markers = [".git", ".ipc", "pyproject.toml", "package.json"]

    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent

    # 마커가 없으면 현재 디렉토리를 루트로 사용
    return Path.cwd()
```

### 5. 브로커 데몬 수정

```python
class ProjectLocalBroker:
    """프로젝트 로컬 브로커"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or detect_project_root()
        self.ipc_dir = self.project_root / ".ipc"

        # .ipc 디렉토리가 없으면 초기화
        if not self.ipc_dir.exists():
            init_project_ipc(self.project_root)

        # 프로젝트별 데이터베이스 사용
        self.db_path = self.ipc_dir / "data" / "ipc.db"
        self.pid_file = self.ipc_dir / "state" / "broker.pid"
        self.log_file = self.ipc_dir / "logs" / "broker.log"

        # 로깅 설정
        self._setup_logging()

        # 설정 로드
        self.config = self._load_config()
        self.host = self.config.get("broker_host", "127.0.0.1")
        self.port = self.config.get("broker_port", 9876)
```

## 🔧 마이그레이션 전략

### 단계 1: 기존 데이터 백업
```python
def backup_global_data():
    """전역 데이터 백업"""
    global_dir = Path.home() / ".claude-ipc-data"
    backup_dir = global_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if global_dir.exists():
        shutil.copytree(global_dir, backup_dir)
        return backup_dir
    return None
```

### 단계 2: 데이터 마이그레이션
```python
def migrate_to_project_local(project_root: Path):
    """전역 데이터를 프로젝트 로컬로 마이그레이션"""
    global_db = Path.home() / ".claude-ipc-data" / "messages.db"
    project_ipc = init_project_ipc(project_root)
    project_db = project_ipc / "data" / "ipc.db"

    if global_db.exists():
        # SQLite ATTACH로 데이터 복사
        with sqlite3.connect(project_db) as conn:
            conn.execute(f"ATTACH DATABASE '{global_db}' AS global")

            # 인스턴스 복사
            conn.execute("""
                INSERT OR IGNORE INTO instances
                SELECT instance_id, ?, registered_at, last_seen
                FROM global.instances
            """, (str(project_root),))

            # 메시지 복사
            conn.execute("""
                INSERT INTO messages
                SELECT * FROM global.messages
            """)

            conn.execute("DETACH DATABASE global")
            conn.commit()
```

### 단계 3: 점진적 전환
1. **Phase 1**: 새 브로커는 `.ipc/` 사용, 기존 브로커는 그대로
2. **Phase 2**: 모든 새 등록은 `.ipc/`로
3. **Phase 3**: 기존 데이터 마이그레이션
4. **Phase 4**: 전역 디렉토리 제거 (옵션)

## 📊 장점

### 1. **프로젝트별 격리**
- 각 프로젝트는 독립적인 IPC 환경
- 프로젝트 간 간섭 없음
- 프로젝트 삭제 시 IPC 데이터도 함께 정리

### 2. **상태 일관성**
- 모든 AI CLI가 같은 `.ipc/` 사용
- 단일 데이터베이스로 동기화 문제 해결
- 프로젝트 컨텍스트 명확

### 3. **이식성**
- 프로젝트 폴더만 복사하면 IPC 환경도 함께 이동
- Git으로 `.ipc/` 제외 설정 가능 (.gitignore)
- 팀 간 공유 시 일관된 환경

### 4. **디버깅 용이**
- 프로젝트별 로그 분리
- 문제 추적 간편
- 데이터 검사 쉬움

## 🚀 구현 우선순위

1. ✅ **설계 문서 작성** (현재 문서)
2. ⏳ **ProjectLocalBroker 클래스 구현**
3. ⏳ **프로젝트 루트 감지 로직**
4. ⏳ **데이터베이스 통합**
5. ⏳ **마이그레이션 도구**
6. ⏳ **테스트 및 검증**

## 🔍 호환성

- **기존 코드**: broker_client API는 동일하게 유지
- **CLI 명령어**: 기존 명령어 그대로 사용
- **MCP 도구**: 변경 없음
- **자동 감지**: 프로젝트 루트 자동 인식

## 📝 사용 예시

```python
# 자동으로 프로젝트 루트 감지하고 .ipc/ 사용
from src.core import broker_client

# 등록 (자동으로 현재 프로젝트 .ipc/ 사용)
session = broker_client.register('claude-instance')

# 메시지 전송 (같은 프로젝트 .ipc/ 공유)
broker_client.send(session['session_token'], 'claude', 'gemini', 'Hello!')
```

## 🎯 성공 기준

- [ ] 모든 AI CLI가 같은 인스턴스 목록 확인
- [ ] 메시지 전송/수신 100% 성공률
- [ ] 프로젝트 간 격리 확인
- [ ] 기존 기능 모두 정상 작동
- [ ] 성능 저하 없음 (<5% 허용)
