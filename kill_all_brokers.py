#!/usr/bin/env python3
"""Kill ALL broker processes"""
import subprocess
import time

print("🔪 Killing ALL broker processes...")

# Find all processes using port 9876
result = subprocess.run(
    ["netstat", "-ano"],
    capture_output=True,
    text=True
)

pids = set()
for line in result.stdout.split('\n'):
    if ':9876' in line and 'LISTENING' in line:
        parts = line.split()
        pid = parts[-1]
        pids.add(pid)
        print(f"  Found PID: {pid}")

# Kill each one
for pid in pids:
    print(f"  Killing {pid}...")
    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)

print(f"  Killed {len(pids)} processes")

# Wait
print("\n  Waiting 2 seconds...")
time.sleep(2)

# Verify
result = subprocess.run(
    ["netstat", "-ano"],
    capture_output=True,
    text=True
)

still_running = []
for line in result.stdout.split('\n'):
    if ':9876' in line and 'LISTENING' in line:
        still_running.append(line)

if still_running:
    print(f"\n  ⚠️  Still {len(still_running)} processes running:")
    for line in still_running:
        print(f"    {line}")
else:
    print("\n  ✅ All brokers killed!")

# Clean lock file
from pathlib import Path
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    lock_file.unlink()
    print("  ✅ Lock file removed")

print("\n✅ Ready to start clean broker!")