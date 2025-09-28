# 🌐 글로벌 IPC 합의 문서
## 📅 작성일: 2025-09-28 21:30
## 👥 참여자: Claude, Gemini, Codex

---

## 🎯 최종 합의: 하이브리드 글로벌 IPC 아키텍처

### 핵심 결정사항

1. **글로벌 서버 접근법**: 시스템 서비스 + 온디맨드 하이브리드
2. **네임스페이스 전략**: 프로젝트 격리 + 선택적 글로벌 노출
3. **인증 방식**: JWT 토큰 + 프로젝트 키 조합
4. **메시지 라우팅**: 중앙 라우터 + P2P 백업

---

## 💬 AI 합의 내용

### 🔵 Claude의 제안 (채택됨)

**글로벌 싱글톤 서버 아키텍처**:
```python
# ~/.global-ipc/server_config.json
{
    "server": {
        "host": "localhost",
        "port": 9876,
        "type": "singleton",
        "auto_start": true
    },
    "namespace": {
        "strategy": "hybrid",
        "global": "ai.ipc.global",
        "project": "ai.ipc.project.{project_hash}"
    },
    "auth": {
        "method": "jwt_with_project_key",
        "token_lifetime": 86400,
        "project_key_required": true
    }
}
```

### 🟢 Gemini의 보안 분석 (반영됨)

**보안 요구사항**:
1. **프로젝트 격리 유지**: 기본적으로 프로젝트 간 통신 차단
2. **명시적 권한 부여**: 글로벌 통신은 명시적 승인 필요
3. **감사 로깅**: 모든 크로스-프로젝트 통신 기록
4. **토큰 기반 인증**: JWT + 프로젝트 고유 키 조합

```python
class SecurityManager:
    def validate_cross_project_access(self, from_project, to_project, message):
        # 1. 프로젝트 키 검증
        if not self.verify_project_key(from_project):
            return False

        # 2. 권한 매트릭스 확인
        if not self.check_permission_matrix(from_project, to_project):
            return False

        # 3. 메시지 검증
        if not self.validate_message_content(message):
            return False

        # 4. 감사 로그 기록
        self.audit_log.record(from_project, to_project, message)

        return True
```

### 🟠 Codex의 성능 최적화 (구현됨)

**성능 전략**:
1. **메시지 큐 분산**: 프로젝트별 큐 + 글로벌 우선순위 큐
2. **비동기 처리**: asyncio 기반 완전 비동기 아키텍처
3. **커넥션 풀링**: 프로젝트당 최대 10개 연결
4. **캐싱 전략**: 자주 사용되는 라우팅 정보 캐싱

```python
class PerformanceOptimizer:
    async def route_message(self, message):
        # 1. 캐시 확인
        if cached_route := await self.cache.get_route(message.to_id):
            return await self.send_cached(cached_route, message)

        # 2. 병렬 라우팅 검색
        routes = await asyncio.gather(
            self.find_local_route(message),
            self.find_global_route(message),
            self.find_p2p_route(message)
        )

        # 3. 최적 경로 선택
        best_route = self.select_best_route(routes)

        # 4. 캐시 업데이트
        await self.cache.set_route(message.to_id, best_route)

        return await self.send_optimized(best_route, message)
```

---

## 🚀 구현 계획

### Phase 1: 글로벌 서버 설정 (즉시)

```bash
# 1. 글로벌 IPC 서버 설치
pip install global-ipc-server

# 2. 시스템 환경 변수 설정
export GLOBAL_IPC_HOST="localhost"
export GLOBAL_IPC_PORT="9876"
export GLOBAL_IPC_MODE="hybrid"

# 3. 서버 시작
python ~/.global-ipc/start_global_server.py
```

### Phase 2: 프로젝트별 설정 (각 프로젝트)

```python
# 각 프로젝트의 .claude/ipc_config.json
{
    "mode": "hybrid",
    "server": {
        "host": "localhost",
        "port": 9876
    },
    "project": {
        "id": "auto_generated_hash",
        "name": "claude-ipc-mcp",
        "visibility": "project"  # project | global | selective
    },
    "permissions": {
        "allow_from": ["trusted_project_1", "trusted_project_2"],
        "allow_to": ["all"],  # all | specific_list
        "require_auth": true
    }
}
```

### Phase 3: 통합 테스트

```python
# test_global_ipc.py
async def test_cross_project_communication():
    # 프로젝트 A 클라이언트
    client_a = GlobalIPCClient(
        project="claude-ipc-mcp",
        config_path="D:/claude-ipc-mcp/.claude/ipc_config.json"
    )

    # 프로젝트 B 클라이언트
    client_b = GlobalIPCClient(
        project="test-tem",
        config_path="D:/test-tem/.claude/ipc_config.json"
    )

    # 등록
    await client_a.register("claude")
    await client_b.register("gemini")

    # 크로스-프로젝트 메시지 전송
    result = await client_a.send(
        to="gemini@test-tem",
        message="Cross-project test message",
        require_auth=True
    )

    assert result.status == "delivered"
    assert result.project_validated == True
```

---

