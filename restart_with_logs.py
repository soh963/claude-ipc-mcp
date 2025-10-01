#!/usr/bin/env python3
"""Restart broker and check debug logs"""
import subprocess
import time
import sys
from pathlib import Path

print("🔄 Restarting broker with debug logs...")

# 1. Kill existing broker
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    pid = int(lock_file.read_text().strip())
    print(f"  Killing PID {pid}...")
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    time.sleep(1)
    lock_file.unlink()

# 2. Start new broker
log_file = Path("D:/claude-ipc-mcp/broker_debug.log")
broker_script = Path("D:/claude-ipc-mcp/src/claude_ipc_server.py")

print(f"  Starting broker...")
print(f"  Log: {log_file}")

with open(log_file, "w") as f:
    f.write("=== Debug Start ===\n")
    proc = subprocess.Popen(
        [sys.executable, str(broker_script)],
        stdout=f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print(f"  Started PID: {proc.pid}")
    lock_file.write_text(str(proc.pid))

# 3. Wait and test
print(f"  Waiting 3 seconds...")
time.sleep(3)

# 4. Test status
print(f"\n  Testing status...")
sys.path.insert(0, "D:/claude-ipc-mcp/src")
from core import broker_client

status = broker_client.status()
print(f"  Response: {status}")

# 5. Show logs
print(f"\n📋 Debug logs:")
with open(log_file, 'r') as f:
    for line in f:
        print(f"    {line.rstrip()}")

print("\n✅ Done!")