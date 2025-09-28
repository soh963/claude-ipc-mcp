# Codex 인스턴스 등록 가이드

## 문제 해결

### Python 실행 문제
Codex 환경에서 Python을 찾을 수 없는 경우 (`python: command not found`)

#### 해결 방법 1: Python 경로 확인
```bash
# Python 설치 확인
which python3
which python
where python  # Windows

# Python 버전 확인
python3 --version
python --version
```

#### 해결 방법 2: Python Alias 설정
```bash
# Bash/Zsh에서
alias python=python3
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc

# Windows에서
doskey python=python3 $*
```

#### 해결 방법 3: 직접 Python3 사용
```bash
# 등록 스크립트 실행
python3 tools/ipc_register_with_responder.py codex

# 또는 가상환경 사용
.venv/bin/python tools/ipc_register_with_responder.py codex
```

### MCP 모듈 오류
`ModuleNotFoundError: No module named 'mcp'` 에러가 발생하는 경우

#### 해결 방법 1: UV 사용 (권장)
```bash
# UV 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

#### 해결 방법 2: 가상환경 생성 및 설치
```bash
# 가상환경 생성
python3 -m venv .venv

# 활성화 (Unix/Mac)
source .venv/bin/activate

# 활성화 (Windows)
.venv\Scripts\activate

# 패키지 설치
pip install -e .
```

#### 해결 방법 3: 시스템 Python 사용 (비권장)
```bash
# 강제 설치 (주의: 시스템 패키지 충돌 가능)
python3 -m pip install --break-system-packages mcp
```

### Codex 환경에서 완전한 설치 스크립트

```bash
#!/bin/bash

# 1. Python 확인
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Python not found. Please install Python 3.12+"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

# 2. 가상환경 생성
cd /path/to/claude-ipc-mcp
$PYTHON_CMD -m venv .venv

# 3. 가상환경 활성화
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    .venv/Scripts/activate
else
    # Unix/Mac
    source .venv/bin/activate
fi

# 4. 패키지 설치
pip install -U pip
pip install -e .

# 5. 서버 시작
.venv/bin/python src/claude_ipc_server.py &
SERVER_PID=$!
sleep 3

# 6. Codex 등록
.venv/bin/python tools/ipc_register_with_responder.py codex

echo "Codex registered successfully!"
```

### Windows PowerShell 버전

```powershell
# 1. Python 확인
$pythonCmd = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
             elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" }
             else { Write-Error "Python not found"; exit 1 }

Write-Host "Using Python: $pythonCmd"
& $pythonCmd --version

# 2. 가상환경 생성
Set-Location "D:\claude-ipc-mcp"
& $pythonCmd -m venv .venv

# 3. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 4. 패키지 설치
python -m pip install -U pip
python -m pip install -e .

# 5. 서버 시작 (백그라운드)
Start-Process python -ArgumentList "src/claude_ipc_server.py" -WindowStyle Hidden
Start-Sleep -Seconds 3

# 6. Codex 등록
python tools/ipc_register_with_responder.py codex

Write-Host "Codex registered successfully!"
```

## 권장 사항

1. **가상환경 사용**: 시스템 Python과 충돌을 피하기 위해 가상환경 사용 권장
2. **UV 사용**: 빠르고 안정적인 패키지 관리를 위해 UV 사용 권장
3. **Python 버전**: Python 3.12+ 사용 권장 (pyproject.toml 요구사항)

## 문제가 지속되는 경우

1. Python 재설치
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# MacOS
brew install python@3.12

# Windows
# python.org에서 직접 다운로드
```

2. 환경 변수 설정 확인
```bash
echo $PATH
# Python 경로가 포함되어 있는지 확인
```

3. 직접 실행
```bash
# 절대 경로로 Python 실행
/usr/bin/python3 tools/ipc_register_with_responder.py codex
```