# 📜 Claude IPC MCP 프로젝트 헌법 (Project Constitution)
## 제정일: 2024-09-26

---

## 제1장: 핵심 가치 (Core Values)

### 제1조 [근본 목적]
본 프로젝트의 유일한 존재 이유는 **AI CLI 간의 통신**이다.
- **SEND** (메시지 전송)
- **RECEIVE** (메시지 수신)
- **RESPOND** (자동 응답)

이 세 가지 핵심 기능 외의 모든 것은 부수적이며, 핵심 기능을 방해해서는 안 된다.

### 제2조 [절대 금지 사항]
1. **무한 루프 절대 금지** ❌
   - 모든 응답 체인은 최대 3회로 제한
   - 자기 자신에게 메시지 전송 시 자동 응답 비활성화
   - 순환 참조 감지 시 즉시 중단

2. **무분별한 파일 생성 금지** ❌
   - 테스트 파일은 즉시 삭제
   - 중복 기능 파일 생성 불가
   - 임시 파일은 24시간 후 자동 삭제

---

## 제2장: 파일 관리 헌법 (File Management Constitution)

### 제3조 [파일 생성 규칙]
```yaml
file_creation_rules:
  BEFORE_CREATE:
    - CHECK: "동일 기능 파일이 이미 존재하는가?"
    - CHECK: "핵심 기능에 필요한 파일인가?"
    - CHECK: "적절한 디렉토리가 존재하는가?"

  IF_EXISTS:
    action: "기존 파일 수정"
    never: "새 파일 생성"

  IF_NOT_EXISTS:
    require: "명확한 목적 문서화"
    location: "정확한 디렉토리 배치"
```

### 제4조 [파일 구조 체계]
```
claude-ipc-mcp/
├── src/                    # 핵심 서버 (1개 파일만 허용)
│   └── claude_ipc_server.py
├── tools/                  # 도구 스크립트 (기능당 1개)
│   ├── ipc_*.py           # IPC 기본 도구
│   ├── monitor_*.py       # 모니터링 도구
│   └── auto_*.py          # 자동화 도구
├── config/                 # 설정 파일
├── backup/                 # 백업 및 실패 코드
│   ├── failed_YYYY-MM-DD/ # 실패한 코드
│   ├── test_YYYY-MM-DD/   # 테스트 코드
│   └── success_YYYY-MM-DD/# 성공 버전 백업
└── logs/                   # 로그 파일
```

### 제5조 [파일 이름 규칙]
- **핵심 기능**: `ipc_[function].py` (예: `ipc_send.py`)
- **모니터링**: `monitor_[target].py` (예: `monitor_instance.py`)
- **자동화**: `auto_[action].py` (예: `auto_responder.py`)
- **테스트**: `test_[feature].py` → 즉시 backup/test로 이동
- **임시 파일**: `tmp_[purpose]_[timestamp]` → 24시간 후 삭제

---

## 제3장: 상태 관리 헌법 (State Management Constitution)

### 제6조 [작업 상태 표시]
```python
WORK_STATUS = {
    "✅ SUCCESS": "검증 완료, production 준비 완료",
    "🧪 TESTING": "기능 구현 완료, 검증 진행 중",
    "❌ FAILED": "오류 발생, backup 폴더로 이동",
    "🔄 IN_PROGRESS": "현재 작업 중",
    "⏸️ PAUSED": "일시 중단, 의존성 대기"
}
```

### 제7조 [상태 파일 관리]
```yaml
# .status.yml - 프로젝트 루트에 항상 유지
current_work:
  task: "현재 작업 내용"
  status: "SUCCESS|TESTING|FAILED|IN_PROGRESS|PAUSED"
  started_by: "claude|gemini|codex|human"
  started_at: "2024-09-26T10:00:00"
  last_update: "2024-09-26T11:00:00"

history:
  - task: "이전 작업"
    status: "완료 상태"
    duration: "소요 시간"
    result: "결과 요약"
```

### 제8조 [맥락 유지 프로토콜]
1. **즉시 기록**: 모든 변경사항은 5분 이내 커밋
2. **명확한 메시지**: 커밋 메시지는 [STATUS] 작업내용 형식
3. **연속성 보장**: CLAUDE.md 파일에 현재 상태 항상 업데이트
4. **인계 문서**: 작업 중단 시 `.handover.md` 파일 생성

---

