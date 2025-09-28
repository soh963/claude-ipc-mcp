# 🚀 IPC System Quick Start Guide

## 원클릭 실행 방법

### Windows 사용자

#### 방법 1: 배치 파일 (가장 간단)
```
더블클릭 → START_IPC.bat
```

#### 방법 2: PowerShell
```powershell
우클릭 → "PowerShell에서 실행" → Start-IPCSystem.ps1
```

#### 방법 3: Python 직접 실행
```bash
python start_all_ipc.py
```

### 실행 순서 (자동)

1. 🧹 기존 프로세스 정리
2. 🖥️ IPC 서버 확인/시작
3. 📝 모든 AI 인스턴스 등록
4. 🧪 통신 테스트
5. 📈 데이터베이스 통계 표시
6. 👥 활성 인스턴스 목록
7. 🤖 Auto-responder 시작
8. 📊 모니터링 시작

## 시스템 확인 방법

### 전체 테스트
```bash
python test_ipc_communication.py
```

### 개별 명령어
```bash
# 메시지 전송
python tools/ipc_send.py gemini "안녕하세요!"

# 메시지 확인
python tools/ipc_check.py gemini

# 활성 인스턴스 목록
python tools/ipc_list.py
```

## 시스템 관리

### 전체 종료
- `Ctrl + C` 또는 창 닫기
- 또는: `taskkill /F /IM python.exe`

### 메시지 초기화
```bash
python tools/clear_project_messages.py
```

### 프로세스 리셋
```bash
python tools/reset_all_ipc.py
```

## 파일 구조

```
📁 claude-ipc-mcp/
├── 🚀 START_IPC.bat          # Windows 원클릭 실행
├── 🐍 start_all_ipc.py       # 통합 실행 스크립트
├── 🧪 test_ipc_communication.py  # 통신 테스트
├── 📊 start_split_monitoring.py  # 모니터링
└── 🛠️ tools/
    ├── ipc_register.py       # 인스턴스 등록
    ├── ipc_send.py          # 메시지 전송
    ├── ipc_check.py         # 메시지 확인
    └── ipc_list.py          # 인스턴스 목록
```

## 작동 확인 체크리스트

✅ **정상 작동 시:**
- "✅ IPC server already running" 또는 "✅ IPC server started"
- 모든 인스턴스 "✅ Registered"
- 통신 테스트 "✅ claude → gemini" 등
- "💚 System is running" 메시지

❌ **문제 발생 시:**
1. Python 설치 확인: `python --version`
2. 프로세스 정리: `taskkill /F /IM python.exe`
3. 다시 실행: `START_IPC.bat`

## 핵심 기능

- **프로젝트 격리**: 같은 프로젝트의 AI CLI만 통신 가능
- **자동 응답**: Auto-responder가 메시지 자동 처리
- **모니터링**: 실시간 메시지 모니터링
- **통신 테스트**: 모든 인스턴스 간 통신 자동 검증

## 문의 & 문제 해결

문제 발생 시:
1. `SOLUTION_COMPLETE.md` 참조
2. `PROJECT_CONSTITUTION.md`의 규칙 확인
3. `test_ipc_communication.py` 실행하여 상태 확인

---

**한 번의 클릭으로 모든 것이 준비됩니다!** 🎉