# 500 Internal Server Error 해결 가이드

## 에러 설명
`exceeded retry limit, last status: 500 Internal Server Error` 에러는 Claude Code CLI가 서버와 통신할 때 발생하는 에러입니다.

## 원인 분석

### 1. **서버 과부하**
- Claude API 서버의 일시적 과부하
- 너무 많은 동시 요청
- Rate limiting 초과

### 2. **네트워크 문제**
- 불안정한 인터넷 연결
- 프록시 또는 방화벽 차단
- DNS 해석 실패

### 3. **토큰/인증 문제**
- API 키 만료 또는 무효화
- 권한 부족
- 세션 타임아웃

### 4. **요청 크기 문제**
- 너무 큰 요청 페이로드
- 컨텍스트 길이 초과
- 메모리 부족

## 즉시 해결 방법

### 1. **재시작 및 대기**
```bash
# 1. 모든 백그라운드 프로세스 종료
taskkill /F /IM python.exe

# 2. 5-10초 대기

# 3. 다시 시작
claude-code
```

### 2. **컨텍스트 초기화**
- 새로운 세션 시작
- 큰 파일이나 긴 대화 피하기
- `--uc` (ultracompressed) 모드 사용

### 3. **네트워크 확인**
```bash
# 인터넷 연결 확인
ping api.anthropic.com

# DNS 확인
nslookup api.anthropic.com

# 프록시 설정 확인
echo %HTTP_PROXY%
echo %HTTPS_PROXY%
```

### 4. **API 키 재설정**
```bash
# Windows
set ANTHROPIC_API_KEY=your-new-api-key

# 또는 .env 파일 수정
echo ANTHROPIC_API_KEY=your-new-api-key > .env
```

## 예방 조치

### 1. **요청 최적화**
```python
# 큰 요청을 작은 청크로 분할
def chunk_request(data, chunk_size=1000):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# Rate limiting 적용
import time

def rate_limited_request(func, delay=1):
    def wrapper(*args, **kwargs):
        time.sleep(delay)  # 요청 간 지연
        return func(*args, **kwargs)
    return wrapper
```

### 2. **에러 핸들링 개선**
```python
import time
from typing import Optional

class RetryHandler:
    def __init__(self, max_retries=5, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "500" in str(e):
                    # Exponential backoff
                    delay = self.base_delay * (2 ** attempt)
                    print(f"Retry {attempt + 1}/{self.max_retries} in {delay}s...")
                    time.sleep(delay)
                else:
                    raise e
        raise Exception(f"Failed after {self.max_retries} retries")
```

### 3. **백그라운드 프로세스 관리**
```python
# tools/process_manager.py
import psutil
import os

def cleanup_zombie_processes():
    """좀비 프로세스 정리"""
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        if proc.info['name'] == 'python.exe':
            if proc.info['status'] == 'zombie':
                proc.kill()
            # 10분 이상 된 프로세스 종료
            elif proc.create_time() < time.time() - 600:
                if proc.pid != current_pid:
                    proc.terminate()
```

### 4. **로컬 IPC 사용**
IPC 시스템을 사용하여 Claude API 의존성 감소:
```python
# Claude API 대신 로컬 IPC 사용
from tools.ipc_manager import IPCManager

ipc = IPCManager()
# API 호출 대신 로컬 메시지
ipc.send("claude", "gemini", "파일 리스트 요청")
```

## 모니터링 설정

### 1. **에러 로깅**
```python
# tools/error_logger.py
import logging
from datetime import datetime

logging.basicConfig(
    filename='error_log.txt',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_500_error(error_details):
    logging.error(f"500 Error: {error_details}")
    # 에러 횟수 추적
    with open('500_error_count.txt', 'a') as f:
        f.write(f"{datetime.now()}: {error_details}\n")
```

### 2. **상태 체크**
```bash
# 상태 체크 스크립트
@echo off
echo === System Status Check ===
echo.
echo 1. Network Status:
ping -n 1 api.anthropic.com
echo.
echo 2. Python Processes:
tasklist | findstr python
echo.
echo 3. Memory Usage:
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory
echo.
echo 4. Active IPC Sessions:
python tools/ipc_manager.py list
```

## 자동 복구 스크립트

```python
# tools/auto_recovery.py
#!/usr/bin/env python3
import subprocess
import time
import sys

def auto_recover_500_error():
    """500 에러 자동 복구"""
    print("🔧 500 Error detected, starting recovery...")

    # 1. 모든 Python 프로세스 종료
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"],
                   capture_output=True)
    time.sleep(3)

    # 2. 캐시 정리
    import shutil
    cache_dirs = [
        "~/.cache/claude",
        "~/.claude/cache",
        "./tmp"
    ]
    for dir in cache_dirs:
        try:
            shutil.rmtree(os.path.expanduser(dir))
        except:
            pass

    # 3. IPC 시스템 재시작
    subprocess.Popen(["python", "tools/auto_responder.py"])

    print("✅ Recovery complete!")
    return True

if __name__ == "__main__":
    auto_recover_500_error()
```

## 권장 설정

### .env 파일
```bash
# API 설정
ANTHROPIC_API_KEY=your-key
ANTHROPIC_TIMEOUT=30
ANTHROPIC_MAX_RETRIES=5
ANTHROPIC_RETRY_DELAY=2

# 로컬 설정
USE_LOCAL_FALLBACK=true
LOCAL_IPC_ENABLED=true
AUTO_RECOVERY_ENABLED=true
```

### 시작 스크립트 개선
```batch
@echo off
REM start_with_recovery.bat

echo Starting Claude IPC with auto-recovery...

:LOOP
python tools/auto_responder.py
if %ERRORLEVEL% NEQ 0 (
    echo Error detected, recovering...
    python tools/auto_recovery.py
    timeout /t 5
    goto LOOP
)
```

## 결론

500 Internal Server Error는 주로 일시적인 문제이며, 위의 방법들로 해결할 수 있습니다:

1. **즉시 조치**: 프로세스 재시작, 대기
2. **예방 조치**: Rate limiting, 청크 분할
3. **자동 복구**: 에러 감지 및 자동 재시작
4. **로컬 대안**: IPC 시스템 활용

로컬 IPC 시스템을 활용하면 Claude API 의존성을 줄이고 안정적인 작업이 가능합니다.