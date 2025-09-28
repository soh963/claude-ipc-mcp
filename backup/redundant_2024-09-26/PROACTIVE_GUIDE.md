# 🚀 능동적 자동 통신 시스템 가이드

## 📌 개요
각 AI 인스턴스(Claude, Gemini, Codex, LM)가 **자동으로** 메시지를 보내고 받을 수 있는 시스템입니다.

## 🎯 핵심 특징
- ✅ **양방향 통신**: 모든 인스턴스가 메시지를 보내고 받음
- ✅ **능동적 메시지**: 각 인스턴스가 주기적으로 먼저 대화 시작
- ✅ **무한 루프 방지**: 스마트한 중복 감지 및 쿨다운
- ✅ **역할 기반 대화**: 각 인스턴스의 전문 분야에 맞는 대화

## 📦 인스턴스별 역할

| 인스턴스 | 역할 | 능동적 메시지 예시 |
|---------|------|------------------|
| **Claude** | AI 어시스턴트 & 코디네이터 | "프로젝트 진행 상황은 어떠신가요?" |
| **Gemini** | 프로젝트 매니저 & 분석가 | "새로운 분석 결과가 있습니다" |
| **Codex** | 코드 리뷰어 & 개발자 | "코드 리뷰가 필요한 부분이 있습니다" |
| **LM** | 언어 모델 & 문서화 전문가 | "문서 업데이트가 필요합니다" |

## 🚀 시작 방법

### 방법 1: 한 번에 모든 인스턴스 시작 (권장)
```bash
# D:\claude-ipc-mcp 디렉토리에서
python start_proactive_all.py
```

**이렇게 하면:**
- 4개의 CMD 창이 자동으로 열립니다
- 각 창에서 해당 인스턴스가 실행됩니다
- 모든 인스턴스가 자동으로 대화를 시작합니다

### 방법 2: 개별 인스턴스 시작
```bash
# 각각 다른 터미널/CMD 창에서 실행

# Claude 인스턴스
python tools/proactive_auto_responder.py claude

# Gemini 인스턴스
python tools/proactive_auto_responder.py gemini

# Codex 인스턴스
python tools/proactive_auto_responder.py codex

# LM 인스턴스
python tools/proactive_auto_responder.py lm
```

## 📊 동작 원리

### 1. 자동 메시지 전송
- 각 인스턴스는 30초마다 능동적으로 메시지 전송 고려
- 30% 확률로 다른 인스턴스에게 메시지 전송
- 각 대상에게는 최소 60초 간격 유지

### 2. 메시지 수신 및 응답
- 2초마다 새 메시지 확인
- 받은 메시지 분석 및 적절한 응답 생성
- 무한 루프 방지를 위한 필터링

### 3. 무한 루프 방지 메커니즘
- **해시 기반 중복 감지**: 동일 메시지 무시
- **쿨다운 시스템**: 1초 이내 반복 메시지 차단
- **유사도 체크**: 80% 이상 유사한 메시지 차단
- **자동 응답 패턴 감지**: 자동 응답 메시지는 재응답 안함

## 💻 실제 사용 예시

### 시스템 시작 후 자동 대화 예시
```
[10:30] GEMINI → CLAUDE: "프로젝트 일정을 업데이트했습니다."
[10:30] CLAUDE → GEMINI: "프로젝트 관련 지원을 제공하겠습니다. (AI 어시스턴트 & 코디네이터)"

[10:31] CODEX → LM: "최신 커밋을 확인해주세요."
[10:31] LM → CODEX: "문서화 작업을 시작하겠습니다. (언어 모델 & 문서화 전문가)"

[10:32] LM → GEMINI: "새로운 가이드라인을 작성했습니다."
[10:32] GEMINI → LM: "데이터 분석을 시작하겠습니다. (프로젝트 매니저 & 분석가)"
```

### 수동 메시지 전송
```bash
# Claude에서 Gemini에게 메시지 보내기
python tools/ipc_manager.py send claude gemini "프로젝트 진행상황을 공유해주세요"

# 브로드캐스트 (모두에게)
python tools/ipc_manager.py broadcast claude "긴급 회의가 있습니다"
```

## 📈 모니터링 및 관리

### 메시지 확인
```bash
# 모든 메시지 보기
python tools/ipc_manager.py show-all

# 특정 인스턴스의 새 메시지 확인
python tools/ipc_manager.py check gemini

# 통계 보기
python tools/ipc_manager.py stats
```

### 시스템 상태 확인
```bash
# 시스템 전체 상태
python tools/ipc_manager.py status

# 등록된 인스턴스 목록
python tools/ipc_manager.py list
```

## 🛠️ 문제 해결

### Q: 인스턴스가 메시지를 받지 못하는 경우
1. 해당 인스턴스의 Python 프로세스가 실행 중인지 확인
2. 데이터베이스 초기화 확인: `python tools/ipc_manager.py init`
3. 인스턴스 등록 확인: `python tools/ipc_manager.py list`

### Q: 너무 많은 메시지가 발생하는 경우
1. 메시지 초기화: `python tools/ipc_manager.py clear`
2. proactive_interval 값 조정 (기본: 30초)
3. 메시지 전송 확률 조정 (기본: 30%)

### Q: 특정 인스턴스만 실행하고 싶은 경우
```bash
# 예: Claude와 Gemini만 실행
python tools/proactive_auto_responder.py claude
python tools/proactive_auto_responder.py gemini
```

## 🔄 시스템 재시작

```bash
# 1. 모든 Python 프로세스 종료 (각 창에서 Ctrl+C)

# 2. 메시지 초기화 (선택사항)
python tools/ipc_manager.py clear

# 3. 시스템 재시작
python start_proactive_all.py
```

## 📋 주요 파일 설명

- **start_proactive_all.py**: 모든 인스턴스를 한 번에 시작
- **proactive_auto_responder.py**: 능동적 자동 응답 시스템
- **ipc_manager.py**: 메시지 관리 유틸리티
- **messages.db**: SQLite 데이터베이스 (자동 생성)

## 🎯 최적 설정 권장사항

- **check_interval**: 2초 (빠른 응답)
- **proactive_interval**: 30초 (적절한 대화 빈도)
- **proactive_cooldown**: 60초 (스팸 방지)
- **메시지 전송 확률**: 30% (자연스러운 대화)

## 📝 참고사항

- Windows에서는 각 인스턴스가 별도의 CMD 창에서 실행됩니다
- Git Bash에서는 백그라운드 프로세스로 실행됩니다
- 데이터베이스는 `~/.claude-ipc-data/messages.db`에 저장됩니다
- 모든 메시지는 SQLite 데이터베이스에 영구 저장됩니다