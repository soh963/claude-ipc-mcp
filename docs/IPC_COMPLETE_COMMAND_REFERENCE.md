# IPC Complete Command Reference

## 📚 전체 명령어 목록

### 기본 명령어 (Top-level Commands)

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ipc init` | 프로젝트 .ipc/ 폴더 초기화 | `ipc init` |
| `ipc status` | IPC 시스템 전체 상태 확인 | `ipc status` |
| `ipc ping` | 브로커 연결 테스트 | `ipc ping` |
| `ipc chat` | 메시지 전송 (fire and forget) | `ipc chat --to gemini "hello"` |
| `ipc doctor` | 시스템 진단 및 문제 해결 | `ipc doctor` |
| `ipc register` | 현재 프로젝트를 인스턴스로 등록 | `ipc register claude` |

### 브로커 관리 (ipc broker)

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ipc broker start` | 글로벌 브로커 시작 (포트 9876) | `ipc broker start` |
| `ipc broker stop` | 브로커 종료 | `ipc broker stop` |
| `ipc broker status` | 브로커 상태 확인 | `ipc broker status` |

### 인스턴스 관리 (ipc instances)

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ipc instances list` | 인스턴스 목록 (간단) | `ipc instances list` |
| `ipc instances list --full` | 인스턴스 목록 (상세) | `ipc instances list --full` |
| `ipc instances delete` | 특정 인스턴스 삭제 | `ipc instances delete codex` |
| `ipc instances reset` | 모든 인스턴스 삭제 | `ipc instances reset` |

### 메시지 관리 (ipc messages)

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ipc messages clear --force` | 모든 메시지 삭제 | `ipc messages clear --force` |

### 양방향 통신 (ipc ask)

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ipc ask --to <target> "<prompt>"` | 메시지 전송 후 응답 대기 | `ipc ask --to gemini "상태?" --timeout 10` |
| `--timeout <seconds>` | 대기 시간 설정 (기본값: 30초) | `--timeout 15` |
| `--poll-interval <seconds>` | 폴링 간격 (기본값: 1초) | `--poll-interval 2` |
| `--corr <id>` | 커스텀 상관 ID | `--corr my-request-123` |

### 자동 응답기 (ipc responder)

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ipc responder start` | 응답기 시작 | `ipc responder start gemini --policy smart --detach` |
| `ipc responder start-all` | 모든 응답기 시작 | `ipc responder start-all --policy smart` |
| `ipc responder stop` | 응답기 종료 | `ipc responder stop gemini` |
| `ipc responder stop-all` | 모든 응답기 종료 | `ipc responder stop-all` |
| `ipc responder status` | 응답기 상태 확인 | `ipc responder status gemini` |

#### 응답기 옵션
- `--policy <simple|smart>`: 응답 정책 (기본값: smart)
- `--detach`: 백그라운드 실행

### 세션 관리 (ipc session)

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `ipc session` | 현재 세션 정보 확인 | `ipc session` |
| `ipc session clear` | 현재 세션 클리어 | `ipc session clear` |

## 🎯 명령어별 상세 설명

### 1. ipc init

**기능**: 현재 프로젝트에 `.ipc/` 폴더 생성

**생성 구조**:
```
.ipc/
├── config/          # 설정 파일
├── logs/            # 로그 파일
├── state/           # 세션 상태
└── secret/          # 인증 정보
```

**사용 시기**:
- 프로젝트를 IPC 시스템에 통합할 때 (최초 1회)
- 선택사항이지만 권장

### 2. ipc broker start/stop/status

**기능**: 글로벌 메시지 브로커 관리

**브로커 역할**:
- TCP 서버 (포트 9876)
- 모든 인스턴스 간 메시지 중계
- SQLite 기반 메시지 영속화
- 세션 관리 및 인증

**필수 여부**: ⭐ 필수 - 브로커 없이는 통신 불가능

### 3. ipc register <instance_name>

**기능**: 현재 프로젝트를 IPC 인스턴스로 등록

**동작**:
1. 브로커에 연결
2. 세션 토큰 발급 받음
3. 메시지 송수신 가능 상태

**명명 규칙**:
- 1-32자 길이
- 영문, 숫자, dash(-), underscore(_) 사용 가능
- 예: `claude-main`, `codex_worker`, `gemini-assistant`

### 4. ipc status

**기능**: 전체 시스템 상태 확인

**표시 정보**:
- 브로커 연결 상태
- 등록된 인스턴스 수
- 현재 세션 정보
- 활성 응답기 상태

### 5. ipc instances list

**기능**: 등록된 인스턴스 목록 조회

**옵션**:
- 기본: 인스턴스 이름만 표시
- `--full`: 브로커 상태, 응답기 상태 포함

**출력 예시**:
```
📊 Unified Instance Status (2 instance(s)):

  Instance: claude-debate
    Broker:    ✓ Registered
    Responder: ✗ Not running

  Instance: test-tem-main
    Broker:    ✓ Registered
    Responder: ✗ Not running
```

### 6. ipc chat --to <target> "<message>"

**기능**: 단방향 메시지 전송 (응답 대기 안 함)

**사용 사례**:
- 작업 완료 알림
- 상태 업데이트 공유
- 일방적 명령 전송

**예시**:
```bash
ipc chat --to gemini "빌드 완료"
ipc chat --to codex "src/main.py 리뷰 부탁"
ipc chat --to team-lead "배포 준비 완료"
```

