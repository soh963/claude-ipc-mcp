#!/usr/bin/env python3
"""Check broker connection directly"""
import socket
import json

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    sock.connect(("127.0.0.1", 9876))

    # Send list request
    request = json.dumps({"action": "list"})
    sock.sendall(request.encode() + b'\n')

    # Receive response
    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
        if b'\n' in response:
            break

    sock.close()

    result = json.loads(response.decode().strip())
    print(f"Raw response: {json.dumps(result, indent=2)}")

except Exception as e:
    print(f"Error: {e}")