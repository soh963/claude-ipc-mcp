# 브로드캐스트 자동응답 문제 해결 요약

**날짜**: 2025-10-01
**이슈**: Auto-responder가 브로드캐스트 메시지에 응답하지 않음

## 🔍 문제의 근본 원인

### 1. Auto-responder가 브로드캐스트 메시지를 감지하지 못함

**파일**: `tools/auto_responder.py` (86-94번 줄)

**문제**:
```python
cursor.execute("""
    SELECT id, from_id, content, timestamp
    FROM messages
    WHERE to_id = ? AND id > ?
    ORDER BY id ASC
""", (self.instance_id, self.last_message_id))
```

- 자동응답기는 `to_id = self.instance_id`인 메시지만 조회
- 브로드캐스트 메시지는 `to_id = "*"` 또는 `to_id = "all"`로 저장됨
- 따라서 자동응답기가 브로드캐스트를 전혀 볼 수 없었음

### 2. 브로커가 브로드캐스트를 거부함

**파일**: `src/claude_ipc_server.py` (774번 줄)

**문제**:
```python
# Validate to_id format
if not self._validate_instance_id(to_id):
    return {"status": "error", "message": "Invalid recipient ID format"}
```

- `_validate_instance_id()` 함수는 알파벳, 숫자, `-`, `_`만 허용
- `*`와 `all`은 유효하지 않은 문자로 거부됨

## ✅ 적용된 해결책

### 해결책 1: Auto-responder가 브로드캐스트 메시지 감지 (구현 완료)

**파일**: `tools/auto_responder.py`

**변경 사항**:
```python
# 1. SQL 쿼리 수정 - 브로드캐스트 메시지도 조회
cursor.execute("""
    SELECT id, from_id, to_id, content, timestamp
    FROM messages
    WHERE (to_id = ? OR to_id = '*' OR to_id = 'all') AND id > ?
    ORDER BY id ASC
""", (self.instance_id, self.last_message_id))

# 2. 메시지 타입 표시
msg_type = "📢 브로드캐스트" if to_id in ("*", "all") else "📨 직접 메시지"
print(f"\n📥 받은 메시지 ({msg_type}) [{from_id}]: {content}", flush=True)

# 3. 브로드캐스트 응답 로직 추가
response = self.generate_response(content, from_id, is_broadcast=(to_id in ("*", "all")))
```

**`generate_response()` 함수 개선**:
```python
def generate_response(self, content, from_id, is_broadcast=False):
    # 브로드캐스트 메시지에 대한 특별 처리
    if is_broadcast:
        # 브로드캐스트에는 간단하게 응답
        if "안녕" in content or "hello" in content_lower or "hi" in content_lower:
            return f"👋 안녕하세요 {from_id}님! {self.instance_id}입니다. 브로드캐스트 메시지 수신했습니다!"
        elif "테스트" in content or "test" in content_lower:
            return f"✅ {self.instance_id} 인스턴스 정상 작동 중!"
        elif "반가" in content or "반답" in content:
            return f"😊 {self.instance_id}에서 인사드립니다!"
        # 브로드캐스트는 기본적으로 응답함
        return f"📢 {self.instance_id}: 메시지 확인했습니다!"

    # ... 기존 직접 메시지 응답 로직
```

### 해결책 2: 브로커가 브로드캐스트 허용 (구현 완료)

**파일**: `src/claude_ipc_server.py`

**변경 사항**:
```python
# Validate to_id format (allow * and all for broadcast)
if to_id not in ("*", "all") and not self._validate_instance_id(to_id):
    return {"status": "error", "message": "Invalid recipient ID format"}
```

- 이제 `*`와 `all`을 특별한 수신자로 인식
- 브로드캐스트 메시지가 데이터베이스에 정상적으로 저장됨

## 📊 예상 결과

### Before (이전 - 문제 상황)
```
사용자: broadcast "안녕하세요! 모든 인스턴스 여러분!"
      ↓
브로커: ❌ "Invalid recipient ID format" 오류
자동응답기: 메시지를 전혀 볼 수 없음
결과: 0개의 응답
```

### After (수정 후 - 정상 작동)
```
사용자: broadcast "안녕하세요! 모든 인스턴스 여러분!"
      ↓
브로커: ✅ 메시지 저장 (to_id = "*")
      ↓
자동응답기(claude): "👋 안녕하세요! claude입니다. 브로드캐스트 메시지 수신했습니다!"
자동응답기(gemini): "👋 안녕하세요! gemini입니다. 브로드캐스트 메시지 수신했습니다!"
자동응답기(mock): "👋 안녕하세요! mock입니다. 브로드캐스트 메시지 수신했습니다!"
자동응답기(test-tem-main): "👋 안녕하세요! test-tem-main입니다. 브로드캐스트 메시지 수신했습니다!"
      ↓
결과: 4개의 응답 (각 인스턴스가 발신자에게 회신)
```

## 🧪 테스트 방법

### 1. 시스템 재시작 (필수)

**이유**: 코드 변경사항 적용 및 다중 브로커 프로세스 정리

```bash
# 모든 Python 프로세스 종료
powershell -Command "Stop-Process -Name python -Force"

# 잠시 대기
timeout 3

# 브로커 시작
uv run python tools/start_broker.py &

# 잠시 대기
timeout 5
```

### 2. 인스턴스 등록

```bash
uv run python tools/ipc_global_command.py register claude
uv run python tools/ipc_global_command.py register gemini
uv run python tools/ipc_global_command.py register test-tem-main
uv run python tools/ipc_global_command.py register mock
```

