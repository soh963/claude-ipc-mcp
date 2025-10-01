#!/usr/bin/env python3
"""Simple script to restart the broker"""
import os
import signal
import subprocess
import time
from pathlib import Path

# Read PID from lock file
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    pid = int(lock_file.read_text().strip())
    print(f"Killing broker process {pid}...")
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
    except ProcessLookupError:
        print(f"Process {pid} not found")

# Start new broker
print("Starting new broker...")
broker_script = Path(__file__).parent / "src" / "claude_ipc_server.py"
log_file = Path(__file__).parent / "broker.log"

with open(log_file, "w") as f:
    subprocess.Popen(
        ["python", str(broker_script)],
        stdout=f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )

print("Broker restarted. Waiting for initialization...")
time.sleep(3)

# Test status
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))
from core import broker_client
status = broker_client.status()
print(f"Status: {status}")