# Claude IPC MCP - 스마트 AI 통신 시스템

## 🚀 개요
Claude IPC MCP는 여러 AI 인스턴스 간의 안전한 메시지 교환을 위한 통신 시스템입니다. 무한 루프 방지 기능과 스마트 자동 응답 시스템을 통해 안정적인 AI-to-AI 통신을 제공합니다.

## ✨ 주요 기능
- **다중 인스턴스 지원**: Claude, Gemini, Codex, LM 등 여러 AI 인스턴스 동시 관리
- **무한 루프 방지**: 3중 보안 시스템으로 메시지 루프 완벽 차단
- **스마트 자동 응답**: 컨텍스트 인식 기반 지능형 응답
- **실시간 모니터링**: 메시지 송수신 실시간 추적 및 표시
- **양방향 통신**: 모든 인스턴스 간 자유로운 메시지 교환

## 📋 시스템 요구사항
- Python 3.8 이상
- SQLite3 지원
- asyncio 라이브러리

## 🛠️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/claude-ipc-mcp.git
cd claude-ipc-mcp
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 초기화
```bash
python tools/ipc_manager.py init
```

## 🎯 빠른 시작

### 1. 인스턴스 등록
```bash
# Claude 인스턴스 등록
python tools/ipc_manager.py register claude

# 다른 인스턴스들 등록
python tools/ipc_manager.py register gemini
python tools/ipc_manager.py register codex
python tools/ipc_manager.py register lm
```

### 2. 자동 응답 시스템 실행

#### 단일 인스턴스 실행
```bash
# Claude 인스턴스 자동 응답 시작
python tools/smart_auto_responder.py claude
```

#### 모든 인스턴스 동시 실행
```bash
# 4개 인스턴스 모두 자동 응답 시작
python tools/multi_instance_responder.py
```

### 3. 메시지 보내기
```bash
# Claude에서 Gemini에게 메시지 보내기
python tools/ipc_manager.py send claude gemini "안녕하세요!"

# 모든 인스턴스에게 브로드캐스트
python tools/ipc_manager.py broadcast claude "모두 안녕하세요!"
```

## 📝 관리 명령어

### 인스턴스 관리
```bash
# 인스턴스 등록
python tools/ipc_manager.py register [instance_id]

# 인스턴스 삭제
python tools/ipc_manager.py unregister [instance_id]

# 등록된 인스턴스 목록 확인
python tools/ipc_manager.py list
```

### 메시지 관리
```bash
# 메시지 보내기
python tools/ipc_manager.py send [from_id] [to_id] "[message]"

# 브로드캐스트
python tools/ipc_manager.py broadcast [from_id] "[message]"

# 메시지 확인
python tools/ipc_manager.py check [instance_id]

# 모든 메시지 보기
python tools/ipc_manager.py show-all

# 메시지 초기화 (모든 메시지 삭제)
python tools/ipc_manager.py clear
```

### 시스템 관리
```bash
# 데이터베이스 초기화
python tools/ipc_manager.py init

# 시스템 상태 확인
python tools/ipc_manager.py status

# 통계 보기
python tools/ipc_manager.py stats
```

## 🔧 고급 설정

### 자동 응답 커스터마이징
`tools/smart_auto_responder.py`의 `generate_smart_response` 메서드를 수정하여 응답 로직을 커스터마이징할 수 있습니다:

```python
async def generate_smart_response(self, msg: dict) -> Optional[str]:
    from_id = msg['from_id']
    content = msg['content'].lower()

    # 인스턴스별 맞춤 응답 추가
    if from_id == "your_instance":
        if "특정키워드" in content:
            return "맞춤 응답"

    return None
```

### 체크 간격 조정
자동 응답기의 메시지 체크 간격을 조정할 수 있습니다:

```python
# 2초마다 체크 (기본값)
responder = SmartAutoResponder(instance_id, check_interval=2.0)

# 1초마다 체크 (더 빠른 응답)
responder = SmartAutoResponder(instance_id, check_interval=1.0)
```

## 🛡️ 무한 루프 방지 시스템

### 3중 보안 메커니즘
1. **메시지 해시 중복 제거**: MD5 해시를 이용한 중복 메시지 필터링
2. **쿨다운 시스템**: 1초 간격 메시지 전송 제한
3. **유사도 검사**: 80% 이상 유사한 메시지는 핑퐁으로 판단

### 자동 응답 패턴 감지
다음 패턴이 감지되면 자동으로 응답하지 않습니다:
- "요청을 확인했습니다"
- "처리 중입니다"
- "메시지 받았습니다"
- "질문을 받았습니다"

## 📊 시스템 아키텍처

```
┌─────────────────────────────────────────────┐
│            Multi Instance Manager            │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Claude  │  │ Gemini  │  │  Codex  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘    │
│       │            │            │           │
│       └────────────┼────────────┘           │
│                    │                        │
│         ┌──────────▼──────────┐            │
│         │  Smart Auto Responder │           │
│         │  - Loop Prevention    │           │
│         │  - Pattern Detection  │           │
│         └──────────┬──────────┘            │
│                    │                        │
│         ┌──────────▼──────────┐            │
│         │   SQLite Database    │           │
│         │  ~/.claude-ipc-data  │           │
│         └─────────────────────┘            │
└─────────────────────────────────────────────┘
```

## 🐛 문제 해결

### 메시지가 전달되지 않음
1. 인스턴스가 등록되어 있는지 확인: `python tools/ipc_manager.py list`
2. 자동 응답기가 실행 중인지 확인
3. 데이터베이스 권한 확인

### 무한 루프 발생
1. 즉시 자동 응답기 중지 (Ctrl+C)
2. 메시지 초기화: `python tools/ipc_manager.py clear`
3. 자동 응답 패턴 검토 후 재시작

### 데이터베이스 오류
```bash
# 데이터베이스 재초기화
python tools/ipc_manager.py init --force
```

## 📁 프로젝트 구조
```
claude-ipc-mcp/
├── tools/
│   ├── smart_auto_responder.py     # 스마트 자동 응답 시스템
│   ├── multi_instance_responder.py # 다중 인스턴스 관리자
│   ├── ipc_manager.py              # IPC 관리 유틸리티
│   ├── test_bidirectional.py      # 양방향 통신 테스트
│   └── realtime_notifier.py       # 실시간 알림 (레거시)
├── docs/
│   └── README_KR.md                # 한국어 문서
├── README.md                       # 영문 프로젝트 문서
├── requirements.txt                # 파이썬 의존성
└── .gitignore                     # Git 무시 파일
```

## 📜 라이선스
MIT License

## 🤝 기여하기
Pull Request는 언제나 환영합니다!

## 📧 문의
문제가 있거나 질문이 있으시면 이슈를 등록해주세요.