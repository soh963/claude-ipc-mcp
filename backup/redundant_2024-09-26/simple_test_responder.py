#!/usr/bin/env python
"""
Simple test responder - responds once to each unique message
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.ipc_client import IPCClient
import time
import random

def run_responder(instance_id, role):
    """Run a simple responder that responds once to each message"""
    client = IPCClient()

    # Register
    if not client.register(instance_id):
        print(f"Failed to register {instance_id}")
        return

    print(f"✅ {instance_id} registered - {role}")

    # Track what we've already responded to
    responded_to = set()

    # Check messages periodically
    for i in range(30):  # Run for 60 seconds max
        messages = client.check(instance_id)

        if messages:
            for msg in messages:
                # Create unique key for this message
                msg_key = f"{msg['from_id']}_{msg['timestamp']}_{msg['content'][:50]}"

                # Skip if we already responded to this exact message
                if msg_key in responded_to:
                    continue

                # Skip messages from ourselves
                if msg['from_id'] == instance_id:
                    continue

                # Skip auto-responder messages to prevent loops
                if 'auto-responder' in msg['content'].lower():
                    continue

                print(f"\n📨 [{instance_id}] Got message from {msg['from_id']}")
                print(f"   Content: {msg['content'][:100]}")

                # Send a simple response
                response = f"Hello {msg['from_id']}! I'm {instance_id} - {role}"
                if client.send(instance_id, msg['from_id'], response):
                    print(f"   ↩️ Sent response")
                    responded_to.add(msg_key)

        time.sleep(2)

    print(f"\n{instance_id} shutting down")

if __name__ == "__main__":
    # Run a single responder
    if len(sys.argv) >= 2:
        instance_id = sys.argv[1]
        role = sys.argv[2] if len(sys.argv) > 2 else "Test responder"
    else:
        instance_id = "test_responder"
        role = "Test responder"

    run_responder(instance_id, role)