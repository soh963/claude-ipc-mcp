#!/usr/bin/env python3
"""Clean restart of broker - delete cache and restart"""
import os
import signal
import subprocess
import time
from pathlib import Path

# Delete cached compiled files
cache_dir = Path(__file__).parent / "src" / "__pycache__"
for pyc_file in cache_dir.glob("claude_ipc_server*.pyc"):
    print(f"Deleting cached file: {pyc_file}")
    pyc_file.unlink()

# Read PID from lock file and kill broker
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    pid = int(lock_file.read_text().strip())
    print(f"Killing broker process {pid}...")
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
    except ProcessLookupError:
        print(f"Process {pid} already stopped")

# Start new broker
print("Starting fresh broker process...")
broker_script = Path(__file__).parent / "src" / "claude_ipc_server.py"
log_file = Path(__file__).parent / "broker.log"

with open(log_file, "w") as f:
    f.write("=== Broker starting with clean cache ===\n")
    proc = subprocess.Popen(
        ["python", str(broker_script)],
        stdout=f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    print(f"Broker started with PID: {proc.pid}")

print("Waiting for broker to initialize...")
time.sleep(5)

# Test status
print("Testing broker status...")
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Force reload of module to ensure fresh import
import importlib
if 'claude_ipc_server' in sys.modules:
    del sys.modules['claude_ipc_server']

from core import broker_client
import json

status = broker_client.status()
print(json.dumps(status, indent=2))

if status.get("status") == "ok":
    print("\n✅ SUCCESS! Broker authentication fix is working!")
    print(f"Active instances: {len(status.get('instances', []))}")
else:
    print(f"\n❌ Still failing: {status.get('message', 'Unknown error')}")