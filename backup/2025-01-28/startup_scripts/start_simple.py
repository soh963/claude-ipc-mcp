#!/usr/bin/env python3
"""
Simple IPC System Launcher - Minimal version with better error handling
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd_list, timeout=5):
    """Run a command safely"""
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def main():
    print("\n" + "="*60)
    print("    🚀 Simple IPC System Launcher")
    print("="*60)

    project_root = Path(__file__).parent.absolute()
    tools_dir = project_root / "tools"

    # Check Python
    print("\n✅ Python is working")
    print(f"📁 Project: {project_root}")

    # Register instances
    print("\n📝 Registering instances...")
    instances = ["claude", "gemini", "codex", "lm", "chatgpt"]

    for instance in instances:
        register_script = tools_dir / "ipc_register.py"
        if register_script.exists():
            success, out, err = run_command([sys.executable, str(register_script), instance])
            if success and "Registered" in out:
                print(f"   ✅ {instance}")
            else:
                print(f"   ⚠️ {instance}: {err if err else 'Failed'}")
        else:
            print(f"   ❌ Register script not found!")
            break

    # Test communication
    print("\n🧪 Testing communication...")
    send_script = tools_dir / "ipc_send.py"

    if send_script.exists():
        # Register as claude first
        run_command([sys.executable, str(tools_dir / "ipc_register.py"), "claude"])

        # Send test message
        success, out, err = run_command(
            [sys.executable, str(send_script), "gemini", "Test message from launcher"]
        )
        if success and "Sent to" in out:
            print("   ✅ Messages can be sent")
        else:
            print(f"   ⚠️ Send test failed: {err}")

    # List instances
    print("\n👥 Active instances:")
    list_script = tools_dir / "ipc_list.py"

    if list_script.exists():
        success, out, err = run_command([sys.executable, str(list_script)])
        if success:
            count = out.count("ID:")
            print(f"   ✅ {count} instances registered")
        else:
            print("   ⚠️ Could not list instances")

    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)

    print("\n📚 Commands you can use:")
    print("  python tools/ipc_send.py <to> <message>")
    print("  python tools/ipc_check.py <instance>")
    print("  python tools/ipc_list.py")
    print("  python test_ipc_communication.py")

    print("\n💡 To start auto-responders:")
    print("  python tools/simple_auto_responder.py gemini &")
    print("  (repeat for other instances)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()