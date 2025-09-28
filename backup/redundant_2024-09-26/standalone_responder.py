#!/usr/bin/env python
"""
Standalone responder with built-in IPC functionality
"""
import socket
import json
import sys
import time

class SimpleIPCClient:
    def __init__(self):
        self.host = 'localhost'
        self.port = 9876
        self.session_token = None

    def _send_request(self, request):
        """Send request to IPC broker"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.host, self.port))

            # Send request
            sock.sendall(json.dumps(request).encode() + b'\n')

            # Get response
            response_data = sock.recv(4096).decode()
            sock.close()

            return json.loads(response_data)
        except Exception as e:
            print(f"Error: {e}")
            return None

    def register(self, instance_id):
        """Register instance"""
        response = self._send_request({
            'action': 'register',
            'instance_id': instance_id
        })

        if response and response.get('status') == 'ok':
            self.session_token = response.get('session_token')
            return True
        return False

    def send(self, from_id, to_id, content):
        """Send message"""
        if not self.session_token:
            return False

        response = self._send_request({
            'action': 'send',
            'session_token': self.session_token,
            'from_id': from_id,
            'to_id': to_id,
            'content': content
        })

        return response and response.get('status') == 'ok'

    def check(self, instance_id):
        """Check messages"""
        if not self.session_token:
            return []

        response = self._send_request({
            'action': 'check',
            'session_token': self.session_token,
            'instance_id': instance_id
        })

        if response and response.get('status') == 'ok':
            return response.get('messages', [])
        return []

def run_responder(instance_id, role):
    """Run simple responder"""
    client = SimpleIPCClient()

    # Register
    if not client.register(instance_id):
        print(f"❌ Failed to register {instance_id}")
        return

    print(f"✅ {instance_id} registered - {role}")

    # Track responded messages
    responded = set()

    # Main loop (60 seconds)
    for i in range(30):
        messages = client.check(instance_id)

        if messages:
            for msg in messages:
                # Skip if from self
                if msg['from_id'] == instance_id:
                    continue

                # Create unique key
                msg_key = f"{msg['from_id']}_{msg['timestamp']}"

                if msg_key not in responded:
                    print(f"\n📨 [{instance_id}] Message from {msg['from_id']}: {msg['content'][:50]}...")

                    # Send response
                    response = f"Hello {msg['from_id']}! I'm {instance_id} - {role}"
                    if client.send(instance_id, msg['from_id'], response):
                        print(f"   ↩️ Responded")
                        responded.add(msg_key)

        time.sleep(2)

    print(f"\n{instance_id} done")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        instance_id = sys.argv[1]
        role = ' '.join(sys.argv[2:])
    else:
        instance_id = "test"
        role = "Test responder"

    run_responder(instance_id, role)