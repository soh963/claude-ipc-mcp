#!/usr/bin/env python3
"""Test broker with log flushing"""
import subprocess
import time
import sys
from pathlib import Path

# 1. Kill broker
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    pid = int(lock_file.read_text().strip())
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    time.sleep(1)
    lock_file.unlink()

# 2. Start broker with unbuffered output
log_file = Path("D:/claude-ipc-mcp/broker_flush.log")
broker_script = Path("D:/claude-ipc-mcp/src/claude_ipc_server.py")

print("Starting broker with unbuffered logging...")
with open(log_file, "w") as f:
    proc = subprocess.Popen(
        [sys.executable, "-u", str(broker_script)],  # -u for unbuffered
        stdout=f,
        stderr=subprocess.STDOUT,
        env={'PYTHONUNBUFFERED': '1'}
    )
    lock_file.write_text(str(proc.pid))
    print(f"  PID: {proc.pid}")

# 3. Wait for startup
print("Waiting 3 seconds...")
time.sleep(3)

# 4. Send test request
print("\nSending test request...")
import socket, json
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5.0)
s.connect(("127.0.0.1", 9876))
s.send(json.dumps({"action": "list"}).encode("utf-8"))
resp = s.recv(65536).decode("utf-8")
s.close()
print(f"  Response: {resp}")

# 5. Wait for logs to flush
print("\nWaiting 2 seconds for logs to flush...")
time.sleep(2)

# 6. Show logs
print("\n" + "="*80)
print("BROKER LOGS:")
print("="*80)
with open(log_file, 'r') as f:
    print(f.read())