#!/usr/bin/env python3
"""
AI CLI Detection and Auto-Registration System
Automatically detects available AI CLIs and registers them with IPC
"""

import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai_cli_adapter import AICliAdapter


def detect_and_register():
    """Detect available AI CLIs and register them"""
    print("🔍 Detecting available AI CLIs...\n")

    available = AICliAdapter.detect_available_ais()

    print("📊 Detection Results:")
    print("=" * 60)

    for ai_type, is_available in available.items():
        status = "✅ Available" if is_available else "❌ Not found"
        print(f"{status:15} | {ai_type}")

    print("=" * 60)

    # Register available AIs
    available_ais = [ai for ai, avail in available.items() if avail]

    if not available_ais:
        print("\n⚠️ No AI CLIs detected!")
        print("Please install at least one AI CLI:")
        print("  - Ollama: https://ollama.ai")
        print("  - Gemini CLI: pip install google-generativeai")
        print("  - ChatGPT CLI: pip install chatgpt-cli")
        return []

    print(f"\n🚀 Registering {len(available_ais)} AI CLI(s) with IPC...")

    registered = []
    for ai_type in available_ais:
        try:
            result = subprocess.run(
                ["uv", "run", "python", "tools/ipc_global_command.py", "register", ai_type],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                registered.append(ai_type)
                print(f"  ✅ Registered: {ai_type}")
            else:
                print(f"  ⚠️ Already registered or failed: {ai_type}")

        except Exception as e:
            print(f"  ❌ Error registering {ai_type}: {e}")

    if registered:
        print(f"\n✅ Successfully registered {len(registered)} AI(s): {', '.join(registered)}")
    else:
        print("\n⚠️ All AIs may already be registered. Use 'ipc instances list' to check.")

    return registered


def start_ai_responders(ai_types=None):
    """Start AI-powered responders for registered AIs"""
    if ai_types is None:
        available = AICliAdapter.detect_available_ais()
        ai_types = [ai for ai, avail in available.items() if avail]

    if not ai_types:
        print("⚠️ No AI types to start responders for")
        return

    print(f"\n🤖 Starting AI responders for: {', '.join(ai_types)}")
    print("=" * 60)

    for ai_type in ai_types:
        try:
            # Start AI responder in background
            cmd = [
                "uv", "run", "python",
                "tools/auto_responder_ai.py",
                ai_type
            ]

            print(f"  🚀 Starting {ai_type} responder...")

            # On Windows, use CREATE_NEW_PROCESS_GROUP to detach
            import platform
            if platform.system() == "Windows":
                # Use os.devnull to prevent 'nul' file creation
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(
                        cmd,
                        cwd=Path(__file__).parent.parent,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                        stdout=devnull,
                        stderr=devnull
                    )
            else:
                # Use os.devnull to prevent 'nul' file creation
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(
                        cmd,
                        cwd=Path(__file__).parent.parent,
                        stdout=devnull,
                        stderr=devnull,
                        start_new_session=True
                    )

            print(f"  ✅ {ai_type} responder started")

        except Exception as e:
            print(f"  ❌ Failed to start {ai_type}: {e}")

    print("=" * 60)
    print("✅ All AI responders started in background")
    print("Use 'ipc responder status <ai_type>' to check status")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI CLI Detection and Registration")
    parser.add_argument("--register", action="store_true", help="Register detected AIs")
    parser.add_argument("--start", action="store_true", help="Start AI responders")
    parser.add_argument("--all", action="store_true", help="Register and start all")

    args = parser.parse_args()

    if args.all or args.register:
        registered = detect_and_register()

    if args.all or args.start:
        start_ai_responders()

    if not (args.all or args.register or args.start):
        # Just detection
        detect_and_register()
