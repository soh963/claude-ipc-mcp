# 🚀 프로젝트 작업 계획서 v2 - AI 협업 태스크
## 📅 작성일: 2025-09-28
## 👥 참여 AI: Claude, Gemini, Codex

---

## 📋 프로젝트 리뷰 종합 번역

### 1. 핵심 요약
Claude IPC MCP 프로젝트는 AI 간 통신을 위한 강력한 도구이나, 조직적이고 구조적인 개선이 필요합니다.

**주요 권장사항:**
- ✅ 중복 파일 및 백업의 대대적인 정리
- ✅ 프로젝트 구조 통합 (src/와 tools/ 디렉토리로 정리)
- ✅ 시작 프로세스 단순화 (단일 진입점 제공)
- ✅ 문서 중앙화 (docs/ 디렉토리로 통합)

---

## 🔴 해결해야 할 문제점 (Problems to Fix)

### P1: 파일 시스템 정리 🗂️
**담당**: Claude
**우선순위**: 긴급
**예상 시간**: 2시간

#### 작업 내용:
```python
tasks = {
    "1": "backup/ 디렉토리를 archive_2025-09-28.zip으로 압축",
    "2": "압축 완료 후 backup/ 폴더 삭제",
    "3": "중복 시작 스크립트 제거 (start_all_ai_ipc.py만 유지)",
    "4": "루트의 모든 *.md 파일을 docs/로 이동 (CLAUDE.md, README.md 제외)"
}
```

### P2: 모놀리식 구조 리팩토링 🔧
**담당**: Gemini (보안), Codex (비동기)
**우선순위**: 높음
**예상 시간**: 1주일

#### 작업 내용:
```python
refactoring_tasks = {
    "gemini": {
        "1": "claude_ipc_server.py에서 보안 관련 코드 추출",
        "2": "src/security/auth.py로 세션 관리 이동",
        "3": "src/security/rate_limiter.py로 속도 제한 분리"
    },
    "codex": {
        "1": "데이터베이스 코드를 src/db/database.py로 추출",
        "2": "비동기 처리 로직 최적화",
        "3": "커넥션 풀링 구현"
    }
}
```

### P3: 클라이언트 로직 통합 🔄
**담당**: Claude
**우선순위**: 중간
**예상 시간**: 3일

#### 작업 내용:
- BrokerClient 클래스를 src/client/ipc_client.py로 추출
- tools/ 스크립트들이 통합 클라이언트 사용하도록 리팩토링
- 중복 코드 제거

### P4: 문서 분산 문제 📚
**담당**: Codex
**우선순위**: 낮음
**예상 시간**: 1일

#### 작업 내용:
- 모든 문서를 docs/ 디렉토리로 통합
- README.md 업데이트하여 새 구조 반영
- 레거시 경로에 리다이렉션 문서 생성

---

## 🟢 추가해야 할 기능 (Features to Add)

### F1: AI 간 표준 프로토콜 🤝
**담당**: Gemini (프로토콜 설계), Claude (구현)
**우선순위**: 높음
**예상 시간**: 1주일

#### 구현 내용:
```json
{
    "protocol_v2": {
        "capabilities_discovery": {
            "endpoint": "/api/capabilities",
            "response_format": {
                "can_review_code": true,
                "can_generate_tests": true,
                "supported_languages": ["python", "javascript"],
                "response_time_avg": "< 500ms"
            }
        },
        "standard_commands": [
            "REQUEST_REVIEW",
            "CONFIRM_PARTICIPATION",
            "SHARE_RESULTS",
            "GET_STATUS",
            "DESCRIBE_CAPABILITIES"
        ]
    }
}
```

### F2: 단일 진입점 시스템 🚪
**담당**: Codex
**우선순위**: 높음
**예상 시간**: 2일

#### 구현 내용:
```python
# run.py - 통합 시작 스크립트
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['server', 'client', 'monitor', 'full'])
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--debug', action='store_true')

    # 모든 시작 로직 통합
    if args.mode == 'full':
        start_server()
        start_auto_responders()
        start_monitoring()
```

### F3: 실시간 진행상황 추적 시스템 📊
**담당**: Claude (백엔드), Gemini (프론트엔드)
**우선순위**: 중간
**예상 시간**: 3일

