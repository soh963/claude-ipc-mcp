#!/usr/bin/env python3
"""Check which process is using port 9876"""
import subprocess
import sys

result = subprocess.run(
    ["netstat", "-ano"],
    capture_output=True,
    text=True
)

print("Processes using port 9876:")
print("="*80)
for line in result.stdout.split('\n'):
    if ':9876' in line:
        print(line)
print("="*80)

# Also check broker PID
from pathlib import Path
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    broker_pid = lock_file.read_text().strip()
    print(f"\nBroker lock file PID: {broker_pid}")