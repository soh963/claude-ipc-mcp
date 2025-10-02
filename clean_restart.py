#!/usr/bin/env python3
"""Clean restart script - kills all Python processes, starts fresh broker, registers instances, starts responders"""

import subprocess
import time
import sys
from pathlib import Path

def run_cmd(cmd, description):
    """Run a command and print status"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[:200]}")
            return True
        else:
            print(f"⚠️ {description} - Warning (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()[:200]}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("=" * 80)
    print("🧹 IPC SYSTEM CLEAN RESTART")
    print("=" * 80)

    # 1. Kill all Python processes
    run_cmd(
        'powershell -Command "Stop-Process -Name python -Force -ErrorAction SilentlyContinue"',
        "Stopping all Python processes"
    )
    time.sleep(3)

    # 2. Start broker in background
    print("\n🚀 Starting broker...")
    subprocess.Popen(
        ["uv", "run", "python", "tools/start_broker.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    time.sleep(5)

    # 3. Register instances
    instances = ["claude", "gemini", "test-tem-main", "mock"]
    print(f"\n📝 Registering {len(instances)} instances...")
    for instance in instances:
        run_cmd(
            f'uv run python tools/ipc_global_command.py register {instance}',
            f"Register {instance}"
        )
        time.sleep(1)

    # 4. Start all responders
    run_cmd(
        'uv run python tools/ipc_global_command.py responder start-all --policy smart --detach',
        "Starting all auto-responders"
    )

    # 5. Verify status
    print("\n" + "=" * 80)
    print("📊 FINAL STATUS CHECK")
    print("=" * 80)
    run_cmd(
        'uv run python tools/ipc_global_command.py instances list --full',
        "List all instances"
    )

    print("\n" + "=" * 80)
    print("✅ CLEAN RESTART COMPLETE!")
    print("=" * 80)
    print("\n💡 You can now test broadcast messages:")
    print("   python test_broadcast.py")

if __name__ == "__main__":
    main()
