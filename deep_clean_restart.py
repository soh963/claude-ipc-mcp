#!/usr/bin/env python3
"""
Deep clean Python cache and restart broker with fresh code
"""
import os
import sys
import subprocess
import time
from pathlib import Path
import shutil

print("🧹 Deep Clean & Restart Broker")
print("=" * 50)

# 1. Kill existing broker
print("\n1️⃣ Stopping broker...")
lock_file = Path.home() / ".claude-ipc-data" / "broker.lock"
if lock_file.exists():
    try:
        pid = int(lock_file.read_text().strip())
        print(f"  Killing PID {pid}...")
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                      capture_output=True, check=False)
        time.sleep(2)
    except Exception as e:
        print(f"  Error killing process: {e}")

lock_file.unlink(missing_ok=True)

# 2. Remove ALL Python cache files
print("\n2️⃣ Removing Python cache files...")
project_root = Path("D:/claude-ipc-mcp")

# Remove __pycache__ directories
cache_dirs = list(project_root.rglob("__pycache__"))
print(f"  Found {len(cache_dirs)} __pycache__ directories")
for cache_dir in cache_dirs:
    try:
        shutil.rmtree(cache_dir)
        print(f"  ✓ Removed: {cache_dir.relative_to(project_root)}")
    except Exception as e:
        print(f"  ✗ Failed: {cache_dir.relative_to(project_root)} - {e}")

# Remove .pyc files
pyc_files = list(project_root.rglob("*.pyc"))
print(f"  Found {len(pyc_files)} .pyc files")
for pyc_file in pyc_files:
    try:
        pyc_file.unlink()
        print(f"  ✓ Removed: {pyc_file.relative_to(project_root)}")
    except Exception as e:
        print(f"  ✗ Failed: {pyc_file.relative_to(project_root)} - {e}")

# Remove .pyo files (Python 2 optimization files)
pyo_files = list(project_root.rglob("*.pyo"))
if pyo_files:
    print(f"  Found {len(pyo_files)} .pyo files")
    for pyo_file in pyo_files:
        try:
            pyo_file.unlink()
            print(f"  ✓ Removed: {pyo_file.relative_to(project_root)}")
        except Exception as e:
            print(f"  ✗ Failed: {pyo_file.relative_to(project_root)} - {e}")

# 3. Verify the fix is in source code
print("\n3️⃣ Verifying source code fix...")
server_file = project_root / "src" / "claude_ipc_server.py"
with open(server_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    line_622 = lines[621].strip()  # Line 622 is index 621
    if 'if action not in ("register", "list"):' in line_622:
        print(f"  ✅ Fix verified in source: {line_622}")
    else:
        print(f"  ❌ Fix NOT found! Line 622: {line_622}")

# 4. Start broker with PYTHONDONTWRITEBYTECODE=1
print("\n4️⃣ Starting broker with no bytecode cache...")
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent .pyc creation

broker_script = project_root / "src" / "claude_ipc_server.py"
log_file = project_root / "broker_clean.log"

print(f"  Python: {sys.executable}")
print(f"  Script: {broker_script}")
print(f"  Log: {log_file}")
print(f"  PYTHONDONTWRITEBYTECODE: {env.get('PYTHONDONTWRITEBYTECODE')}")

with open(log_file, "w") as f:
    f.write("=== Clean Start ===\n")
    proc = subprocess.Popen(
        [sys.executable, str(broker_script)],
        stdout=f,
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print(f"  ✅ Started process (PID: {proc.pid})")
    lock_file.write_text(str(proc.pid))

# 5. Wait and test
print("\n5️⃣ Waiting for broker initialization...")
time.sleep(3)

# 6. Test status
print("\n6️⃣ Testing broker status...")
sys.path.insert(0, str(project_root / "src"))
from core import broker_client
import json

try:
    status = broker_client.status()
    print(f"  Status response: {json.dumps(status, indent=2)}")
    
    if status.get("status") == "ok":
        print("\n✅ SUCCESS! Authentication fix is working!")
        print(f"  Active instances: {len(status.get('instances', []))}")
    else:
        print(f"\n❌ FAILED: {status.get('message', 'Unknown error')}")
        print("\n📋 Broker log (last 20 lines):")
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
            for line in log_lines[-20:]:
                print(f"    {line.rstrip()}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 50)
print("Deep clean complete!")