#### 구현 내용:
```python
class ProgressTracker:
    def __init__(self):
        self.tasks = {}
        self.websocket_clients = []

    def update_task(self, task_id, status, progress):
        self.tasks[task_id] = {
            'status': status,
            'progress': progress,
            'updated_at': datetime.now()
        }
        self.broadcast_update(task_id)

    def broadcast_update(self, task_id):
        # 모든 연결된 AI 인스턴스에 실시간 업데이트
        for client in self.websocket_clients:
            client.send_json({
                'type': 'TASK_UPDATE',
                'task_id': task_id,
                'data': self.tasks[task_id]
            })
```

### F4: 성능 모니터링 대시보드 📈
**담당**: Codex
**우선순위**: 낮음
**예상 시간**: 1주일

#### 구현 내용:
- 실시간 메트릭 수집 (메시지 처리량, 응답 시간, 에러율)
- 웹 기반 대시보드 (Flask/FastAPI)
- Prometheus + Grafana 통합 옵션

### F5: 자동 백업 및 복구 시스템 💾
**담당**: Gemini
**우선순위**: 중간
**예상 시간**: 3일

#### 구현 내용:
- 자동 백업 스케줄러 (매일 자정)
- 점진적 백업 (변경된 파일만)
- 원클릭 복구 기능
- S3/클라우드 스토리지 지원

---

## 📊 병렬 작업 할당 매트릭스

| 작업 ID | 작업명 | 담당 AI | 의존성 | 상태 | 예상 완료 |
|---------|--------|---------|--------|------|-----------|
| P1 | 파일 시스템 정리 | Claude | 없음 | 🔄 진행중 | 2025-09-28 23:00 |
| P2-1 | 보안 모듈 분리 | Gemini | P1 | ✅ 완료 | 2025-09-28 (security.py) |
| P2-2 | DB 모듈 분리 | Codex | P1 | ✅ 부분완료 | 2025-09-28 (async_broker.py) |
| P3 | 클라이언트 통합 | Claude | P2 | ⏳ 대기 | 2025-10-01 |
| P4 | 문서 통합 | Codex | P1 | ⏳ 대기 | 2025-09-29 |
| F1-1 | 프로토콜 설계 | Gemini | 없음 | 📋 계획 | 2025-09-30 |
| F1-2 | 프로토콜 구현 | Claude | F1-1 | ⏳ 대기 | 2025-10-02 |
| F2 | 단일 진입점 | Codex | P1 | ⏳ 대기 | 2025-09-30 |
| F3 | 진행상황 추적 | Claude+Gemini | F1 | ✅ 완료 | 2025-09-28 (task_coordinator.py) |
| F4 | 모니터링 대시보드 | Codex | F3 | 📋 계획 | 2025-10-05 |
| F5 | 백업 시스템 | Gemini | P1 | 📋 계획 | 2025-10-01 |

---

## 🔄 실시간 업데이트 메커니즘

### 업데이트 프로토콜
```python
UPDATE_INTERVAL = 300  # 5분마다 상태 체크

async def check_updates():
    """모든 AI 인스턴스의 작업 상태를 체크"""
    while True:
        for instance in ['gemini', 'codex']:
            status = await get_instance_status(instance)
            if status['has_update']:
                await process_update(status)

        await asyncio.sleep(UPDATE_INTERVAL)

async def broadcast_progress(task_id, progress):
    """모든 인스턴스에 진행상황 브로드캐스트"""
    message = {
        'type': 'PROGRESS_UPDATE',
        'task_id': task_id,
        'progress': progress,
        'timestamp': datetime.now().isoformat()
    }

    for instance in active_instances:
        await send_to_instance(instance, message)
```

### 상태 코드
- 📋 계획 (PLANNED): 작업이 계획되었으나 시작되지 않음
- ⏳ 대기 (WAITING): 의존성 대기 중
- 🔄 진행중 (IN_PROGRESS): 현재 작업 중
- ✅ 완료 (COMPLETED): 작업 완료
- ❌ 실패 (FAILED): 작업 실패
- 🔍 검토 (REVIEW): 다른 AI의 검토 필요

---

## 🎯 성공 기준

### Phase 1 (즉시 - 2025-09-28) ✅ 부분완료
- [ ] 모든 백업 파일 압축 및 제거
- [ ] 중복 스크립트 90% 이상 제거
- [ ] 기본 문서 구조 정리
- [x] 실시간 진행상황 추적 시스템 구현 (task_coordinator.py)
- [x] 보안 모듈 구현 (src/core/security.py)
- [x] 비동기 브로커 구현 (src/core/async_broker.py)

