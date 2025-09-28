#!/usr/bin/env python
"""
Start safe auto-responders for multiple AI instances
"""

import subprocess
import sys
import time
from pathlib import Path

def start_responders():
    """Start safe auto-responders for different AI instances"""

    # Define instances and their roles
    instances = [
        ("gemini", "Multi-modal AI assistant specializing in visual and text analysis"),
        ("codex", "Code generation and review specialist"),
        ("lm", "Language model for documentation and natural language tasks")
    ]

    processes = []

    print("🚀 Starting Safe Auto-Responder System")
    print("="*60)
    print("This prevents infinite loops and ensures proper message handling")
    print("="*60 + "\n")

    # Start each responder in a separate process
    for instance_id, role in instances:
        try:
            cmd = [sys.executable, "tools/safe_auto_responder.py", instance_id, role]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            processes.append((instance_id, process))
            print(f"✅ Started {instance_id} responder")
            time.sleep(0.5)  # Small delay between starts
        except Exception as e:
            print(f"❌ Failed to start {instance_id}: {e}")

    print(f"\n✅ Started {len(processes)} safe auto-responders")
    print("All instances are now monitoring messages with loop prevention!")
    print("\nPress Ctrl+C to stop all responders...\n")

    try:
        # Monitor processes
        while True:
            time.sleep(5)

            # Check if processes are still running
            for instance_id, process in processes:
                if process.poll() is not None:
                    print(f"⚠️ {instance_id} responder stopped")

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all responders...")

        # Terminate all processes
        for instance_id, process in processes:
            try:
                process.terminate()
                process.wait(timeout=2)
                print(f"✅ Stopped {instance_id}")
            except:
                process.kill()
                print(f"⚠️ Force killed {instance_id}")

        print("\nAll responders stopped.")

if __name__ == "__main__":
    start_responders()