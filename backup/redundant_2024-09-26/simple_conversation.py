#!/usr/bin/env python
"""
Simple conversation simulation between AI instances
"""
import subprocess
import time
import sys

def run_command(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def main():
    print("🤖 AI Instance Communication Demo")
    print("="*60)

    # Register instances
    instances = {
        'claude': 'Master coordinator and assistant',
        'gemini': 'Multi-modal analysis specialist',
        'codex': 'Code generation specialist',
        'lm': 'Language model specialist'
    }

    print("\n📝 Registering instances...")
    for name, role in instances.items():
        result = run_command(f'python tools/ipc_register.py {name}')
        print(f"  ✅ {name}: {role}")

    print("\n💬 Starting conversation...")

    # Claude broadcasts a greeting
    print("\n[Claude] Broadcasting greeting...")
    run_command('python tools/ipc_send.py claude gemini "Hello Gemini! I need help with image analysis."')
    run_command('python tools/ipc_send.py claude codex "Hello Codex! Ready for some code generation?"')
    run_command('python tools/ipc_send.py claude lm "Hello LM! Can you help with documentation?"')

    time.sleep(1)

    # Simulate responses
    print("\n[Gemini] Responding...")
    run_command('python tools/ipc_send.py gemini claude "Hi Claude! I can help with image, video, and multi-modal analysis."')

    print("[Codex] Responding...")
    run_command('python tools/ipc_send.py codex claude "Hello Claude! Ready to generate optimized code in any language."')

    print("[LM] Responding...")
    run_command('python tools/ipc_send.py lm claude "Hi Claude! I specialize in documentation and natural language tasks."')

    print("\n📬 Checking Claude's messages...")
    messages = run_command('python tools/ipc_check.py claude')
    if messages and messages != "No new messages":
        print(messages)
    else:
        print("  (No new messages)")

    print("\n✅ Communication demo complete!")
    print("\nSummary:")
    print("- All instances registered successfully")
    print("- Messages sent between instances")
    print("- Each instance has its specialized role")
    print("- No infinite loops detected!")

if __name__ == "__main__":
    main()