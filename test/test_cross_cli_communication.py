#!/usr/bin/env python3
"""
Cross-CLI Communication E2E Test
Tests message exchange between Claude Code, Gemini CLI, and Codex CLI
"""

import sys
import os
import time
import subprocess
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import broker_client


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'


def print_step(step_num: int, description: str):
    """Print test step header"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.NC}")
    print(f"{Colors.BOLD}Step {step_num}: {description}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.NC}")


def print_pass(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ PASS:{Colors.NC} {message}")


def print_fail(message: str):
    """Print failure message"""
    print(f"{Colors.RED}✗ FAIL:{Colors.NC} {message}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ INFO:{Colors.NC} {message}")


def check_broker_running() -> bool:
    """Check if broker is running"""
    try:
        print_info("Attempting to connect to broker at 127.0.0.1:9876...")
        response = broker_client._send_request({"action": "list"})
        print_info(f"Broker response: {response}")
        return response.get("status") == "ok"
    except Exception as e:
        print_info(f"Connection error: {type(e).__name__}: {e}")
        return False


def register_instance(instance_id: str) -> dict:
    """Register an instance and return session token"""
    try:
        response = broker_client.register(instance_id)
        if response.get("status") == "ok":
            return {
                "success": True,
                "session_token": response.get("session_token")
            }
        return {"success": False, "error": response.get("message")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_message(session_token: str, from_id: str, to_id: str, content: str) -> dict:
    """Send a message between instances"""
    try:
        response = broker_client.send(session_token, from_id, to_id, content)
        return {"success": response.get("status") == "ok", "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_messages(session_token: str, instance_id: str) -> dict:
    """Check messages for an instance"""
    try:
        response = broker_client._send_request({
            "action": "check",
            "instance_id": instance_id,
            "session_token": session_token
        })
        return {
            "success": response.get("status") == "ok",
            "messages": response.get("messages", [])
        }
    except Exception as e:
        return {"success": False, "error": str(e), "messages": []}


def test_cross_cli_communication():
    """
    E2E Test: Cross-CLI Communication

    Test Scenario:
    1. Register three instances (claude-test, gemini-test, codex-test)
    2. Claude sends message to Gemini
    3. Gemini receives and replies to Claude
    4. Codex sends broadcast message
    5. All instances receive broadcast
    6. Verify message integrity
    """

    print(f"\n{Colors.BOLD}{'='*70}")
    print("Cross-CLI Communication E2E Test")
    print(f"{'='*70}{Colors.NC}\n")

    # Test configuration
    instances = {
        "claude-test": None,
        "gemini-test": None,
        "codex-test": None
    }

    # Step 1: Check broker
    print_step(1, "Checking broker status")
    if not check_broker_running():
        print_fail("Broker is not running")
        print_info("Please start broker: uv run python tools/start_broker.py")
        return False
    print_pass("Broker is running")

    # Step 2: Register all instances
    print_step(2, "Registering test instances")
    for instance_id in instances.keys():
        result = register_instance(instance_id)
        if result["success"]:
            instances[instance_id] = result["session_token"]
            print_pass(f"{instance_id} registered (token: {result['session_token'][:16]}...)")
        else:
            print_fail(f"{instance_id} registration failed: {result.get('error')}")
            return False

    # Step 3: Claude → Gemini message
    print_step(3, "Claude sends message to Gemini")
    msg_claude_to_gemini = "Hey Gemini, can you help with the API design?"
    result = send_message(
        instances["claude-test"],
        "claude-test",
        "gemini-test",
        msg_claude_to_gemini
    )
    if result["success"]:
        print_pass(f"Message sent: '{msg_claude_to_gemini}'")
    else:
        print_fail(f"Failed to send: {result.get('error')}")
        return False

    time.sleep(0.5)  # Wait for message propagation

    # Step 4: Gemini checks messages
    print_step(4, "Gemini checks messages")
    result = check_messages(instances["gemini-test"], "gemini-test")
    if result["success"]:
        messages = result["messages"]
        if len(messages) > 0:
            received = messages[0]
            print_pass(f"Gemini received {len(messages)} message(s)")
            print_info(f"From: {received.get('from_id')}")
            print_info(f"Content: {received.get('content')}")

            # Verify message content
            if received.get("content") == msg_claude_to_gemini:
                print_pass("Message content matches")
            else:
                print_fail("Message content mismatch")
                return False
        else:
            print_fail("No messages received by Gemini")
            return False
    else:
        print_fail(f"Failed to check messages: {result.get('error')}")
        return False

    # Step 5: Gemini replies to Claude
    print_step(5, "Gemini replies to Claude")
    msg_gemini_to_claude = "Sure! Let's use REST with OpenAPI specs."
    result = send_message(
        instances["gemini-test"],
        "gemini-test",
        "claude-test",
        msg_gemini_to_claude
    )
    if result["success"]:
        print_pass(f"Reply sent: '{msg_gemini_to_claude}'")
    else:
        print_fail(f"Failed to reply: {result.get('error')}")
        return False

    time.sleep(0.5)

    # Step 6: Claude receives reply
    print_step(6, "Claude receives reply from Gemini")
    result = check_messages(instances["claude-test"], "claude-test")
    if result["success"]:
        messages = result["messages"]
        if len(messages) > 0:
            received = messages[0]
            print_pass(f"Claude received {len(messages)} message(s)")
            print_info(f"From: {received.get('from_id')}")
            print_info(f"Content: {received.get('content')}")

            if received.get("content") == msg_gemini_to_claude:
                print_pass("Reply content matches")
            else:
                print_fail("Reply content mismatch")
                return False
        else:
            print_fail("No reply received by Claude")
            return False
    else:
        print_fail(f"Failed to check messages: {result.get('error')}")
        return False

    # Step 7: Codex sends to both
    print_step(7, "Codex sends messages to Claude and Gemini")
    msg_codex_to_claude = "I'll generate API tests for that design"
    msg_codex_to_gemini = "Please share the API specs when ready"

    result1 = send_message(
        instances["codex-test"],
        "codex-test",
        "claude-test",
        msg_codex_to_claude
    )
    result2 = send_message(
        instances["codex-test"],
        "codex-test",
        "gemini-test",
        msg_codex_to_gemini
    )

    if result1["success"] and result2["success"]:
        print_pass("Codex sent messages to both Claude and Gemini")
    else:
        print_fail("Codex failed to send messages")
        return False

    time.sleep(0.5)

    # Step 8: Verify both received Codex's messages
    print_step(8, "Verify Claude and Gemini received Codex's messages")

    # Check Claude
    result = check_messages(instances["claude-test"], "claude-test")
    claude_got_codex = False
    if result["success"]:
        for msg in result["messages"]:
            if msg.get("from_id") == "codex-test":
                claude_got_codex = True
                print_pass(f"Claude received Codex message: '{msg.get('content')}'")
                break

    # Check Gemini
    result = check_messages(instances["gemini-test"], "gemini-test")
    gemini_got_codex = False
    if result["success"]:
        for msg in result["messages"]:
            if msg.get("from_id") == "codex-test":
                gemini_got_codex = True
                print_pass(f"Gemini received Codex message: '{msg.get('content')}'")
                break

    if claude_got_codex and gemini_got_codex:
        print_pass("All cross-CLI messages delivered successfully")
    else:
        print_fail("Some messages were not delivered")
        return False

    # Final Summary
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}")
    print("✓ ALL TESTS PASSED!")
    print(f"{'='*70}{Colors.NC}\n")

    print("Test Summary:")
    print(f"  • {Colors.GREEN}3 instances registered{Colors.NC} (claude-test, gemini-test, codex-test)")
    print(f"  • {Colors.GREEN}5 messages exchanged{Colors.NC} successfully")
    print(f"  • {Colors.GREEN}Message integrity verified{Colors.NC} (content matches)")
    print(f"  • {Colors.GREEN}Cross-CLI communication working{Colors.NC}\n")

    return True


def main():
    """Run E2E test"""
    try:
        success = test_cross_cli_communication()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with exception: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
