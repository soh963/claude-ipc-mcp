# Claude IPC MCP - 빠른 시작 가이드

## 🚀 즉시 실행하기

### 방법 1: 4개 별도 창 실행 (가장 안정적) ⭐
```bash
# 4개의 별도 CMD 창으로 실행
D:\claude-ipc-mcp\start_4windows.bat
```
각각의 CMD 창에서 claude, gemini, codex, lm 인스턴스가 자동으로 실행됩니다.

### 방법 2: Windows Terminal 2x2 분할 (가로 2, 세로 2)
```bash
# Windows Terminal이 설치되어 있는 경우 (추천 순서)
D:\claude-ipc-mcp\start_simple_2x2.bat    # 가장 간단한 방법 ⭐
D:\claude-ipc-mcp\start_2x2_grid.bat      # 대체 2x2 그리드
D:\claude-ipc-mcp\start_4split_2x2.bat    # 포커스 방식
D:\claude-ipc-mcp\start_4split_fixed.bat  # 기본 분할 버전

# PowerShell 버전 (더 안정적)
powershell -ExecutionPolicy Bypass -File D:\claude-ipc-mcp\start_4split.ps1
```

각 인스턴스는 다른 색상으로 표시됩니다:
- **Claude**: 초록색 (Green)
- **Gemini**: 시안색 (Cyan)
- **Codex**: 빨간색 (Red)
- **LM**: 노란색 (Yellow)

레이아웃:
```
+----------+----------+
| claude   | gemini   |
+----------+----------+
| codex    | lm       |
+----------+----------+
```

### 방법 3: 개별 터미널 실행
```bash
# 각각의 터미널에서 개별 실행
cd D:\claude-ipc-mcp
python tools\interactive_client.py claude    # 터미널 1
python tools\interactive_client.py gemini    # 터미널 2
python tools\interactive_client.py codex     # 터미널 3
python tools\interactive_client.py lm        # 터미널 4
```

## 💬 자연어 명령어 사용법

각 터미널에서 다음과 같은 자연어 명령어를 사용할 수 있습니다:

### 1. 인스턴스 등록 (자동으로 실행됨)
```
# 이미 자동 등록되지만, 수동으로도 가능:
Register this instance as claude
```

### 2. 메시지 보내기
```
Send message to gemini: Hello from Claude!
Send message to codex: How are you?
Send message to lm: Let's collaborate!
```

### 3. 메시지 확인
```
Check messages
또는
Check
```

### 4. 온라인 인스턴스 목록
```
List instances
또는
List
또는
Who
```

### 5. 도움말
```
Help
```

### 6. 화면 지우기
```
Clear
```

### 7. 종료
```
Exit
또는
Quit
```

## 📝 등록 확인 메시지

올바른 등록 메시지는 다음과 같습니다:
```
✅ Successfully registered as 'claude'
```

만약 이미 등록되어 있다면:
```
✅ Already registered as 'claude'
```

## 🎯 사용 시나리오 예제

### 시나리오 1: Claude에서 Gemini로 메시지 보내기
1. Claude 터미널에서: `Send message to gemini: Hello Gemini!`
2. Gemini 터미널에서: `Check messages`
3. 결과: `📥 From claude: Hello Gemini!`

### 시나리오 2: 브로드캐스트 (모든 인스턴스에 메시지)
```bash
# 별도 터미널에서:
cd D:\claude-ipc-mcp
python tools\ipc_manager.py broadcast claude "Hello everyone!"
```

### 시나리오 3: 모든 메시지 기록 보기
```bash
# 별도 터미널에서:
cd D:\claude-ipc-mcp
python tools\ipc_manager.py show-all
```

## 🔧 문제 해결

### Windows Terminal이 실행되지 않을 때
- 4개의 별도 CMD 창이 자동으로 열립니다
- 또는 수동으로 4개의 터미널을 열고 개별 실행

### 인스턴스가 인식되지 않을 때
유효한 인스턴스 이름:
- `claude`
- `gemini`
- `codex`
- `lm`

다른 이름은 사용할 수 없습니다.

### 메시지가 전달되지 않을 때
1. 수신 인스턴스가 실행 중인지 확인
2. `List instances` 명령으로 온라인 인스턴스 확인
3. 정확한 인스턴스 이름 사용 확인

## 🗂️ 프로젝트 구조

```
D:\claude-ipc-mcp\
├── start_4windows.bat          # 4개 별도 창 실행기 (가장 안정적) ⭐
├── start_4split_2x2.bat        # Windows Terminal 2x2 분할 (정확한 버전) ✨
├── start_4split_fixed.bat      # Windows Terminal 2x2 분할 (업데이트)
├── start_4split.ps1            # PowerShell 2x2 분할 실행기
├── tools\
│   ├── interactive_client.py   # 자연어 명령 클라이언트
│   ├── ipc_manager.py          # IPC 관리 도구
│   └── monitor_instance.py     # 인스턴스별 모니터
└── QUICK_START.md              # 이 문서
```

## ⚠️ 주의사항

- 이 시스템은 **로컬 IPC (Inter-Process Communication)** 용입니다
- MCP (Model Context Protocol) 서버와는 별개의 시스템입니다
- 4개의 인스턴스 이름은 고정되어 있습니다 (claude, gemini, codex, lm)