### 7. ipc ask --to <target> "<prompt>"

**기능**: 양방향 통신 (응답 대기)

**동작**:
1. 메시지 전송
2. 상대방 응답 대기 (폴링)
3. 응답 수신 시 출력
4. 타임아웃 시 종료

**옵션**:
- `--timeout <seconds>`: 최대 대기 시간 (기본 30초)
- `--poll-interval <seconds>`: 폴링 간격 (기본 1초)
- `--corr <id>`: 커스텀 상관 ID

**예시**:
```bash
# 10초 대기
ipc ask --to gemini "상태 확인해줘" --timeout 10

# 빠른 폴링 (0.5초마다)
ipc ask --to codex "테스트 통과?" --timeout 5 --poll-interval 0.5
```

### 8. ipc responder start <instance>

**기능**: 자동 응답기 시작

**응답 정책**:
- `simple`: 모든 메시지에 에코 응답
- `smart`: 컨텍스트 기반 지능형 응답 (기본값)

**옵션**:
- `--policy <simple|smart>`: 응답 정책 선택
- `--detach`: 백그라운드 실행 (권장)

**예시**:
```bash
# 스마트 응답기 백그라운드 실행
ipc responder start gemini --policy smart --detach

# 모든 인스턴스 응답기 일괄 시작
ipc responder start-all --policy smart
```

### 9. ipc responder status <instance>

**기능**: 응답기 상태 확인

**표시 정보**:
- 실행 여부 (Running/Not running)
- PID (프로세스 ID)
- 시작 시간
- 마지막 체크 시간
- 응답 정책

### 10. ipc instances delete/reset

**기능**: 인스턴스 삭제

**차이점**:
- `delete <name>`: 특정 인스턴스만 삭제
- `reset`: 모든 인스턴스 삭제 (시스템 초기화)

**주의**: 삭제 시 세션 정보도 함께 제거됨

### 11. ipc messages clear --force

**기능**: 모든 메시지 삭제

**주의**:
- 복구 불가능
- `--force` 플래그 필수 (실수 방지)

### 12. ipc doctor

**기능**: 시스템 진단 및 자동 복구

**검사 항목**:
- 브로커 연결 상태
- 데이터베이스 무결성
- 설정 파일 유효성
- 포트 충돌 확인
- 권한 문제 확인

**자동 복구**:
- 손상된 데이터베이스 수정
- 누락된 디렉토리 생성
- 잘못된 권한 수정

## 🔧 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `IPC_HOST` | 브로커 호스트 | `127.0.0.1` |
| `IPC_GLOBAL_PORT` | 브로커 포트 | `9876` |
| `IPC_SHARED_SECRET` | 인증 암호 (선택) | (없음) |
| `IPC_RESPONDER_POLICY` | 기본 응답기 정책 | `smart` |

**설정 방법**:
```bash
# Windows PowerShell
$env:IPC_GLOBAL_PORT="8877"

# Windows CMD
set IPC_GLOBAL_PORT=8877

# Linux/Mac
export IPC_GLOBAL_PORT=8877
```

## 📋 명령어 체크리스트

### 필수 설정 (Setup)
- [ ] `ipc init` - 프로젝트 초기화
- [ ] `ipc broker start` - 브로커 시작
- [ ] `ipc register <name>` - 인스턴스 등록
- [ ] `ipc status` - 상태 확인

### 기본 통신 (Basic Communication)
- [ ] `ipc chat --to <target> "message"` - 단방향 메시지
- [ ] `ipc ask --to <target> "prompt"` - 양방향 통신
- [ ] `ipc instances list --full` - 인스턴스 확인

### 자동화 (Automation)
- [ ] `ipc responder start <instance>` - 응답기 시작
- [ ] `ipc responder status <instance>` - 응답기 상태
- [ ] `ipc responder stop <instance>` - 응답기 종료

### 유지보수 (Maintenance)
- [ ] `ipc doctor` - 시스템 진단
- [ ] `ipc instances delete <name>` - 인스턴스 삭제
- [ ] `ipc messages clear --force` - 메시지 정리
- [ ] `ipc broker restart` - 브로커 재시작

## 🚀 빠른 참조

### 최소 설정 (3단계)
```bash
ipc broker start          # 1. 브로커 시작
ipc register myname       # 2. 등록
ipc status                # 3. 확인
```

### 기본 통신 (2단계)
```bash
ipc chat --to target "hi"            # 단방향
ipc ask --to target "hi" --timeout 5  # 양방향
```

### 자동 응답 (2단계)
```bash
ipc responder start target --policy smart --detach  # 시작
ipc responder status target                         # 확인
```

### 완전 리셋 (4단계)
```bash
ipc responder stop-all          # 1. 응답기 종료
ipc instances reset             # 2. 인스턴스 삭제
ipc messages clear --force      # 3. 메시지 삭제
ipc broker restart              # 4. 브로커 재시작
```

## 📖 관련 문서

- **설치 가이드**: `docs/INSTALL.md`
- **통합 가이드 (한글)**: `docs/IPC_UNIFIED_GUIDE_KO.md`
- **글로벌 사용법 (한글)**: `docs/GLOBAL_USAGE_KO.md`
- **CLI 명령어**: `docs/ipc_cli_commands.md`
- **레거시 리디렉션**: `docs/IPC_MANAGER_LEGACY_REDIRECT.md`
