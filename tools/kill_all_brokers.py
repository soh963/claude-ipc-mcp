#!/usr/bin/env python3
"""
Kill all broker processes - Emergency cleanup script
브로커 프로세스 전체 종료 - 긴급 정리 스크립트
"""
import subprocess
import sys
import platform

def kill_all_python_brokers():
    """Kill all Python processes running IPC broker"""
    print("🔪 Killing all broker processes...")

    if platform.system() == "Windows":
        # Windows: Find and kill Python processes with broker-related commands
        try:
            # List all Python processes
            result = subprocess.run(
                'tasklist /FI "IMAGENAME eq python.exe" /FO CSV',
                shell=True,
                capture_output=True,
                text=True
            )

            if "python.exe" in result.stdout:
                # Kill all python.exe processes
                subprocess.run(
                    "taskkill /F /IM python.exe",
                    shell=True,
                    capture_output=True
                )
                print("✅ Killed all python.exe processes")
            else:
                print("ℹ️ No python.exe processes found")

        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        # Unix: Find and kill Python processes
        try:
            # Find all Python processes
            result = subprocess.run(
                "ps aux | grep python | grep -E '(claude_ipc_server|start_broker|broker)' | awk '{print $2}'",
                shell=True,
                capture_output=True,
                text=True
            )

            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid.isdigit()]

            if pids:
                for pid in pids:
                    subprocess.run(f"kill -9 {pid}", shell=True)
                print(f"✅ Killed {len(pids)} broker process(es)")
            else:
                print("ℹ️ No broker processes found")

        except Exception as e:
            print(f"❌ Error: {e}")

    # Also check port 9876
    print("\n🔍 Checking port 9876...")

    if platform.system() == "Windows":
        result = subprocess.run(
            "netstat -ano | findstr :9876 | findstr LISTENING",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            # Extract PID and kill
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    subprocess.run(
                        f"taskkill /F /PID {pid}",
                        shell=True,
                        capture_output=True
                    )
                    print(f"✅ Killed process on port 9876 (PID: {pid})")
        else:
            print("✅ Port 9876 is free")
    else:
        result = subprocess.run(
            "lsof -ti:9876",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(f"kill -9 {pid}", shell=True)
            print(f"✅ Killed process(es) on port 9876")
        else:
            print("✅ Port 9876 is free")

if __name__ == "__main__":
    kill_all_python_brokers()
    print("\n✅ Cleanup complete!")
    sys.exit(0)
