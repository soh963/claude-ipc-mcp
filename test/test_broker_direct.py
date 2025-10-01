#!/usr/bin/env python3
"""
Simple direct broker test without MCP interference
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import broker_client

print("\n=== Testing Direct Broker Connection ===\n")

# Test 1: List instances (should work without auth)
print("Test 1: Listing instances...")
try:
    response = broker_client._send_request({"action": "list"})
    print(f"Response: {response}")
    if response.get("status") == "ok":
        print("✓ PASS: List action works")
    else:
        print(f"✗ FAIL: {response.get('message')}")
except Exception as e:
    print(f"✗ FAIL: Connection error - {e}")

print("\nTest 2: Register instance...")
try:
    response = broker_client.register("test-direct")
    print(f"Response: {response}")
    if response.get("status") == "ok":
        token = response.get("session_token")
        print(f"✓ PASS: Registered with token {token[:16]}...")

        # Test 3: Send message
        print("\nTest 3: Send message...")
        send_resp = broker_client.send(token, "test-direct", "test-direct", "Hello self!")
        print(f"Response: {send_resp}")
        if send_resp.get("status") == "ok":
            print("✓ PASS: Message sent")
        else:
            print(f"✗ FAIL: {send_resp.get('message')}")
    else:
        print(f"✗ FAIL: {response.get('message')}")
except Exception as e:
    print(f"✗ FAIL: {e}")

print("\n=== Test Complete ===\n")
