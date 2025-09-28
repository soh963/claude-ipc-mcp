#!/usr/bin/env python3
"""
🔥 Safe 4-Panel IPC Monitor with Auto-Responders
Starts monitoring and auto-responders in separate terminal panels
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    project_root = Path(__file__).parent.absolute()

    print("🚀 Starting Safe 4-Panel IPC Monitor System")
    print("=" * 60)

    # Kill any existing Python processes
    print("🔧 Cleaning up old processes...")
    if os.name == 'nt':
        subprocess.run("taskkill /F /IM python.exe 2>nul", shell=True, capture_output=True)
    else:
        subprocess.run("pkill -f python", shell=True, capture_output=True)

    time.sleep(2)

    # Start monitoring script
    print("📊 Starting monitoring system...")
    monitor_script = project_root / "start_split_monitoring.py"
    if monitor_script.exists():
        subprocess.Popen(
            [sys.executable, str(monitor_script)],
            cwd=str(project_root)
        )
        print("✅ Monitoring started")

    time.sleep(2)

    # Register all AI instances
    print("\n📝 Registering AI instances...")
    instances = ["claude", "gemini", "codex", "lm", "chatgpt", "llama"]
    register_script = project_root / "tools" / "ipc_register.py"

    for instance in instances:
        try:
            result = subprocess.run(
                [sys.executable, str(register_script), instance],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"  ✅ Registered: {instance}")
            else:
                print(f"  ⚠️ Failed to register: {instance}")
        except Exception as e:
            print(f"  ❌ Error registering {instance}: {e}")

    # Start auto-responders (excluding claude)
    print("\n🤖 Starting auto-responders...")
    responder_script = project_root / "tools" / "simple_auto_responder.py"
    responder_instances = ["gemini", "codex", "lm", "chatgpt", "llama"]

    for instance in responder_instances:
        try:
            if os.name == 'nt':
                # Windows: Start in new minimized window
                subprocess.Popen(
                    f'start /min "Auto-Responder {instance}" {sys.executable} {responder_script} {instance}',
                    shell=True,
                    cwd=str(project_root)
                )
            else:
                # Unix/Linux: Start in background
                subprocess.Popen(
                    [sys.executable, str(responder_script), instance],
                    cwd=str(project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            print(f"  ✅ Started auto-responder for {instance}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ❌ Error starting responder for {instance}: {e}")

    print("\n" + "=" * 60)
    print("✨ System Ready!")
    print("=" * 60)
    print("\n📚 Quick Commands:")
    print("  • Send: python tools/ipc_send.py <to> <message>")
    print("  • Check: python tools/ipc_check.py <instance>")
    print("  • List: python tools/ipc_list.py")
    print("\n🛑 To stop: Ctrl+C or close this window")
    print("=" * 60)

    try:
        # Keep running
        while True:
            time.sleep(60)
            print(f"💚 System healthy at {time.strftime('%H:%M:%S')}")
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        if os.name == 'nt':
            subprocess.run("taskkill /F /IM python.exe", shell=True)
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()