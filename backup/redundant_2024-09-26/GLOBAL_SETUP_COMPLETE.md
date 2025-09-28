# 🌐 Claude IPC MCP Global Setup Complete

## ✅ 설치 완료 항목 (Installation Complete)

### 1. **Windows 자동 시작 설정**
- `auto_start_ipc.bat` - Windows 시작 시 자동 실행 스크립트
- `install_startup.bat` - 시작 폴더에 설치하는 스크립트
- 실행: `install_startup.bat` (관리자 권한 필요 없음)

### 2. **글로벌 환경 변수 설정**
- `setup_environment.ps1` - 환경 변수 설정 (사용자 수준)
- `scripts/install-global.ps1` - 시스템 전체 설정 (관리자 필요)

**설치 방법:**
```powershell
# 관리자 PowerShell에서 실행
powershell -ExecutionPolicy Bypass -File D:\claude-ipc-mcp\scripts\install-global.ps1
```

### 3. **자연어 명령어 지원**

어느 디렉토리, 어느 프로젝트에서든 사용 가능:

#### 한국어 명령어
- `모니터링` - 4개 패널 모니터링 시작
- `메시지` - 메시지 보내기
- `확인` - 상태 확인

#### English Commands
- `monitoring` - Start 4-panel monitoring
- `ipc-monitor` - Direct monitoring command
- `ipc-send` - Send messages
- `ipc-check` - Check messages

### 4. **인스턴스 가이드 문서**

각 인스턴스가 처음 읽는 문서:
- **CLAUDE.md** - Claude 마스터 코디네이터 가이드
- **CODEX.md** - Codex 코드 전문가 가이드
- **GEMINI_SETUP.md** - Gemini 멀티모달 어시스턴트 가이드
- **ERROR_RESOLUTION.md** - 500 에러 해결 가이드

### 5. **MCP 설정 파일**
- `.mcp.json` - MCP 서버 구성 완료
- 모든 인스턴스 통신 설정 포함

## 🚀 빠른 시작 가이드

### Step 1: 환경 변수 설정 (한 번만)
```powershell
# 관리자 권한 PowerShell 실행
powershell -ExecutionPolicy Bypass -File D:\claude-ipc-mcp\scripts\install-global.ps1
```

### Step 2: Windows 자동 시작 등록
```batch
# 일반 CMD에서 실행
D:\claude-ipc-mcp\install_startup.bat
```

### Step 3: 테스트
```batch
# 아무 디렉토리에서나 실행
모니터링
```

## 📊 사용 가능한 글로벌 명령어

### 터미널에서 (어디서나)
```bash
# 모니터링 시작
모니터링
monitoring
ipc-monitor

# 메시지 보내기
ipc send claude gemini "안녕하세요"

# 메시지 확인
ipc check claude

# 인스턴스 리스트
ipc list
```

### Python에서 (어디서나)
```python
import os
import sys

# IPC 시스템 경로 추가
sys.path.append(os.environ['CLAUDE_IPC_HOME'])

from tools.ipc_manager import IPCManager
ipc = IPCManager()

# 사용
ipc.send("claude", "gemini", "Hello from anywhere!")
```

## 🔧 환경 변수 확인

CMD 또는 PowerShell에서:
```batch
echo %CLAUDE_IPC_HOME%
echo %CLAUDE_IPC_DB%
echo %IPC_MONITOR%
echo %IPC_INSTANCES%
```

## 🆘 문제 해결

### 모니터링이 안 될 때
1. 환경 변수 확인: `echo %CLAUDE_IPC_HOME%`
2. Python 확인: `python --version`
3. 수동 실행: `python D:\claude-ipc-mcp\tools\fixed_monitor.py claude`

### 500 Error 발생 시
```bash
# 자동 복구 실행
python D:\claude-ipc-mcp\tools\auto_recovery.py
```

### 메시지가 전달되지 않을 때
```bash
# 데이터베이스 초기화
python D:\claude-ipc-mcp\tools\ipc_manager.py init

# 인스턴스 재등록
python D:\claude-ipc-mcp\tools\ipc_manager.py register claude
```

## 📌 중요 경로

- **IPC 홈**: `D:\claude-ipc-mcp`
- **데이터베이스**: `%USERPROFILE%\.claude-ipc-data\messages.db`
- **스크립트**: `D:\claude-ipc-mcp\scripts`
- **도구**: `D:\claude-ipc-mcp\tools`

## 🎯 현재 상태

✅ **완료된 작업:**
1. Windows 자동 시작 스크립트 생성
2. 글로벌 환경 변수 설정 스크립트 생성
3. 자연어 명령어 지원 구현
4. MCP 설정 파일 구성
5. 인스턴스별 가이드 문서 작성
6. 에러 복구 시스템 구축

⏳ **필요한 작업:**
1. PowerShell 스크립트를 **관리자 권한**으로 실행
2. 컴퓨터 재시작 또는 로그아웃/로그인
3. 각 인스턴스에서 가이드 문서 읽기

## 🌟 특별 기능

### 1. 자연어 이해
- "모니터링 시작해줘" → 자동으로 모니터링 실행
- "메시지 보내" → IPC 메시지 전송
- "상태 확인" → 시스템 상태 체크

### 2. 어디서나 접근
- 모든 프로젝트에서 IPC 사용 가능
- 환경 변수로 글로벌 접근
- PATH에 명령어 추가

### 3. 자동 복구
- 500 에러 자동 감지 및 복구
- 프로세스 정리 및 재시작
- 캐시 삭제 및 초기화

## 📝 다음 단계

1. **관리자 PowerShell 실행**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File D:\claude-ipc-mcp\scripts\install-global.ps1
   ```

2. **Windows 자동 시작 등록**:
   ```batch
   D:\claude-ipc-mcp\install_startup.bat
   ```

3. **테스트**:
   ```batch
   모니터링
   ```

모든 설정이 완료되면 어느 프로젝트, 어느 세션에서든 Claude IPC MCP를 사용할 수 있습니다!

---

**Created**: 2025-09-25
**Version**: 2.0 - Global Environment Setup
**Author**: Claude IPC MCP Team