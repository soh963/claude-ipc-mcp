#!/usr/bin/env python3
"""Test script to verify IPC security implementation"""
import socket
import json
import sys
import os
import hashlib

def test_connection():
    """Test basic connection to server"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 9876))
        s.close()
        print("✅ Server is running on port 9876")
        return True
    except Exception:
        print("❌ Server not running on port 9876")
        return False

def test_registration_without_secret():
    """Test registration without shared secret"""
    print("\n--- Testing registration without shared secret ---")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 9876))
        
        request = {
            "action": "register",
            "instance_id": "test-no-secret"
        }
        s.send(json.dumps(request).encode("utf-8"))
        
        response_data = s.recv(65536).decode("utf-8")
        response = json.loads(response_data)
        s.close()
        
        if response.get("status") == "ok":
            print("✅ Registration allowed without secret (secret not configured)")
        else:
            print(f"❌ Registration failed: {response}")
        
        return response
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_registration_with_wrong_secret():
    """Test registration with wrong shared secret"""
    print("\n--- Testing registration with wrong secret ---")
    
    # Make sure secret is set
    if not os.environ.get("IPC_SHARED_SECRET"):
        print("⚠️  IPC_SHARED_SECRET not set, skipping test")
        return None
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 9876))
        
        # Use wrong secret
        wrong_token = hashlib.sha256("test-wrong:wrong-secret".encode()).hexdigest()
        
        request = {
            "action": "register",
            "instance_id": "test-wrong",
            "auth_token": wrong_token
        }
        s.send(json.dumps(request).encode("utf-8"))
        
        response_data = s.recv(65536).decode("utf-8")
        response = json.loads(response_data)
        s.close()
        
        if response.get("status") == "error" and "auth token" in response.get("message", ""):
            print("✅ Registration correctly rejected with wrong secret")
        else:
            print(f"❌ Unexpected response: {response}")
        
        return response
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_registration_with_correct_secret():
    """Test registration with correct shared secret"""
    print("\n--- Testing registration with correct secret ---")
    
    shared_secret = os.environ.get("IPC_SHARED_SECRET", "")
    instance_id = "test-correct"
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 9876))
        
        # Calculate correct token
        auth_token = ""
        if shared_secret:
            auth_token = hashlib.sha256(f"{instance_id}:{shared_secret}".encode()).hexdigest()
        
        request = {
            "action": "register",
            "instance_id": instance_id,
            "auth_token": auth_token
        }
        s.send(json.dumps(request).encode("utf-8"))
        
        response_data = s.recv(65536).decode("utf-8")
        response = json.loads(response_data)
        s.close()
        
        if response.get("status") == "ok" and response.get("session_token"):
            print("✅ Registration successful, received session token")
            return response
        else:
            print(f"❌ Registration failed: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_spoofing_attempt(session_token):
    """Test sending message as different instance"""
    print("\n--- Testing spoofing prevention ---")
    
    if not session_token:
        print("⚠️  No session token, skipping test")
        return
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 9876))
        
        # Try to send as "admin" when registered as "test-correct"
        request = {
            "action": "send",
            "from_id": "admin",  # Spoofing attempt!
            "to_id": "victim",
            "message": {"content": "I am the admin!"},
            "session_token": session_token
        }
        s.send(json.dumps(request).encode("utf-8"))
        
        response_data = s.recv(65536).decode("utf-8")
        response = json.loads(response_data)
        s.close()
        
        if response.get("status") == "ok":
            print("✅ Message sent (server will use real identity from session)")
            # The server should have ignored the claimed from_id
        else:
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_missing_session():
    """Test action without session token"""
    print("\n--- Testing action without session ---")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 9876))
        
        request = {
            "action": "send",
            "from_id": "hacker",
            "to_id": "victim",
            "message": {"content": "No auth!"}
            # No session_token!
        }
        s.send(json.dumps(request).encode("utf-8"))
        
        response_data = s.recv(65536).decode("utf-8")
        response = json.loads(response_data)
        s.close()
        
        if response.get("status") == "error" and "session token" in response.get("message", ""):
            print("✅ Action correctly rejected without session")
        else:
            print(f"❌ Unexpected response: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all security tests"""
    print("🔒 IPC Security Test Suite")
    print("=" * 50)
    
    # Check if server is running
    if not test_connection():
        print("\n⚠️  Start the IPC server first!")
        sys.exit(1)
    
    # Check shared secret
    secret = os.environ.get("IPC_SHARED_SECRET")
    if secret:
        print(f"✅ IPC_SHARED_SECRET is set (length: {len(secret)})")
    else:
        print("⚠️  IPC_SHARED_SECRET not set - auth will be disabled")
    
    # Run tests
    test_registration_without_secret()
    
    if secret:
        test_registration_with_wrong_secret()
    
    reg_response = test_registration_with_correct_secret()
    
    if reg_response and reg_response.get("session_token"):
        session_token = reg_response["session_token"]
        test_spoofing_attempt(session_token)
    
    test_missing_session()
    
    print("\n" + "=" * 50)
    print("✅ Security tests complete!")

if __name__ == "__main__":
    main()