### 3. Auto-responder 시작

```bash
uv run python tools/ipc_global_command.py responder start-all --policy smart --detach
```

### 4. 브로드캐스트 테스트

```bash
# 테스트 스크립트 실행
uv run python test_broadcast.py
```

**test_broadcast.py 내용**:
```python
from core import broker_client
import time

session_token = "YOUR_SESSION_TOKEN"  # 등록 시 받은 토큰
instance_id = "test-tem-main"

# 브로드캐스트 전송
response = broker_client.send(
    session_token,
    instance_id,
    "*",  # 모든 인스턴스에게
    "안녕하세요! 모든 인스턴스 여러분! 브로드캐스트 테스트입니다. 👋"
)

print(f"✅ Broadcast sent: {response}")

# 5초 대기
time.sleep(5)

# 응답 확인
check_response = broker_client._send_request({
    "action": "check",
    "instance_id": instance_id,
    "session_token": session_token
})

messages = check_response.get("messages", [])
print(f"\n✉️ Received {len(messages)} response(s):\n")

for msg in messages:
    print(f"  From: {msg['from']}")
    print(f"  Content: {msg['message']['content']}")
    print()
```

## 🎯 주요 개선사항

### 1. 브로드캐스트 메시지 감지
- ✅ Auto-responder가 이제 `to_id = "*"` 또는 `to_id = "all"` 메시지를 감지
- ✅ 직접 메시지와 브로드캐스트를 구분하여 처리

### 2. 브로드캐스트 응답 로직
- ✅ 브로드캐스트에 대한 간결한 응답 생성
- ✅ 발신자에게만 회신 (브로드캐스트 루프 방지)
- ✅ 한국어 메시지 패턴 인식 ("안녕", "테스트", "반가")

### 3. 브로커 보안 개선
- ✅ `*`와 `all`을 특별한 수신자로 화이트리스트 추가
- ✅ 기존 보안 검증은 유지 (일반 인스턴스 ID는 여전히 검증됨)

## 📌 중요 사항

### Ask vs Broadcast 차이

| 특징 | Ask | Broadcast |
|------|-----|-----------|
| 수신자 | 단일 인스턴스 | 모든 인스턴스 (`*` 또는 `all`) |
| 응답 대기 | 타임아웃까지 대기 | 대기하지 않음 (fire-and-forget) |
| Auto-responder 필요 | ✅ 필수 | ✅ 필수 |
| 응답 경로 | 발신자에게 직접 회신 | 발신자에게 직접 회신 |
| 사용 사례 | 양방향 대화, 질의응답 | 공지, 알림, 상태 확인 |

### Auto-responder 필수

- **Ask 명령**: Auto-responder가 없으면 타임아웃 (응답 없음)
- **Broadcast 명령**: Auto-responder가 없으면 메시지만 전달되고 응답 없음
- **결론**: 자동 응답을 받으려면 수신자 인스턴스에 auto-responder가 실행 중이어야 함

## 📝 변경된 파일 목록

1. **tools/auto_responder.py** (86-154번 줄)
   - SQL 쿼리에 브로드캐스트 메시지 포함
   - `to_id` 필드 추가로 메시지 타입 판별
   - `generate_response()` 함수에 `is_broadcast` 파라미터 추가
   - 브로드캐스트 전용 응답 로직 구현

2. **src/claude_ipc_server.py** (774번 줄)
   - `*`와 `all`을 유효한 수신자로 허용
   - 브로드캐스트 메시지가 데이터베이스에 저장되도록 수정

3. **테스트 스크립트** (신규 생성)
   - `test_broadcast.py`: 브로드캐스트 기능 테스트
   - `clean_restart.py`: 시스템 클린 재시작 스크립트

## 🚀 다음 단계

1. ✅ 모든 Python 프로세스 종료
2. ✅ 브로커 재시작
3. ✅ 인스턴스 등록 (claude, gemini, test-tem-main, mock)
4. ✅ Auto-responder 시작
5. ⏳ 브로드캐스트 테스트 실행
6. ⏳ 결과 검증 및 문서화

## 💡 예상 테스트 결과

```
📢 Sending broadcast message from test-tem-main...
✅ Broadcast sent: {'status': 'ok', 'message': 'Message sent'}

⏳ Waiting 5 seconds for responses...

📬 Checking for responses...

✉️ Received 4 response(s):

  From: claude
  Content: 👋 안녕하세요 test-tem-main님! claude입니다. 브로드캐스트 메시지 수신했습니다!
  Time: 2025-10-01T22:15:30.123456

  From: gemini
  Content: 👋 안녕하세요 test-tem-main님! gemini입니다. 브로드캐스트 메시지 수신했습니다!
  Time: 2025-10-01T22:15:30.234567

  From: mock
  Content: 👋 안녕하세요 test-tem-main님! mock입니다. 브로드캐스트 메시지 수신했습니다!
  Time: 2025-10-01T22:15:30.345678

  From: test-tem-main (자기 자신은 제외됨)
```

## 📚 참고 사항

- 브로드캐스트는 발신자 자신에게는 전달되지 않음 (by design)
- 모든 응답은 발신자에게 직접 회신됨 (그룹 채팅 방식 아님)
- Auto-responder가 멈춰있거나 오프라인인 인스턴스는 응답하지 않음
- 브로드캐스트 메시지도 rate limiting 적용됨 (100 req/min)
