#!/usr/bin/env python3
"""Rename your IPC instance ID"""
import socket
import json
import sys
import os

if len(sys.argv) != 2:
    print("Usage: ipc_rename.py <new_name>")
    print("Example: ipc_rename.py Fred-Debug")
    sys.exit(1)

new_id = sys.argv[1]

try:
    # Load session token
    session_file = os.path.expanduser("~/.ipc-session")
    if not os.path.exists(session_file):
        print("Error: Not registered. Run ipc_register.py first.")
        sys.exit(1)

    with open(session_file, "r") as f:
        session_data = json.load(f)

    old_id = session_data["instance_id"]
    session_token = session_data["session_token"]

    # Connect to IPC server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect(("127.0.0.1", 9876))

    # Send rename request
    request = {
        "action": "rename",
        "old_id": old_id,
        "new_id": new_id,
        "session_token": session_token,
    }
    s.send(json.dumps(request).encode("utf-8"))

    # Get response
    response_data = s.recv(65536).decode("utf-8")
    response = json.loads(response_data)

    s.close()

    # If successful, update session file
    if response.get("status") == "ok":
        session_data["instance_id"] = new_id
        with open(session_file, "w") as f:
            json.dump(session_data, f)

        print(f"✅ Renamed from {old_id} to {new_id}")
        print(f"\nYour old name '{old_id}' will forward to '{new_id}' for 2 hours.")
    else:
        print(json.dumps(response, indent=2))

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
