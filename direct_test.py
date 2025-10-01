#!/usr/bin/env python3
"""Direct TCP test to broker"""
import socket
import json

print("🔌 Direct TCP connection test...")

try:
    # 1. Connect
    print("  Connecting to 127.0.0.1:9876...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect(("127.0.0.1", 9876))
    print("  ✅ Connected!")
    
    # 2. Send request
    request = {"action": "list"}
    data = json.dumps(request).encode("utf-8")
    print(f"  Sending: {request}")
    s.send(data)
    
    # 3. Receive response
    print("  Waiting for response...")
    resp_data = s.recv(65536).decode("utf-8")
    print(f"  Raw response: {resp_data}")
    
    response = json.loads(resp_data)
    print(f"  Parsed response: {response}")
    
    # 4. Close
    s.close()
    print("  Connection closed")
    
    # 5. Check result
    if response.get("status") == "ok":
        print("\n✅ SUCCESS! Broker is responding correctly!")
    else:
        print(f"\n❌ FAILED: {response}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()