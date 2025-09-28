# AI CLI 통합 시스템 설계

## 3개 AI: Claude, Gemini, Codex

---

## 개요
여러 AI CLI (claude-cli, gemini-cli, codex-cli)를 통합하여 하나의 시스템으로 관리하는 방안

---

## 🌐 글로벌 통신 시스템 설계 (2025-01-28 Update)

### 문제 정의
현재 프로젝트 격리 정책으로 인해 서로 다른 프로젝트 폴더의 AI CLI들이 통신할 수 없는 문제가 발생. 이는 크로스 프로젝트 협업과 글로벌 AI 오케스트레이션을 불가능하게 만듦.

### Claude의 제안 - 하이브리드 통신 아키텍처

#### 1. 듀얼 모드 시스템
```yaml
communication_modes:
  global_mode:
    description: "모든 프로젝트의 AI가 자유롭게 통신"
    port: 9876  # 글로벌 고정 포트
    namespace: "global:*"
    security: "token_based_auth"

  project_mode:
    description: "같은 프로젝트 내에서만 통신"
    port_range: 9000-9999  # 프로젝트별 동적 할당
    namespace: "project:{project_id}"
    security: "project_hash_validation"

  hybrid_mode:
    description: "선택적 크로스 프로젝트 통신"
    primary: "project_mode"
    secondary: "global_mode"
    gateway: "permission_based_routing"
```

#### 2. 중앙 라우팅 아키텍처
```python
class GlobalMessageRouter:
    def __init__(self):
        self.global_broker = MessageBroker(port=9876)
        self.project_brokers = {}  # project_id -> broker
        self.routing_table = RoutingTable()

    def route_message(self, message):
        scope = message.get('scope', 'project')

        if scope == 'global':
            # 글로벌 브로커로 라우팅
            return self.global_broker.process(message)
        elif scope == 'project':
            # 프로젝트 브로커로 라우팅
            project_id = message.get('project_id')
            broker = self.get_or_create_project_broker(project_id)
            return broker.process(message)
        elif scope == 'cross':
            # 권한 확인 후 크로스 프로젝트 라우팅
            if self.verify_cross_permission(message):
                target_project = message.get('target_project')
                return self.route_to_project(target_project, message)
```

#### 3. 환경 변수 기반 모드 전환
```bash
# 글로벌 모드 활성화
export IPC_GLOBAL_MODE=true
export IPC_GLOBAL_PORT=9876

# 프로젝트 모드 (기본값)
export IPC_GLOBAL_MODE=false
export IPC_PROJECT_ISOLATION=true

# 하이브리드 모드
export IPC_HYBRID_MODE=true
export IPC_ALLOWED_PROJECTS="proj1,proj2,proj3"
```

#### 4. 보안 고려사항
- **인증**: JWT 토큰 기반 인증 추가
- **권한**: 프로젝트별 접근 권한 관리
- **암호화**: TLS 옵션 for sensitive messages
- **감사**: 모든 크로스 프로젝트 통신 로깅

#### 5. 성능 최적화
- **연결 풀링**: 프로젝트별 연결 재사용
- **메시지 큐잉**: 비동기 메시지 처리
- **캐싱**: 자주 사용되는 라우팅 경로 캐싱
- **로드 밸런싱**: 다중 브로커 인스턴스 지원

### Gemini의 피드백 (2025-01-28 업데이트)
- **보안 강화**: End-to-end 암호화 및 mutual TLS 지원 필요
- **크로스 플랫폼**: Unix 소켓과 Named Pipe 듀얼 지원
- **WSL2 최적화**: Windows-Linux 브리지 자동 감지 및 설정
- **실시간 모니터링**: 메트릭 수집 및 대시보드 통합

### Codex의 피드백 (2025-01-28 업데이트)
- **파이썬 최적화**: asyncio 기반 비동기 처리 전환
- **모듈화 강화**: 플러그인 아키텍처로 확장성 보장
- **성능 개선**: 연결 풀링 및 메시지 배치 처리
- **코드 품질**: Type hints 및 dataclasses 활용

---

## ClaudeX 통합

### 1. 중앙 IPC 아키텍처
```yaml
architecture:
  type: "centralized_message_broker"
  components:
    - ipc_server: "D:\\.ai-cli-ipc\\server.js"
    - shared_memory: "D:\\.ai-cli-ipc\\shared"
    - message_queue: "D:\\.ai-cli-ipc\\queue"
```

### 2. 환경 변수 관리
```javascript
// 환경 변수 브리지 시스템
const EnvProxy = {
  bridge: "PowerShell/CMD wrapper",
  fallback: "Local config cache",
  permissions: "Elevated when needed"
};
```

