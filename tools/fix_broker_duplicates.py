#!/usr/bin/env python3
"""
Fix Broker Duplicate Instances
Detects and terminates duplicate broker processes, keeping only one
"""

import sys
import subprocess
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def get_broker_pids(port: int = 9876) -> list:
    """Get all PIDs using the broker port"""
    pids = []
    try:
        if sys.platform == "win32":
            output = subprocess.check_output(
                f"netstat -ano | findstr :{port}",
                shell=True,
                text=True
            )
            lines = output.strip().split('\n')
            pid_set = set()
            for line in lines:
                if "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid_set.add(parts[-1])
            pids = sorted(list(pid_set))
        else:
            output = subprocess.check_output(
                f"lsof -ti:{port}",
                shell=True,
                text=True
            )
            pids = output.strip().split('\n')
    except subprocess.CalledProcessError:
        pass  # No processes found
    return pids


def kill_process(pid: str) -> bool:
    """Kill a process by PID"""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", pid],
                         capture_output=True, check=True)
        else:
            subprocess.run(["kill", "-9", pid],
                         capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    """Main function"""
    print("🔍 Checking for duplicate broker processes...")

    pids = get_broker_pids()

    if len(pids) == 0:
        print("✓ No broker processes found on port 9876")
        return 0
    elif len(pids) == 1:
        print(f"✓ One broker process found (PID: {pids[0]})")
        return 0
    else:
        print(f"⚠ Multiple broker processes detected: {len(pids)}")
        for i, pid in enumerate(pids, 1):
            print(f"  {i}. PID {pid}")

        # Keep the first (oldest) and kill others
        keep_pid = pids[0]
        kill_pids = pids[1:]

        print(f"\n📌 Keeping PID {keep_pid}")
        print(f"🔪 Terminating {len(kill_pids)} duplicate(s)...")

        killed = 0
        for pid in kill_pids:
            if kill_process(pid):
                print(f"  ✓ Killed PID {pid}")
                killed += 1
            else:
                print(f"  ✗ Failed to kill PID {pid}")

        # Wait and verify
        time.sleep(1)
        remaining = get_broker_pids()

        if len(remaining) == 1:
            print(f"\n✅ Success! One broker process remains (PID: {remaining[0]})")
            return 0
        elif len(remaining) == 0:
            print("\n⚠ Warning: No broker processes remain. You may need to restart the broker.")
            return 1
        else:
            print(f"\n❌ Error: {len(remaining)} processes still remain")
            return 1


if __name__ == "__main__":
    sys.exit(main())