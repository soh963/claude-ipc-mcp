#!/usr/bin/env python3
"""Check for multiple Python processes running claude_ipc_server"""
import subprocess

result = subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
    capture_output=True,
    text=True
)

lines = result.stdout.strip().split('\n')
print(f"Found {len(lines) - 1} Python processes:")
for line in lines[1:]:  # Skip header
    parts = line.strip('"').split('","')
    if len(parts) >= 2:
        print(f"  PID: {parts[1]}")

# Check lock file
from pathlib import Path
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    lock_pid = lock_file.read_text().strip()
    print(f"\nBroker lock file PID: {lock_pid}")