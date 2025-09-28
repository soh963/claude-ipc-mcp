# 🌐 Global IPC Setup Guide - AI CLI 인스턴스 통합 가이드

## 📋 목차
1. [문제 진단](#문제-진단)
2. [글로벌 환경 설정](#글로벌-환경-설정)
3. [AI CLI 인스턴스 설정](#ai-cli-인스턴스-설정)
4. [자동 등록 시스템](#자동-등록-시스템)
5. [모니터링 및 디버깅](#모니터링-및-디버깅)
6. [트러블슈팅](#트러블슈팅)

## 🔍 문제 진단

### 현재 발생하는 문제들
1. **메시지 전송은 되지만 수신/응답 안됨**
   - 원인: 각 AI CLI가 서로 다른 세션/프로세스에서 실행
   - 해결: 중앙 브로커 서버 상시 실행 필요

2. **인스턴스 인식 실패**
   - 원인: 등록 정보가 세션 종료시 소실
   - 해결: SQLite 영구 저장 및 자동 재등록

3. **글로벌 접근 불가**
   - 원인: 환경 변수 미설정, PATH 미등록
   - 해결: 시스템 레벨 환경 설정 필요

## 🌍 글로벌 환경 설정

### Step 1: 시스템 환경 변수 설정

#### Windows (PowerShell as Admin)
```powershell
# IPC 홈 디렉토리 설정
[System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_HOME", "D:\claude-ipc-mcp", "Machine")
[System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_DB", "$env:USERPROFILE\.claude-ipc-data\messages.db", "Machine")
[System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_PORT", "9876", "Machine")
[System.Environment]::SetEnvironmentVariable("CLAUDE_IPC_ENABLED", "true", "Machine")

# PATH에 tools 디렉토리 추가
$currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
$newPath = "$currentPath;D:\claude-ipc-mcp\tools"
[System.Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")

# 시스템 재시작 또는 새 터미널 열기 필요
```

#### Linux/macOS
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export CLAUDE_IPC_HOME="/path/to/claude-ipc-mcp"
export CLAUDE_IPC_DB="$HOME/.claude-ipc-data/messages.db"
export CLAUDE_IPC_PORT="9876"
export CLAUDE_IPC_ENABLED="true"
export PATH="$PATH:$CLAUDE_IPC_HOME/tools"

# 적용
source ~/.bashrc  # or source ~/.zshrc
```

### Step 2: 중앙 브로커 서버 상시 실행

#### Windows 서비스로 등록
```powershell
# 서비스 설치 스크립트 생성
New-Item -Path "D:\claude-ipc-mcp\install_service.ps1" -ItemType File
```

#### systemd 서비스 (Linux)
```bash
# /etc/systemd/system/claude-ipc.service 생성
sudo nano /etc/systemd/system/claude-ipc.service
```

## 🤖 AI CLI 인스턴스 설정

### Claude Code 설정
```json
// ~/.claude/config.json에 추가
{
  "ipc": {
    "enabled": true,
    "instance_name": "claude",
    "auto_register": true,
    "auto_respond": true
  }
}
```

### Gemini CLI 설정
```python
# ~/.gemini/startup.py
import sys
sys.path.append('D:/claude-ipc-mcp/tools')
from ipc_manager import IPCManager

# 자동 등록
ipc = IPCManager()
ipc.register("gemini")
print("✅ Gemini registered with IPC")

# 메시지 체크 함수
def check_ipc():
    messages = ipc.check("gemini")
    if messages:
        for msg in messages:
            print(f"📨 From {msg['from']}: {msg['message']['content']}")
    return messages
```

### Codex CLI 설정
```python
# ~/.codex/startup.py
import sys
import os
sys.path.append(os.environ.get('CLAUDE_IPC_HOME', 'D:/claude-ipc-mcp') + '/tools')
from ipc_manager import IPCManager

ipc = IPCManager()
ipc.register("codex")
print("✅ Codex registered with IPC")
```

## 🔄 자동 등록 시스템

### 글로벌 자동 등록 스크립트
```python
# D:\claude-ipc-mcp\global_auto_register.py
#!/usr/bin/env python3
"""
Global Auto-Registration System for AI CLI Instances
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from ipc_manager import IPCManager

class GlobalIPCRegistrar:
    def __init__(self):
        self.config_file = Path.home() / '.claude-ipc' / 'instances.json'
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.ipc = IPCManager()
        self.load_config()

    def load_config(self):
        """Load instance configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.instances = json.load(f)
        else:
            # Default configuration
            self.instances = {
                "claude": {
                    "auto_register": True,
                    "startup_check": "claude --version",
                    "enabled": True
                },
                "gemini": {
                    "auto_register": True,
                    "startup_check": "gemini --version",
                    "enabled": True
                },
                "codex": {
                    "auto_register": True,
                    "startup_check": "codex --version",
                    "enabled": True
                },
                "cursor": {
                    "auto_register": True,
                    "startup_check": "cursor --version",
                    "enabled": True
                }
            }
            self.save_config()

    def save_config(self):
        """Save instance configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.instances, f, indent=2)

    def register_all(self):
        """Register all enabled instances"""
        for name, config in self.instances.items():
            if config.get('enabled') and config.get('auto_register'):
                try:
                    result = self.ipc.register(name)
                    print(f"✅ {name}: Registered successfully")
                except Exception as e:
                    print(f"❌ {name}: Registration failed - {e}")

    def monitor_and_respond(self):
        """Monitor messages for all instances"""
        while True:
            for name in self.instances:
                if self.instances[name].get('enabled'):
                    try:
                        messages = self.ipc.check(name)
                        if messages:
                            self.process_messages(name, messages)
                    except:
                        pass
            time.sleep(1)  # Check every second

    def process_messages(self, instance_name, messages):
        """Process received messages"""
        for msg in messages:
            sender = msg.get('from')
            content = msg.get('message', {}).get('content', '')

            print(f"📨 {instance_name} received from {sender}: {content}")

            # Auto-respond logic
            if "ping" in content.lower():
                self.ipc.send(instance_name, sender, f"pong from {instance_name}")
            elif "status" in content.lower():
                self.ipc.send(instance_name, sender, f"{instance_name} is active")

if __name__ == "__main__":
    registrar = GlobalIPCRegistrar()

    # Register all instances
    registrar.register_all()

    # Start monitoring
    print("🔄 Starting global IPC monitor...")
    registrar.monitor_and_respond()
```

### Windows 시작 시 자동 실행
```batch
@echo off
REM D:\claude-ipc-mcp\startup_ipc.bat
echo Starting Global IPC System...

REM Start broker server
start /B python "D:\claude-ipc-mcp\src\claude_ipc_server.py"

REM Wait for broker to initialize
timeout /t 2 /nobreak >nul

REM Start global registrar
start /B python "D:\claude-ipc-mcp\global_auto_register.py"

REM Start monitoring UI (optional)
start /B python "D:\claude-ipc-mcp\start_split_monitoring.py"

echo ✅ Global IPC System Started
```

## 📊 모니터링 및 디버깅

### 실시간 상태 확인 도구
```python
# D:\claude-ipc-mcp\global_status.py
#!/usr/bin/env python3
"""
Global IPC Status Monitor
"""

import sys
import os
import time
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live

sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from ipc_manager import IPCManager

class GlobalStatusMonitor:
    def __init__(self):
        self.console = Console()
        self.ipc = IPCManager()

    def get_status_table(self):
        """Create status table"""
        table = Table(title=f"IPC Global Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        table.add_column("Instance", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Last Seen", style="yellow")
        table.add_column("Messages", style="magenta")

        # Get all instances
        try:
            instances = self.ipc.list_instances()
            for inst in instances:
                status = "🟢 Active" if inst.get('active') else "🔴 Inactive"
                table.add_row(
                    inst['id'],
                    status,
                    inst.get('last_seen', 'Never'),
                    str(inst.get('message_count', 0))
                )
        except Exception as e:
            table.add_row("Error", str(e), "", "")

        return table

    def monitor(self):
        """Start monitoring"""
        with Live(self.get_status_table(), refresh_per_second=1) as live:
            while True:
                time.sleep(1)
                live.update(self.get_status_table())

if __name__ == "__main__":
    monitor = GlobalStatusMonitor()
    monitor.monitor()
```

### 연결 테스트 스크립트
```python
# D:\claude-ipc-mcp\test_global_connection.py
#!/usr/bin/env python3
"""
Test Global IPC Connectivity
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from ipc_manager import IPCManager

def test_connection():
    """Test IPC connectivity between instances"""
    ipc = IPCManager()

    print("🔍 Testing Global IPC Connection...")

    # Test instances
    test_instances = ["claude", "gemini", "codex", "cursor"]

    for instance in test_instances:
        print(f"\n📌 Testing {instance}:")

        # Try to register
        try:
            result = ipc.register(instance)
            print(f"  ✅ Registration: Success")
        except Exception as e:
            print(f"  ❌ Registration: Failed - {e}")
            continue

        # Send test message to self
        try:
            ipc.send(instance, instance, f"Test from {instance}")
            print(f"  ✅ Send: Success")
        except Exception as e:
            print(f"  ❌ Send: Failed - {e}")

        # Check messages
        try:
            messages = ipc.check(instance)
            if messages:
                print(f"  ✅ Receive: {len(messages)} messages")
            else:
                print(f"  ⚠️ Receive: No messages")
        except Exception as e:
            print(f"  ❌ Receive: Failed - {e}")

    # Cross-instance test
    print("\n🔄 Cross-Instance Communication Test:")
    try:
        ipc.send("claude", "gemini", "Hello from Claude")
        ipc.send("gemini", "claude", "Hello from Gemini")
        print("  ✅ Cross-instance messaging works")
    except Exception as e:
        print(f"  ❌ Cross-instance failed: {e}")

if __name__ == "__main__":
    test_connection()
```

## 🔧 트러블슈팅

### 문제: 메시지가 전달되지 않음
```bash
# 1. 브로커 서버 확인
netstat -an | grep 9876

# 2. 데이터베이스 확인
sqlite3 ~/.claude-ipc-data/messages.db "SELECT * FROM messages;"

# 3. 로그 확인
tail -f ~/.claude-ipc/logs/broker.log
```

### 문제: 인스턴스가 등록되지 않음
```python
# 수동 등록 테스트
python -c "
from tools.ipc_manager import IPCManager
ipc = IPCManager()
print(ipc.register('test'))
"
```

### 문제: 자동 응답이 작동하지 않음
```bash
# Auto-responder 재시작
pkill -f auto_responder.py
python tools/auto_responder.py &
```

## 🚀 Quick Start 명령어

### 전체 시스템 시작
```bash
# Windows
D:\claude-ipc-mcp\startup_ipc.bat

# Linux/macOS
~/claude-ipc-mcp/startup_ipc.sh
```

### 상태 확인
```bash
python global_status.py
```

### 연결 테스트
```bash
python test_global_connection.py
```

## 📝 체크리스트

- [ ] 환경 변수 설정 완료
- [ ] 브로커 서버 자동 시작 설정
- [ ] 각 AI CLI startup 스크립트 추가
- [ ] 자동 등록 시스템 구동
- [ ] 모니터링 도구 실행
- [ ] Cross-instance 통신 테스트 성공

## 🎯 예상 결과

설정 완료 후:
1. 모든 AI CLI가 자동으로 IPC에 등록
2. 메시지 송수신이 실시간으로 작동
3. 시스템 재부팅 후에도 자동 복구
4. 글로벌 명령어로 어디서든 IPC 사용 가능

```bash
# 어디서든 사용 가능
ipc send claude gemini "Hello!"
ipc check gemini
ipc list
```