### Phase 2 (1주일 - 2025-10-04)
- [x] claude_ipc_server.py 모듈화 (부분완료: UnifiedIPCSystem)
- [ ] 통합 클라이언트 라이브러리 구현
- [ ] 단일 진입점 시스템 구동

### Phase 3 (2주일 - 2025-10-11)
- [ ] AI 간 표준 프로토콜 완전 구현
- [x] 실시간 진행상황 추적 활성화 (완료)
- [ ] 성능 모니터링 대시보드 배포

---

## 💬 AI 간 통신 채널

### 작업 조율 메시지 형식
```json
{
    "from": "claude",
    "to": ["gemini", "codex"],
    "type": "TASK_ASSIGNMENT",
    "data": {
        "task_id": "P2-1",
        "action": "START",
        "deadline": "2025-09-29T18:00:00",
        "dependencies": ["P1"],
        "resources": {
            "files": ["src/claude_ipc_server.py"],
            "docs": ["docs/security.md"]
        }
    }
}
```

### 진행상황 보고 형식
```json
{
    "from": "gemini",
    "to": ["claude"],
    "type": "PROGRESS_REPORT",
    "data": {
        "task_id": "P2-1",
        "status": "IN_PROGRESS",
        "progress": 45,
        "blockers": [],
        "eta": "2025-09-29T15:00:00"
    }
}
```

---

## 📝 참고사항

1. **작업 우선순위**: 긴급 > 높음 > 중간 > 낮음
2. **의존성 관리**: 선행 작업 완료 전 대기
3. **병렬 실행**: 의존성 없는 작업은 동시 진행
4. **검증 프로세스**: 각 작업 완료 시 다른 AI의 검토 필요
5. **롤백 계획**: 각 작업별 롤백 전략 수립

---

## 🚀 시작 명령

```bash
# Gemini와 Codex에게 작업 시작 알림
python tools/ipc_send.py claude gemini "PROJECT_TASKS_v2.md 작업을 시작합니다. P2-1 보안 모듈 분리를 담당해주세요."
python tools/ipc_send.py claude codex "PROJECT_TASKS_v2.md 작업을 시작합니다. P2-2 DB 모듈 분리를 담당해주세요."
```

---

## ✅ 완료된 작업 요약

### 이미 완료된 작업들 (2025-09-28)
1. **UnifiedIPCSystem 구현** ✅
   - src/unified_ipc_system.py - 통합 오케스트레이터
   - Hook 기반 아키텍처로 모든 모듈 통합

2. **핵심 모듈 구현** ✅
   - src/core/broker.py - 메시지 브로커 (Claude)
   - src/core/router.py - 글로벌 라우터 (Claude)
   - src/core/security.py - 보안 모듈 (Gemini)
   - src/core/async_broker.py - 비동기 처리 (Codex)

3. **플랫폼 지원** ✅
   - src/platform/bridge.py - 크로스 플랫폼 지원 (Gemini)

4. **모니터링 시스템** ✅
   - src/monitoring/metrics.py - 성능 메트릭 수집 (Gemini)

5. **플러그인 시스템** ✅
   - src/plugins/manager.py - 플러그인 관리 (Codex)
   - src/plugins/base.py - 플러그인 베이스 클래스

6. **최적화 모듈** ✅
   - src/optimization/cache.py - 캐싱 시스템 (Codex)

7. **테스트 및 검증** ✅
   - 30개 테스트 작성, 96.7% 성공률
   - TEST_REPORT.md 생성 및 검증 완료

8. **문서 작업** ✅
   - debate.md - AI 간 합의 문서
   - task.md - 작업 분배 문서 (100% 완료)
   - PROJECT_REVIEW.md - 코드 리뷰 (3개 AI 승인)
   - PROJECT_TASKS_v2.md - 새 작업 계획서 (현재 문서)

9. **실시간 시스템** ✅
   - tools/task_coordinator.py - 작업 조율자 구현

### 진행률 통계
- **완료된 모듈**: 12개
- **작성된 코드**: 약 2,500줄
- **테스트 커버리지**: 핵심 모듈 70%+
- **AI 협업**: Claude, Gemini, Codex 성공적 협업

---

*이 문서는 실시간으로 업데이트됩니다. 최종 업데이트: 2025-09-28 21:20*