# Claude Code IPC Slash Commands - 완전 가이드

## 📋 개요

Claude Code CLI에서 `:` (콜론) 구분자를 사용하여 IPC 명령어를 실행할 수 있습니다.

**명령어 형식**: `/ipc:command`

예: `/ipc:setup`, `/ipc:status`, `/ipc:send`

## 🚀 빠른 시작

### 1. 최초 설정 (원클릭)

```
/ipc:setup <instance-name>
```

예시:
```
/ipc:setup claude-main
```

이 명령어는 다음을 자동으로 수행합니다:
- ✅ .ipc 디렉토리 초기화
- 📝 인스턴스 등록
- 🤖 자동 응답기 시작
- 🔗 연결 확인

### 2. 상태 확인

```
/ipc:status
```

브로커 연결 상태, 활성 인스턴스 수, 세션 정보를 표시합니다.

### 3. 메시지 전송

```
/ipc:send <from> <to> <message>
```

예시:
```
/ipc:send claude gemini "API 설계를 도와줄 수 있나요?"
```

### 4. 메시지 확인

```
/ipc:check <instance-name>
```

예시:
```
/ipc:check claude-main
```

## 📚 전체 명령어 목록 (27개)

### 🔧 설정 및 관리
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/ipc:setup` | ⚡ 완전한 설정 마법사 | `/ipc:setup myname` |
| `/ipc:init` | 📁 .ipc 디렉토리 초기화 | `/ipc:init` |
| `/ipc:register` | 📝 인스턴스 등록 | `/ipc:register myname` |
| `/ipc:validate` | ✅ 설정 검증 | `/ipc:validate` |

### 📊 상태 및 진단
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/ipc:status` | 📊 연결 상태 확인 | `/ipc:status` |
| `/ipc:ping` | 🏓 연결 테스트 | `/ipc:ping` |
| `/ipc:doctor` | 🔍 문제 진단 및 자동 수정 | `/ipc:doctor` |
| `/ipc:fix` | 🔧 설정 자동 수정 | `/ipc:fix` |

### 💬 메시징
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/ipc:send` | 📤 메시지 전송 | `/ipc:send alice bob "Hi"` |
| `/ipc:check` | 📬 받은 편지함 확인 | `/ipc:check alice` |
| `/ipc:ask` | 💬 응답 대기 메시지 | `/ipc:ask alice bob "Q?" 30` |
| `/ipc:broadcast` | 📢 전체 브로드캐스트 | `/ipc:broadcast "Update"` |

### 👥 인스턴스 관리
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/ipc:list` | 📋 인스턴스 목록 | `/ipc:list` |
| `/ipc:rename` | ✏️ 이름 변경 | `/ipc:rename old new` |
| `/ipc:instances-delete` | 🗑️ 인스턴스 삭제 | `/ipc:instances-delete id` |
| `/ipc:instances-reset` | 🔄 전체 초기화 | `/ipc:instances-reset` |

### 🤖 자동 응답기
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/ipc:responder-start` | ▶️ 응답기 시작 | `/ipc:responder-start alice smart` |
| `/ipc:responder-status` | ℹ️ 응답기 상태 | `/ipc:responder-status alice` |
| `/ipc:responder-stop` | ⏹️ 응답기 중지 | `/ipc:responder-stop alice` |
| `/ipc:responder-start-all` | ▶️ 모두 시작 | `/ipc:responder-start-all` |
| `/ipc:responder-stop-all` | ⏹️ 모두 중지 | `/ipc:responder-stop-all` |

### 🔌 브로커 관리
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/ipc:broker-start` | 🚀 브로커 시작 | `/ipc:broker-start` |
| `/ipc:broker-status` | 📊 브로커 상태 | `/ipc:broker-status` |
| `/ipc:broker-stop` | 🛑 브로커 중지 | `/ipc:broker-stop` |

### 🗂️ 세션 및 메시지
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/ipc:session` | 📋 세션 정보 | `/ipc:session` |
| `/ipc:session-clear` | 🧹 세션 초기화 | `/ipc:session-clear` |
| `/ipc:messages-clear` | 🗑️ 메시지 삭제 | `/ipc:messages-clear --force` |

## 🔄 Claude Code 재시작 후 문제 해결

### 문제: 브로커/인스턴스 인식 안 됨

Claude Code를 재시작한 후 IPC 연결이 끊어진 경우:

#### 1단계: 상태 확인
```
/ipc:status
```

출력 예시:
```json
{
  "broker": {
    "running": false,
    "version": "2.0.0"
  },
  "connections": 0
}
```

#### 2단계: 브로커 시작 (필요시)
```
/ipc:broker-start
```

#### 3단계: 인스턴스 재등록
```
/ipc:register <your-instance-name>
```

또는 완전한 재설정:
```
/ipc:setup <your-instance-name>
```

#### 4단계: 연결 확인
```
/ipc:ping
```

### 자동 진단 및 수정

가장 빠른 방법:
```
/ipc:doctor
```

이 명령어는 자동으로:
- ✅ 브로커 연결 확인
- 🔍 세션 토큰 검증
- 💾 데이터베이스 무결성 검사
- 🔧 문제 자동 수정

## 💡 사용 시나리오

### 시나리오 1: AI 간 협업

```bash
# Claude 인스턴스 1 (Frontend)
/ipc:setup claude-frontend
/ipc:send claude-frontend gemini "UI 컴포넌트 디자인 피드백 부탁합니다"