## 제4장: 백업 및 복구 헌법 (Backup & Recovery Constitution)

### 제9조 [백업 정책]
```bash
# 자동 백업 트리거
ON_SUCCESS:
  - backup/success_YYYY-MM-DD/[version]/
  - git tag -a "stable-v[version]"

ON_FAILURE:
  - backup/failed_YYYY-MM-DD/[error_code]/
  - 실패 원인 문서화: failure_report.md
  - 자동 rollback 이전 stable 버전

ON_TEST:
  - backup/test_YYYY-MM-DD/[feature]/
  - 격리된 환경에서 실행
  - 메인 코드 영향 없음
```

### 제10조 [복구 프로토콜]
1. **즉시 복구**: 치명적 오류 시 마지막 SUCCESS 상태로 자동 복구
2. **격리 원칙**: 실패한 코드는 즉시 격리 (backup/failed/)
3. **영향 차단**: 실패한 모듈은 import 차단
4. **기록 유지**: 모든 복구 작업 로그 기록

---

## 제5장: 확장성 헌법 (Extensibility Constitution)

### 제11조 [모듈 확장 규칙]
```python
# 새 기능 추가 시 반드시 따를 구조
class NewFeature:
    """독립적 모듈로 구현"""

    def __init__(self):
        self.dependencies = []  # 최소 의존성
        self.affects = []       # 영향 받는 모듈 명시

    def integrate(self):
        """기존 시스템과 통합"""
        # 1. 호환성 검사
        # 2. 안전 모드 실행
        # 3. 점진적 활성화
        pass

    def rollback(self):
        """문제 발생 시 자동 롤백"""
        pass
```

### 제12조 [의존성 관리]
- **느슨한 결합**: 모듈 간 직접 의존 최소화
- **인터페이스 통신**: 정의된 API만 사용
- **버전 호환성**: 하위 호환성 항상 유지
- **격리 테스트**: 새 모듈은 격리 환경에서 먼저 검증

---

## 제6장: 통신 프로토콜 헌법 (Communication Protocol Constitution)

### 제13조 [프로젝트 격리 원칙] 🔒
**동일 프로젝트 내에서만 통신 허용**
```yaml
project_isolation:
  RULE: "같은 프로젝트 디렉토리를 바라보는 AI CLI만 통신 가능"
  PROHIBITED: "다른 프로젝트의 AI CLI와 크로스 통신 절대 금지"

  enforcement:
    - "프로젝트별 고유 네임스페이스"
    - "프로젝트 경로 해시 기반 인증"
    - "세션별 프로젝트 바인딩"
```

### 제14조 [프로젝트 네임스페이스 구현]
```python
# 프로젝트별 격리 구현 방법
PROJECT_NAMESPACE = {
    "method_1": "포트 격리",      # 프로젝트별 다른 포트
    "method_2": "경로 해시",       # 프로젝트 경로를 해시하여 ID 생성
    "method_3": "환경 변수",       # PROJECT_ID 환경변수 설정
    "method_4": "설정 파일"        # .ipc_project.yml 파일 사용
}
```

#### 구현 방법 1: 포트 격리
```yaml
# .ipc_project.yml - 프로젝트 루트에 생성
project:
  name: "my-project"
  port: 9877  # 기본 9876이 아닌 프로젝트 전용 포트
  id: "proj_abc123"  # 프로젝트 고유 ID
```

#### 구현 방법 2: 프로젝트 경로 해시
```python
import hashlib
import os

def get_project_id():
    """프로젝트 경로를 해시하여 고유 ID 생성"""
    project_path = os.getcwd()
    hash_obj = hashlib.sha256(project_path.encode())
    return hash_obj.hexdigest()[:8]  # 8자리 해시

# 등록 시 프로젝트 ID 포함
registration = {
    "instance_id": "claude",
    "project_id": get_project_id()  # 같은 프로젝트만 매칭
}
```

#### 구현 방법 3: 환경 변수 격리
```bash
# 프로젝트별 환경 설정
export IPC_PROJECT_ID="my-project-2024"
export IPC_PROJECT_PORT=9877

# AI CLI 시작 시 자동으로 해당 프로젝트 네임스페이스 사용
```

