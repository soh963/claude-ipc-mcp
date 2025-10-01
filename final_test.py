#!/usr/bin/env python3
"""Final comprehensive test"""
import subprocess
import time
import sys
import socket
import json
from pathlib import Path

print("=" * 80)
print("FINAL COMPREHENSIVE TEST")
print("=" * 80)

# 1. Kill broker
print("\n1. Stopping existing broker...")
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    pid = int(lock_file.read_text().strip())
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    time.sleep(2)
    lock_file.unlink()
    print("   ✓ Stopped")

# 2. Start broker normally (no special env)
print("\n2. Starting broker normally...")
log_file = Path("D:/claude-ipc-mcp/broker_final.log")
broker_script = Path("D:/claude-ipc-mcp/src/claude_ipc_server.py")

with open(log_file, "w") as f:
    proc = subprocess.Popen(
        [sys.executable, str(broker_script)],
        stdout=f,
        stderr=subprocess.STDOUT
    )
    lock_file.write_text(str(proc.pid))
    print(f"   ✓ Started (PID: {proc.pid})")

# 3. Wait
print("\n3. Waiting 4 seconds for initialization...")
time.sleep(4)

# 4. Send request
print("\n4. Sending test request...")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect(("127.0.0.1", 9876))
    
    request = {"action": "list"}
    print(f"   → Sending: {request}")
    s.send(json.dumps(request).encode("utf-8"))
    
    resp = s.recv(65536).decode("utf-8")
    print(f"   ← Response: {resp}")
    
    response = json.loads(resp)
    s.close()
    
    # 5. Check result
    print("\n5. Result Analysis:")
    if response.get("status") == "ok":
        print("   ✅ SUCCESS! Auth fix is working!")
        print(f"   Instances: {response.get('instances', [])}")
    else:
        print(f"   ❌ FAILED: {response.get('message')}")
        print(f"   This means line 634 check is NOT working!")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# 6. Show first 30 lines of log
print("\n6. Broker log (first 30 lines):")
print("-" * 80)
with open(log_file, 'r') as f:
    for i, line in enumerate(f):
        if i >= 30:
            break
        print(f"   {line.rstrip()}")
print("-" * 80)

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)