# Gemini 인스턴스
/ipc:check gemini
/ipc:send gemini claude-frontend "좋습니다. shadcn/ui 사용을 제안합니다"

# Claude 인스턴스 1
/ipc:check claude-frontend
```

### 시나리오 2: 자동 응답 시스템

```bash
# 자동 응답기 설정
/ipc:setup gemini-assistant
/ipc:responder-start gemini-assistant smart

# 다른 인스턴스에서 메시지 전송
/ipc:send claude gemini-assistant "현재 시간 알려줘"

# 자동 응답 확인
/ipc:check claude
```

### 시나리오 3: 멀티 프로젝트 메시징

```bash
# 프로젝트 A
cd /path/to/project-a
/ipc:setup backend-api

# 프로젝트 B
cd /path/to/project-b
/ipc:setup frontend-app

# 프로젝트 간 통신
/ipc:send frontend-app backend-api "API 스펙 공유 부탁"
```

## 🛠️ 문제 해결 체크리스트

### ✅ 연결 문제
- [ ] `/ipc:broker-status` - 브로커 실행 중인가?
- [ ] `/ipc:status` - 연결 상태 확인
- [ ] `/ipc:ping` - 네트워크 지연 확인
- [ ] `/ipc:doctor` - 자동 진단 실행

### ✅ 메시지 문제
- [ ] `/ipc:list` - 대상 인스턴스 등록되었나?
- [ ] `/ipc:check <instance>` - 메시지 도착했나?
- [ ] `/ipc:responder-status <instance>` - 자동 응답기 작동 중인가?

### ✅ 세션 문제
- [ ] `/ipc:session` - 세션 정보 확인
- [ ] `/ipc:register <name>` - 재등록 시도
- [ ] `/ipc:session-clear` - 세션 초기화 후 재등록

## 📖 관련 문서

- **설치 가이드**: `docs/platform-guides/CLAUDE_CODE_SETUP.md`
- **통합 가이드**: `docs/IPC_UNIFIED_GUIDE_KO.md`
- **명령어 참조**: `docs/ipc_cli_commands.md`
- **문제 해결**: `docs/TROUBLESHOOTING.md`

## 🔗 추가 리소스

### 환경 변수
```bash
IPC_HOST=127.0.0.1              # 브로커 호스트
IPC_GLOBAL_PORT=9876            # 브로커 포트
IPC_SHARED_SECRET=secret        # 인증 토큰 (선택)
```

### 디렉토리 구조
```
.ipc/
├── config/         # 프로젝트 설정
├── logs/           # 브로커 및 응답기 로그
├── state/
│   ├── session.json      # 세션 토큰
│   ├── broker.pid        # 브로커 PID
│   └── messages.db       # 로컬 메시지 DB
└── secret/         # 민감 데이터
```

### 전역 데이터
```
~/.claude-ipc-data/
├── messages.db           # 전역 메시지 DB
├── large-messages/       # 큰 메시지 파일 (>10KB)
└── responders/
    ├── <instance>.pid
    └── <instance>.json
```

## 🎯 베스트 프랙티스

1. **항상 setup으로 시작**: `/ipc:setup <name>` - 모든 것을 한 번에 설정
2. **정기적으로 상태 확인**: `/ipc:status` - 연결 상태 모니터링
3. **자동 응답기 활용**: 백그라운드 메시지 처리 자동화
4. **재시작 후 doctor 실행**: `/ipc:doctor` - 자동 문제 해결
5. **명확한 인스턴스 이름**: 프로젝트-역할 형식 사용 (예: `backend-api`, `frontend-dev`)

## 🆕 변경 사항 (v2.0)

### 명령어 형식 변경
- **이전**: `/ipc-setup`, `/ipc-status`
- **현재**: `/ipc:setup`, `/ipc:status`
- **이유**: 계층적 명령어 구조, 더 나은 가독성

### 주요 개선사항
- ✅ 모든 명령어에 이모지 아이콘 추가
- 📝 상세한 설명 및 사용 예시
- 🔄 재시작 후 자동 재연결 가이드
- 🔍 향상된 문제 해결 안내

## 📞 지원

문제가 발생하면:
1. `/ipc:doctor` - 자동 진단 실행
2. `docs/TROUBLESHOOTING.md` - 문제 해결 가이드 참조
3. GitHub Issues - https://github.com/anthropics/claude-ipc-mcp/issues

---

**버전**: 2.0.0
**최종 업데이트**: 2025-10-03
**문서 유형**: Claude Code Slash Commands 완전 가이드
