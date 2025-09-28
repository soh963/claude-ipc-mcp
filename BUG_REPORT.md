# IPC System Bug Report

## 발견된 문제들

### 1. 상태 표시 문제 (Status Display Issue)

#### 현상
- 인스턴스 등록 직후 `IDLE` 대신 `REGISTERED`로 표시됨
- 시간이 지나면 `IDLE`이 아닌 `REGISTERED`로 계속 남아있음

#### 원인
`enhanced_monitor.py`의 시간 비교 로직 오류:
```python
# Line 106-114
last_time = datetime.fromisoformat(last.replace('T', ' ').replace('Z', ''))
time_diff = datetime.now() - last_time

if time_diff < timedelta(minutes=1):
    self.instance_status[instance] = "active"
elif time_diff < timedelta(minutes=5):
    self.instance_status[instance] = "idle"
else:
    self.instance_status[instance] = "registered"  # 5분 이후로는 계속 registered
```

#### 문제점
- `created_at` (세션 생성 시간)을 사용해서 상태를 판단
- 실제 활동 시간이 아닌 등록 시간 기준으로 판단
- 5분이 지나면 영원히 `REGISTERED` 상태로 남음

#### 상태 의미 설명
- **ACTIVE** (녹색): 최근 1분 이내 등록된 인스턴스
- **IDLE** (노란색): 1-5분 사이에 등록된 인스턴스
- **REGISTERED** (회색): 5분 이상 전에 등록된 인스턴스
- **OFFLINE** (빨간색): 등록되지 않았거나 세션이 만료된 인스턴스

### 2. Codex 인스턴스 등록 문제

#### 현상
- codex에서 Python을 찾을 수 없다는 오류 발생
- `python: command not found`

#### 원인
- codex 환경에 Python이 설치되지 않았거나 PATH에 없음
- 또는 Python 3.x가 `python3`로만 설치되어 있음

#### 해결 방법
```bash
# codex 환경에서
# 1. Python이 설치되어 있는지 확인
which python3 || which python

# 2. Python 3를 python으로 alias 설정
alias python=python3

# 3. 또는 python3로 직접 실행
python3 tools/ipc_register_with_responder.py codex

# 4. 가상환경 사용 시
.venv/bin/python tools/ipc_register_with_responder.py codex
```

### 3. MCP 모듈 오류

#### 현상
- `ModuleNotFoundError: No module named 'mcp'`

#### 해결 방법
```bash
# UV 사용 (권장)
uv sync

# 또는 pip 사용
pip install mcp

# 가상환경 사용
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python src/claude_ipc_server.py
```

## 수정 사항

### 1. enhanced_monitor.py 수정
- 실제 메시지 활동 시간 기반으로 상태 결정
- 마지막 메시지 송수신 시간 추적

### 2. 등록 스크립트 개선
- Python 실행 파일 자동 감지
- 다양한 Python 명령어 시도 (python, python3, py)

### 3. 문서 업데이트
- 상태 의미 명확히 설명
- Troubleshooting 섹션 추가