## 📊 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────┐
│            글로벌 IPC 서버 (Port 9876)          │
│                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │  Router   │  │  Security │  │   Cache   │  │
│  └───────────┘  └───────────┘  └───────────┘  │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │        Message Queue Manager            │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐│   │
│  │  │Project A│  │Project B│  │ Global  ││   │
│  │  │  Queue  │  │  Queue  │  │  Queue  ││   │
│  │  └─────────┘  └─────────┘  └─────────┘│   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Project A   │ │  Project B   │ │  Project C   │
│claude-ipc-mcp│ │  test-tem    │ │  other-proj  │
│              │ │              │ │              │
│ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │
│ │  Claude  │ │ │ │  Gemini  │ │ │ │  Codex   │ │
│ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## ✅ 합의된 핵심 기능

### 1. 프로젝트 네임스페이스
- **격리 모드**: `claude@project:claude-ipc-mcp`
- **글로벌 모드**: `claude@global`
- **하이브리드**: `claude` (컨텍스트에 따라 자동 결정)

### 2. 메시지 라우팅 규칙
```python
def resolve_recipient(to_id: str, from_project: str) -> str:
    # 1. 명시적 프로젝트 지정
    if "@" in to_id and ":" in to_id:
        return to_id  # gemini@project:test-tem

    # 2. 글로벌 명시
    if to_id.endswith("@global"):
        return to_id  # gemini@global

    # 3. 같은 프로젝트 우선
    if local_instance := find_in_project(to_id, from_project):
        return f"{to_id}@project:{from_project}"

    # 4. 글로벌 검색 (권한 있을 때)
    if global_instance := find_global(to_id):
        return f"{to_id}@global"

    # 5. 실패
    raise RecipientNotFound(to_id)
```

### 3. 보안 매트릭스
| From\To | Same Project | Different Project | Global |
|---------|--------------|-------------------|--------|
| Project | ✅ Always    | ⚠️ With Permission | ⚠️ With Permission |
| Global  | ✅ Always    | ✅ Always         | ✅ Always |

### 4. 성능 목표
- **메시지 지연**: < 10ms (같은 프로젝트), < 50ms (크로스 프로젝트)
- **처리량**: 10,000 msg/sec
- **동시 연결**: 1,000 clients
- **캐시 히트율**: > 80%

---

## 🔧 구현 파일

### 1. 글로벌 서버 (`~/.global-ipc/global_server.py`)
```python
import asyncio
from pathlib import Path
from typing import Dict, Optional
import json
import hashlib

class GlobalIPCServer:
    def __init__(self):
        self.config_path = Path.home() / '.global-ipc'
        self.config_path.mkdir(exist_ok=True)
        self.port = 9876
        self.projects: Dict[str, ProjectConfig] = {}
        self.instances: Dict[str, InstanceInfo] = {}

    async def start(self):
        """글로벌 서버 시작"""
        server = await asyncio.start_server(
            self.handle_client,
            'localhost',
            self.port
        )

        print(f"🌐 Global IPC Server started on port {self.port}")

        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        """클라이언트 요청 처리"""
        try:
            data = await reader.read(65536)
            request = json.loads(data.decode())

            response = await self.process_request(request)

            writer.write(json.dumps(response).encode())
            await writer.drain()

        finally:
            writer.close()
            await writer.wait_closed()

    async def process_request(self, request):
        """요청 처리 및 라우팅"""
        request_type = request.get('type')

        if request_type == 'register':
            return await self.handle_registration(request)
        elif request_type == 'send':
            return await self.handle_message(request)
        elif request_type == 'list':
            return await self.handle_list(request)
        else:
            return {'status': 'error', 'message': 'Unknown request type'}
```

### 2. 프로젝트 클라이언트 (`src/global_ipc_client.py`)
```python
class GlobalIPCClient:
    def __init__(self, project: str, config_path: str = None):
        self.project = project
        self.project_hash = hashlib.sha256(project.encode()).hexdigest()[:8]
        self.config = self.load_config(config_path)
        self.instance_id = None

    async def register(self, name: str, visibility: str = "project"):
        """인스턴스 등록"""
        request = {
            'type': 'register',
            'name': name,
            'project': self.project,
            'project_hash': self.project_hash,
            'visibility': visibility
        }

        response = await self.send_request(request)

        if response['status'] == 'ok':
            self.instance_id = response['instance_id']

        return response

    async def send(self, to: str, message: str, require_auth: bool = True):
        """메시지 전송"""
        request = {
            'type': 'send',
            'from': self.instance_id,
            'to': to,
            'message': message,
            'project': self.project,
            'require_auth': require_auth
        }

        return await self.send_request(request)
```

---

## 🎉 합의 결과

### ✅ 모든 AI 동의 사항
1. **하이브리드 접근법**: 프로젝트 격리 + 선택적 글로벌 노출
2. **중앙 서버 아키텍처**: 포트 9876의 글로벌 싱글톤 서버
3. **보안 우선**: JWT + 프로젝트 키 조합 인증
4. **성능 최적화**: 비동기 처리 + 캐싱 + 커넥션 풀링
5. **점진적 마이그레이션**: 기존 프로젝트별 IPC와 호환

### 📝 다음 단계
1. 글로벌 서버 구현 (`global_server.py`)
2. 클라이언트 라이브러리 구현 (`global_ipc_client.py`)
3. 통합 테스트 작성
4. 문서화 및 배포

---

**합의 완료**: 2025-09-28 21:35
**참여자 서명**: Claude ✅, Gemini ✅, Codex ✅