#!/usr/bin/env python3
"""Force restart broker with updated code"""
import os
import subprocess
import time
from pathlib import Path

print("🛑 브로커 강제 종료 중...")

# Kill process using PID from lock file
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    pid = int(lock_file.read_text().strip())
    print(f"  PID {pid} 종료...")
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        time.sleep(2)
    except Exception as e:
        print(f"  종료 실패: {e}")

# Delete all cache files
print("\n🗑️  캐시 파일 삭제 중...")
cache_dir = Path("D:/claude-ipc-mcp/src/__pycache__")
if cache_dir.exists():
    for pyc in cache_dir.glob("*.pyc"):
        print(f"  삭제: {pyc.name}")
        pyc.unlink()

print("\n🚀 브로커 재시작 중...")
print("  Python: C:\\Python313\\python.exe")
print("  Script: D:\\claude-ipc-mcp\\src\\claude_ipc_server.py")

# Start broker
broker_script = "D:/claude-ipc-mcp/src/claude_ipc_server.py"
log_file = "D:/claude-ipc-mcp/broker.log"

with open(log_file, "w") as f:
    f.write("=== 수정된 코드로 브로커 시작 ===\n")
    proc = subprocess.Popen(
        ["python", broker_script],
        stdout=f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print(f"  ✅ 프로세스 시작됨 (PID: {proc.pid})")

print("\n⏳ 브로커 초기화 대기 중 (5초)...")
time.sleep(5)

# Test status
print("\n🔍 상태 테스트 중...")
import sys
sys.path.insert(0, "D:/claude-ipc-mcp/src")
from core import broker_client
import json

status = broker_client.status()
print(json.dumps(status, indent=2))

if status.get("status") == "ok":
    print("\n✅ 성공! 브로커 인증 수정사항이 적용되었습니다!")
    print(f"활성 인스턴스: {len(status.get('instances', []))}")
else:
    print(f"\n❌ 여전히 실패: {status.get('message', '알 수 없는 오류')}")
    print("\n브로커 로그 확인:")
    with open(log_file, "r") as f:
        print(f.read())