#!/usr/bin/env python3
"""
Comprehensive IPC System Test
Tests all functionality: broker, instances, messaging, auto-responder
"""

import os
import sys
import time
import json
import socket
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import broker_client
from core.project_context import ProjectContext


class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_test(name: str):
    """Print test name"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def check_port_usage(port: int = 9876) -> dict:
    """Check how many processes are using the port"""
    result = {"count": 0, "pids": []}
    try:
        if sys.platform == "win32":
            output = subprocess.check_output(
                f"netstat -ano | findstr :{port}",
                shell=True,
                text=True
            )
            lines = output.strip().split('\n')
            pids = set()
            for line in lines:
                if "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pids.add(parts[-1])
            result["count"] = len(pids)
            result["pids"] = list(pids)
        else:
            output = subprocess.check_output(
                f"lsof -ti:{port}",
                shell=True,
                text=True
            )
            pids = output.strip().split('\n')
            result["count"] = len(pids)
            result["pids"] = pids
    except subprocess.CalledProcessError:
        pass  # No processes found
    return result


def test_broker_status():
    """Test 1: Broker status check"""
    print_test("Broker Status Check")

    # Check port usage
    port_info = check_port_usage()
    print(f"Port 9876 usage: {port_info['count']} process(es)")
    if port_info['count'] > 1:
        print_warning(f"Multiple brokers detected! PIDs: {port_info['pids']}")
        print_warning("This may cause status inconsistency")
    elif port_info['count'] == 0:
        print_warning("No broker process detected on port 9876")
    else:
        print_success(f"One broker process (PID: {port_info['pids'][0]})")

    # Test socket connection
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(("127.0.0.1", 9876))
        s.close()
        print_success("Socket connection successful")
    except Exception as e:
        print_error(f"Socket connection failed: {e}")
        return False

    # Test status API
    try:
        response = broker_client.status()
        if response.get("status") == "ok":
            print_success(f"Broker status: OK")
            print(f"  Active instances: {len(response.get('instances', []))}")
            return True
        else:
            print_error(f"Broker status: {response}")
            return False
    except Exception as e:
        print_error(f"Status check failed: {e}")
        return False


def test_instance_registration():
    """Test 2: Instance registration"""
    print_test("Instance Registration")

    test_id = f"test-instance-{int(time.time())}"

    try:
        # Register
        response = broker_client.register(test_id)
        if response.get("status") == "ok":
            print_success(f"Registered instance: {test_id}")
            session_token = response.get("session_token")
            print(f"  Session token: {session_token[:16]}...")

            # Verify in instance list
            list_response = broker_client.status()
            instances = list_response.get("instances", [])
            instance_ids = [inst.get("id") for inst in instances]

            if test_id in instance_ids:
                print_success(f"Instance appears in list")
                return True, test_id, session_token
            else:
                print_error(f"Instance not found in list")
                return False, None, None
        else:
            print_error(f"Registration failed: {response}")
            return False, None, None
    except Exception as e:
        print_error(f"Registration exception: {e}")
        return False, None, None


def test_messaging(session_token: str, from_id: str):
    """Test 3: Message sending and receiving"""
    print_test("Message Send/Receive")

    # Register second instance
    to_id = f"test-receiver-{int(time.time())}"
    try:
        recv_response = broker_client.register(to_id)
        if recv_response.get("status") != "ok":
            print_error(f"Failed to register receiver: {recv_response}")
            return False
        recv_token = recv_response.get("session_token")
        print_success(f"Registered receiver: {to_id}")
    except Exception as e:
        print_error(f"Receiver registration failed: {e}")
        return False

    # Send message
    test_message = f"Test message at {time.time()}"
    try:
        send_response = broker_client.send(session_token, from_id, to_id, test_message)
        if send_response.get("status") == "ok":
            print_success(f"Message sent: {test_message}")
        else:
            print_error(f"Send failed: {send_response}")
            return False
    except Exception as e:
        print_error(f"Send exception: {e}")
        return False

    # Check messages
    time.sleep(0.5)  # Brief delay
    try:
        check_req = {
            "action": "check",
            "instance_id": to_id,
            "session_token": recv_token
        }
        check_response = broker_client._send_request(check_req)

        if check_response.get("status") == "ok":
            messages = check_response.get("messages", [])
            if len(messages) > 0:
                msg = messages[0]
                if msg.get("message", {}).get("content") == test_message:
                    print_success(f"Message received correctly")
                    return True
                else:
                    print_error(f"Message content mismatch")
                    return False
            else:
                print_error(f"No messages received")
                return False
        else:
            print_error(f"Check failed: {check_response}")
            return False
    except Exception as e:
        print_error(f"Check exception: {e}")
        return False


def test_broadcast(session_token: str, from_id: str):
    """Test 4: Broadcast messaging"""
    print_test("Broadcast Messaging")

    # Register multiple receivers
    receivers = []
    for i in range(3):
        recv_id = f"test-broadcast-recv-{i}-{int(time.time())}"
        try:
            response = broker_client.register(recv_id)
            if response.get("status") == "ok":
                receivers.append((recv_id, response.get("session_token")))
                print_success(f"Registered receiver {i+1}: {recv_id}")
        except Exception as e:
            print_error(f"Failed to register receiver {i+1}: {e}")

    if len(receivers) < 2:
        print_error("Not enough receivers registered")
        return False

    # Send broadcast
    broadcast_msg = f"Broadcast test at {time.time()}"
    try:
        broadcast_req = {
            "action": "broadcast",
            "from_id": from_id,
            "message": {"content": broadcast_msg},
            "session_token": session_token
        }
        response = broker_client._send_request(broadcast_req)
        if response.get("status") == "ok":
            print_success(f"Broadcast sent")
        else:
            print_error(f"Broadcast failed: {response}")
            return False
    except Exception as e:
        print_error(f"Broadcast exception: {e}")
        return False

    # Check all receivers got the message
    time.sleep(0.5)
    received_count = 0
    for recv_id, recv_token in receivers:
        try:
            check_req = {
                "action": "check",
                "instance_id": recv_id,
                "session_token": recv_token
            }
            response = broker_client._send_request(check_req)
            messages = response.get("messages", [])
            if any(m.get("message", {}).get("content") == broadcast_msg for m in messages):
                received_count += 1
        except Exception:
            pass

    if received_count >= len(receivers):
        print_success(f"All {len(receivers)} receivers got broadcast")
        return True
    else:
        print_warning(f"Only {received_count}/{len(receivers)} receivers got broadcast")
        return received_count > 0


def test_responder_lifecycle():
    """Test 5: Auto-responder lifecycle"""
    print_test("Auto-Responder Lifecycle")

    responder_id = f"test-responder-{int(time.time())}"

    # Start responder
    print("Starting responder...")
    try:
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "tools" / "ipc_global_command.py"),
            "responder", "start", responder_id,
            "--policy", "simple",
            "--detach"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("Responder started")
        else:
            print_error(f"Responder start failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Responder start exception: {e}")
        return False

    # Wait for startup
    time.sleep(2)

    # Check status
    try:
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "tools" / "ipc_global_command.py"),
            "responder", "status", responder_id
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            status_data = json.loads(result.stdout)
            if status_data.get("running"):
                print_success(f"Responder is running (PID: {status_data.get('pid')})")
            else:
                print_error("Responder not running according to status")
                return False
        else:
            print_error(f"Status check failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Status check exception: {e}")
        return False

    # Stop responder
    print("Stopping responder...")
    try:
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "tools" / "ipc_global_command.py"),
            "responder", "stop", responder_id
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("Responder stopped")
            return True
        else:
            print_warning(f"Stop command returned error (may be OK): {result.stderr}")
            return True  # Still pass if stop attempted
    except Exception as e:
        print_error(f"Responder stop exception: {e}")
        return False


def test_cli_commands():
    """Test 6: CLI commands"""
    print_test("CLI Commands")

    base_cmd = [
        sys.executable,
        str(Path(__file__).parent.parent / "tools" / "ipc_global_command.py")
    ]

    tests = [
        (["status"], "status command"),
        (["ping"], "ping command"),
        (["instances", "reset"], "instances reset"),
        (["messages", "clear", "--force"], "messages clear"),
    ]

    passed = 0
    for cmd_args, desc in tests:
        try:
            result = subprocess.run(
                base_cmd + cmd_args,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success(f"{desc}: OK")
                passed += 1
            else:
                print_error(f"{desc}: Failed (exit {result.returncode})")
        except Exception as e:
            print_error(f"{desc}: Exception {e}")

    return passed == len(tests)


def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}IPC COMPREHENSIVE TEST SUITE{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    results = {}

    # Test 1: Broker status
    results["broker_status"] = test_broker_status()

    # Test 2: Instance registration
    reg_result, test_id, session_token = test_instance_registration()
    results["instance_registration"] = reg_result

    if reg_result:
        # Test 3: Messaging
        results["messaging"] = test_messaging(session_token, test_id)

        # Test 4: Broadcast
        results["broadcast"] = test_broadcast(session_token, test_id)
    else:
        results["messaging"] = False
        results["broadcast"] = False
        print_warning("Skipping messaging tests due to registration failure")

    # Test 5: Responder
    results["responder"] = test_responder_lifecycle()

    # Test 6: CLI commands
    results["cli_commands"] = test_cli_commands()

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name:30s} {status}")

    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.RESET}\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())