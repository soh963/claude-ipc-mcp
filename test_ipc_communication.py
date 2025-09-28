#!/usr/bin/env python3
"""
IPC Communication Test Script
Tests message exchange between AI instances
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd_list):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    project_root = Path(__file__).parent.absolute()
    tools_dir = project_root / "tools"

    print("🧪 IPC Communication Test")
    print("=" * 60)

    # Test instances
    instances = ["claude", "gemini", "codex", "lm", "chatgpt"]

    # Step 1: Register all instances
    print("\n1️⃣ Registering all instances...")
    for instance in instances:
        output = run_command([sys.executable, str(tools_dir / "ipc_register.py"), instance])
        if "Registered" in output:
            print(f"   ✅ {instance}: Registered successfully")
        else:
            print(f"   ❌ {instance}: Registration failed")

    # Step 2: Send test messages
    print("\n2️⃣ Sending test messages...")
    test_messages = [
        ("claude", "gemini", "안녕 Gemini! Claude입니다. 테스트 메시지입니다."),
        ("gemini", "claude", "안녕하세요 Claude! Gemini입니다. 메시지 받았습니다."),
        ("claude", "codex", "Codex, 코드 생성 준비되셨나요?"),
        ("codex", "claude", "네, 준비됐습니다. 어떤 코드가 필요하신가요?"),
        ("claude", "lm", "LM, 텍스트 처리 테스트입니다."),
        ("lm", "claude", "LM instance ready for text processing."),
    ]

    for from_id, to_id, message in test_messages:
        # Register as sender
        run_command([sys.executable, str(tools_dir / "ipc_register.py"), from_id])
        # Send message
        output = run_command([sys.executable, str(tools_dir / "ipc_send.py"), to_id, message])
        if "Sent to" in output:
            print(f"   ✅ {from_id} → {to_id}: Message sent")
        else:
            print(f"   ❌ {from_id} → {to_id}: Send failed - {output}")
        time.sleep(0.5)  # Small delay

    # Step 3: Check messages for each instance
    print("\n3️⃣ Checking messages for each instance...")
    for instance in instances:
        # Register as instance
        run_command([sys.executable, str(tools_dir / "ipc_register.py"), instance])
        # Check messages
        output = run_command([sys.executable, str(tools_dir / "ipc_check.py"), instance])

        if "No new messages" in output:
            print(f"\n   📭 {instance}: No new messages")
        elif "From:" in output:
            # Count messages
            message_count = output.count("From:")
            print(f"\n   📬 {instance}: {message_count} new message(s)")
            # Show first message
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if "From:" in line:
                    print(f"      • {line}")
                    break
        else:
            print(f"\n   ⚠️ {instance}: {output}")

    # Step 4: List all active instances
    print("\n4️⃣ Active instances:")
    output = run_command([sys.executable, str(tools_dir / "ipc_list.py")])
    if output:
        for line in output.split('\n'):
            if line.strip():
                print(f"   • {line}")

    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("\n💡 To start auto-responders, run:")
    print("   python start_auto_responders.bat")
    print("\n💡 To monitor messages, run:")
    print("   python start_split_monitoring.py")

if __name__ == "__main__":
    main()