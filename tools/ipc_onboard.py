#!/usr/bin/env python3
"""
IPC Onboarding Tool - One-click instance setup

Automatically handles:
- Broker availability check and startup
- Instance registration
- Session token storage
- Auto-responder activation
- Connection verification
"""

import sys
import os
import time
import argparse
import subprocess
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import broker_client
from core import responder_proc
from core.project_context import write_session, state_file


def check_and_start_broker() -> bool:
    """Check if broker is running, start if needed"""
    print("🔍 Checking broker status...")

    if broker_client.is_broker_available():
        print("✅ Broker is running")
        return True

    print("⚠️  Broker not running. Starting broker...")

    # Get script directory
    script_dir = Path(__file__).parent
    broker_script = script_dir / "start_broker.py"

    if not broker_script.exists():
        print(f"❌ Broker script not found: {broker_script}")
        return False

    # Start broker in background
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                ["python", str(broker_script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:  # Unix-like
            # Use os.devnull to prevent 'nul' file creation
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen(
                    ["python3", str(broker_script)],
                    stdout=devnull,
                    stderr=devnull
                )

        # Wait for broker to start
        print("⏳ Waiting for broker to start...")
        for i in range(10):
            time.sleep(1)
            if broker_client.is_broker_available():
                print("✅ Broker started successfully")
                return True
            print(f"   Attempt {i+1}/10...")

        print("❌ Broker failed to start within 10 seconds")
        return False

    except Exception as e:
        print(f"❌ Failed to start broker: {e}")
        return False


def register_instance(instance_id: str) -> dict:
    """Register instance with broker"""
    print(f"\n📝 Registering instance: {instance_id}")

    try:
        response = broker_client.register(instance_id)

        if response.get("status") == "ok":
            session_token = response.get("session_token")
            print(f"✅ Registration successful")
            print(f"   Session token: {session_token[:16]}...")
            return {"session_token": session_token, "success": True}
        else:
            error_msg = response.get("message", "Unknown error")
            print(f"❌ Registration failed: {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        print(f"❌ Registration error: {e}")
        return {"success": False, "error": str(e)}


def save_session(instance_id: str, session_token: str) -> bool:
    """Save session token to project context"""
    print(f"\n💾 Saving session...")

    try:
        write_session(instance_id, session_token)

        session_file_path = state_file()
        print(f"✅ Session saved to: {session_file_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to save session: {e}")
        return False


def start_auto_responder(instance_id: str, policy: str = "smart", detach: bool = True) -> bool:
    """Start auto-responder for instance"""
    print(f"\n🤖 Starting auto-responder (policy: {policy})...")

    try:
        # Check if responder already running
        status = responder_proc.get_status(instance_id)

        if status.get("running"):
            pid = status.get("pid")
            print(f"⚠️  Auto-responder already running (PID: {pid})")
            return True

        # Start responder
        result = responder_proc.start_responder(
            instance_id=instance_id,
            policy=policy,
            detach=detach
        )

        if result.get("status") == "ok":
            pid = result.get("pid")
            print(f"✅ Auto-responder started (PID: {pid})")
            return True
        else:
            error = result.get("message", "Unknown error")
            print(f"❌ Failed to start responder: {error}")
            return False

    except Exception as e:
        print(f"❌ Responder error: {e}")
        return False


def verify_connection(session_token: str) -> bool:
    """Verify IPC connection with ping test"""
    print(f"\n🏓 Verifying connection...")

    try:
        response = broker_client.ping(session_token)

        if response.get("status") == "ok":
            rtt = response.get("rtt_ms", 0)
            print(f"✅ Ping successful: {rtt:.2f}ms")
            return True
        else:
            error = response.get("message", "Unknown error")
            print(f"❌ Ping failed: {error}")
            return False

    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False


def show_next_steps(instance_id: str):
    """Show helpful next steps"""
    print(f"\n" + "="*60)
    print(f"🎉 {instance_id} is ready for IPC!")
    print("="*60)
    print(f"\n📚 Next steps:")
    print(f"")
    print(f"1. Check status:")
    print(f"   /ipc:status")
    print(f"")
    print(f"2. List other instances:")
    print(f"   /ipc:list")
    print(f"")
    print(f"3. Send a message:")
    print(f"   /ipc:send {instance_id} <target> <message>")
    print(f"")
    print(f"4. Check messages:")
    print(f"   /ipc:check {instance_id}")
    print(f"")
    print(f"5. View responder status:")
    print(f"   /ipc:responder-status {instance_id}")
    print(f"")
    print(f"💡 Tip: Auto-responder is running, so you'll automatically")
    print(f"         reply to messages even when you're offline!")
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="One-click IPC onboarding for AI instances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic onboarding with smart responder
  python ipc_onboard.py --name claude-main --policy smart

  # Onboarding without auto-responder
  python ipc_onboard.py --name gemini-test --no-responder

  # Simple echo responder
  python ipc_onboard.py --name codex-dev --policy simple
        """
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Instance name (alphanumeric, dash, underscore only)"
    )

    parser.add_argument(
        "--policy",
        choices=["simple", "smart"],
        default="smart",
        help="Auto-responder policy (default: smart)"
    )

    parser.add_argument(
        "--no-responder",
        action="store_true",
        help="Skip auto-responder setup"
    )

    parser.add_argument(
        "--no-detach",
        action="store_true",
        help="Run responder in foreground (for debugging)"
    )

    args = parser.parse_args()

    # Validate instance name
    instance_id = args.name
    if not instance_id or len(instance_id) > 32:
        print("❌ Instance name must be 1-32 characters")
        return 1

    print("")
    print("="*60)
    print(f"🚀 IPC Onboarding: {instance_id}")
    print("="*60)

    # Step 1: Check broker
    if not check_and_start_broker():
        print("\n❌ Onboarding failed: Broker not available")
        return 1

    # Step 2: Register instance
    reg_result = register_instance(instance_id)
    if not reg_result["success"]:
        print(f"\n❌ Onboarding failed: {reg_result.get('error')}")
        return 1

    session_token = reg_result["session_token"]

    # Step 3: Save session
    if not save_session(instance_id, session_token):
        print("\n⚠️  Session not saved, but registration successful")

    # Step 4: Verify connection
    if not verify_connection(session_token):
        print("\n⚠️  Connection test failed, but registration successful")

    # Step 5: Start auto-responder (optional)
    if not args.no_responder:
        detach = not args.no_detach
        start_auto_responder(instance_id, args.policy, detach)
    else:
        print("\n⏭️  Skipping auto-responder setup (--no-responder)")

    # Show next steps
    show_next_steps(instance_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