### 3. 중앙 CLI 레지스트리
```json
{
  "registry": "D:\\.ai-cli-registry",
  "cli_endpoints": {
    "claude": "npx claude-cli",
    "gemini": "gemini-cli",
    "codex": "codex-cli"
  }
}
```

---

## GeminiX 통합 (대안)

### 1. 크로스 플랫폼 지원
- WSL2 환경 지원
- PowerShell Core 활용
- Unix-like 환경 지원

### 2. 보안 강화
```yaml
security:
  - sandboxed_execution: true
  - permission_escalation: "on-demand"
  - audit_logging: enabled
```

### 3. 성능 최적화
- 멀티 프로세스 처리
- 비동기 처리
- 메모리 관리

---

## CodexX 통합 (대안)

### 1. 파이썬 기반 통합
```python
class CLIIntegrator:
    def __init__(self):
        self.env_manager = EnvironmentManager()
        self.ipc_handler = IPCHandler()
        self.cmd_executor = CommandExecutor()

    def execute_cross_cli(self, command):
        # 크로스 플랫폼 실행
        # 여러 CLI 통합
        # 결과 반환 처리
        pass
```

### 2. 확장 가능성
- 플러그인 아키텍처
- 모듈화 설계
- API 통합 지원

---

## 구현 로드맵

### Phase 1: 기본 구조 (1주)
1.  중앙 IPC 서버 구축
2.  환경 변수 브리지 시스템
3.  CLI 레지스트리 구축

### Phase 2: 통합 테스트 (30일)
1. 각 MCP 서버 통합
2. 크로스 플랫폼 테스트
3. 성능 벤치마크

### Phase 3: 고급 기능 (1개월)
1. 자동 설치 스크립트
2. GUI 관리 도구
3. 모니터링 시스템

---

## 현재 상태

**개발 진행**:
- Claude:  완료
- Gemini:  (5일 후 완료)
- Codex:  (5일 후 완료)

**다음 단계**:
1. AI CLI 설치 확인
2.  중앙 PATH 설정
3. IPC 서버 시작
4. 통합 테스트

---

## 🤝 AI 컨센서스 - 최종 합의 설계 (2025-01-28)

### 모든 AI가 동의한 최종 아키텍처

#### 1. 핵심 원칙
- **보안 우선**: 모든 통신은 인증되고 감사 가능해야 함
- **확장성**: 플러그인 아키텍처로 새로운 AI 추가 가능
- **성능**: 비동기 처리 및 캐싱으로 최적화
- **호환성**: 크로스 플랫폼 지원 (Windows, Linux, WSL2)

#### 2. 통합된 아키텍처
```python
# 최종 합의된 구조
class UnifiedIPCSystem:
    """모든 AI가 동의한 통합 IPC 시스템"""

    components = {
        'router': 'GlobalMessageRouter',      # Claude 제안
        'security': 'MutualTLSAuth',         # Gemini 제안
        'async': 'AsyncioMessageBroker',     # Codex 제안
        'monitor': 'RealtimeDashboard',      # 공동 합의
        'plugin': 'ExtensionManager'         # 확장성 보장
    }

    modes = ['global', 'project', 'hybrid']

    def __init__(self):
        self.router = GlobalMessageRouter()
        self.security = SecurityManager()
        self.broker = AsyncMessageBroker()
        self.monitor = MonitoringSystem()
        self.plugins = PluginManager()
```

#### 3. 구현 우선순위 (합의됨)
1. **Phase 1**: 기본 라우팅 및 메시징 (완료)
2. **Phase 2**: 보안 및 인증 시스템
3. **Phase 3**: 비동기 최적화 및 플러그인
4. **Phase 4**: 모니터링 및 대시보드

#### 4. 파일 구조 정리 (합의됨)
```
claude-ipc-mcp/
├── src/                    # 핵심 소스 코드
│   ├── core/              # 핵심 기능
│   │   ├── router.py      # 라우팅 시스템
│   │   ├── broker.py      # 메시지 브로커
│   │   └── security.py    # 보안 모듈
│   ├── plugins/           # 플러그인 시스템
│   └── monitoring/        # 모니터링
├── tools/                 # 유틸리티 도구
├── test/                  # 테스트 코드
├── backup/               # 이전 버전 백업
│   └── 2025-01-28/      # 날짜별 백업
└── docs/                 # 문서
```

#### 5. 제거/백업 대상 파일 (합의됨)
- 중복된 시작 스크립트들 → backup/
- 테스트용 임시 파일들 → backup/test/
- 이전 버전 구현들 → backup/old/

---

## 변경 이력
- 2024-09-28 18:14 - 초기 설계 문서 작성
- 2024-09-28 18:15 - Phase 1 구조 완료
- 2025-01-28 19:53 - AI 컨센서스 도달 및 최종 설계 합의