### 제15조 [메시지 규칙]
```yaml
message_rules:
  max_size: 10240  # 10KB
  max_queue: 100   # 인스턴스당 최대 100개
  ttl: 604800      # 7일 후 자동 삭제

  format:
    required: ["from_id", "to_id", "content", "timestamp", "project_id"]  # project_id 필수
    optional: ["data", "summary", "priority"]

  validation:
    - "프로젝트 ID 일치 검증"  # 새로운 검증 추가
    - "메시지 크기 검증"
    - "수신자 존재 여부 무관"
    - "발신자 인증 필수"
```

### 제16조 [응답 제한]
```python
RESPONSE_LIMITS = {
    "max_chain_length": 3,      # 최대 응답 체인
    "self_response": False,      # 자기 응답 금지
    "duplicate_check": True,     # 중복 응답 방지
    "cooldown": 1,              # 1초 쿨다운
}
```

---

## 제7장: 품질 보증 헌법 (Quality Assurance Constitution)

### 제15조 [코드 품질 기준]
1. **가독성**: 명확한 변수명, 충분한 주석
2. **안정성**: 모든 예외 처리, 타임아웃 설정
3. **성능**: 응답 시간 < 100ms, CPU 사용률 < 20%
4. **보안**: 토큰 해싱, Rate Limiting, 입력 검증

### 제16조 [검증 체크리스트]
```yaml
before_commit:
  - [ ] 기존 테스트 모두 통과
  - [ ] 새 기능 테스트 작성
  - [ ] 문서 업데이트
  - [ ] 백업 생성
  - [ ] 상태 파일 업데이트
```

---

## 제8장: 비상 프로토콜 (Emergency Protocol)

### 제17조 [위기 대응]
```bash
# 위기 상황 자동 대응
IF system_crash:
  1. 즉시 safe mode 전환
  2. 마지막 stable 버전 복구
  3. 오류 로그 backup/emergency/
  4. 관리자 알림 (있는 경우)

IF infinite_loop_detected:
  1. 프로세스 강제 종료
  2. 메시지 큐 초기화
  3. 블랙리스트 등록
  4. 재시작 후 해당 모듈 비활성화
```

### 제18조 [데이터 보호]
- **영속성 보장**: SQLite 트랜잭션 사용
- **백업 다중화**: 로컬 + 날짜별 백업
- **복구 지점**: 매 성공 작업마다 체크포인트
- **무결성 검사**: 일일 데이터베이스 검증

---

## 제9장: 거버넌스 (Governance)

### 제19조 [의사결정 구조]
1. **핵심 기능 변경**: 불가 (SEND, RECEIVE, RESPOND는 불변)
2. **확장 기능 추가**: 모듈 형태로만 허용
3. **파일 삭제**: 백업 후에만 가능
4. **구조 변경**: 마이그레이션 계획 필수

### 제20조 [헌법 개정]
- 이 헌법은 프로젝트의 근본 규칙이다
- 개정 시 `CONSTITUTION_CHANGELOG.md`에 기록
- 핵심 가치(제1장)는 개정 불가
- 나머지 조항은 합리적 사유로 개정 가능

---

## 부칙

### 시행일
이 헌법은 2024년 09월 26일부터 시행한다.

### 우선순위
1. 안정성 > 기능성
2. 단순함 > 복잡함
3. 유지보수 > 새 기능
4. 문서화 > 구현

### 강제 사항
- 모든 AI 인스턴스는 작업 시작 시 이 헌법을 읽어야 함
- 헌법 위반 코드는 즉시 거부/삭제
- 헌법 준수 여부는 커밋 전 체크리스트로 확인

---

## 🔏 서명
이 헌법은 Claude IPC MCP 프로젝트의 모든 참여자에게 적용되며,
프로젝트의 건전성과 지속가능성을 보장하기 위한 최고 규범이다.

제정: 2024-09-26
최종 수정: 2024-09-26
버전: 1.0.0

---

## 📋 Quick Reference Checklist

작업 전 확인:
- [ ] 이 헌법을 읽었는가?
- [ ] 핵심 기능에 집중하는가?
- [ ] 파일 생성이 꼭 필요한가?
- [ ] 기존 파일 수정으로 가능한가?
- [ ] 백업이 준비되었는가?

작업 후 확인:
- [ ] 상태 파일을 업데이트했는가?
- [ ] CLAUDE.md를 업데이트했는가?
- [ ] 테스트를 실행했는가?
- [ ] 불필요한 파일을 정리했는가?
- [ ] 커밋 메시지가 명확한가?