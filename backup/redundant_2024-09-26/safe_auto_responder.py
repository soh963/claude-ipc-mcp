#!/usr/bin/env python
"""
Safe Auto-Responder for IPC System
- Prevents infinite loops by tracking responded messages
- Only responds once to each message
- Doesn't respond to own messages
"""

import sys
import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.ipc_client import IPCClient

class SafeAutoResponder:
    def __init__(self, instance_id: str, role_description: str):
        self.instance_id = instance_id
        self.role_description = role_description
        self.client = IPCClient()
        self.responded_messages: Set[int] = set()  # Track which messages we've responded to
        self.last_check_id = 0  # Track last message ID we checked

        # Register instance
        if not self.client.register(instance_id):
            print(f"❌ Failed to register {instance_id}")
            sys.exit(1)

        print(f"✅ Registered as {instance_id}")
        print(f"📝 Role: {role_description}")

        # Get database path
        self.db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

        # Get initial last message ID to avoid responding to old messages
        self._get_last_message_id()

    def _get_last_message_id(self):
        """Get the ID of the last message in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM messages")
            result = cursor.fetchone()
            if result and result[0]:
                self.last_check_id = result[0]
                print(f"📊 Starting from message ID: {self.last_check_id}")
            conn.close()
        except Exception as e:
            print(f"⚠️ Error getting last message ID: {e}")

    def should_respond(self, message: dict) -> bool:
        """Determine if we should respond to this message"""
        # Don't respond to our own messages
        if message.get('from_id') == self.instance_id:
            return False

        # Don't respond to messages we've already responded to
        msg_id = message.get('id', 0)
        if msg_id in self.responded_messages:
            return False

        # Don't respond to old messages (before we started)
        if msg_id <= self.last_check_id:
            return False

        # Don't respond to auto-responder messages (prevent loops)
        content = message.get('content', '')
        if any(keyword in content for keyword in [
            'Auto-Responder', '자동 응답', 'ready for', 'Hello claude!'
        ]):
            return False

        return True

    def generate_response(self, message: dict) -> str:
        """Generate a contextual response"""
        from_id = message.get('from_id', 'unknown')
        content = message.get('content', '')

        # Simple contextual responses based on content
        if '협업' in content or 'collaborate' in content.lower():
            return f"[{self.instance_id}] Yes, I'm ready to collaborate! {self.role_description}"
        elif '전문' in content or 'capabilities' in content.lower():
            return f"[{self.instance_id}] My capabilities: {self.role_description}"
        elif 'hello' in content.lower() or '안녕' in content:
            return f"[{self.instance_id}] Hello {from_id}! {self.role_description}"
        else:
            return f"[{self.instance_id}] Received your message. {self.role_description}"

    def check_and_respond(self):
        """Check for new messages and respond appropriately"""
        try:
            # Get new messages from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get unread messages for this instance
            cursor.execute("""
                SELECT id, from_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND id > ?
                ORDER BY id
            """, (self.instance_id, self.last_check_id))

            messages = cursor.fetchall()
            conn.close()

            for msg in messages:
                msg_id, from_id, content, timestamp = msg

                # Update last checked ID
                self.last_check_id = max(self.last_check_id, msg_id)

                message_dict = {
                    'id': msg_id,
                    'from_id': from_id,
                    'content': content,
                    'timestamp': timestamp
                }

                if self.should_respond(message_dict):
                    print(f"\n📨 New message from {from_id}")
                    print(f"   Content: {content[:100]}...")

                    # Generate and send response
                    response = self.generate_response(message_dict)
                    if self.client.send(self.instance_id, from_id, response):
                        print(f"   ↩️ Responded: {response}")
                        self.responded_messages.add(msg_id)
                    else:
                        print(f"   ❌ Failed to send response")

        except Exception as e:
            print(f"⚠️ Error checking messages: {e}")

    def run(self):
        """Main loop"""
        print("\n" + "="*60)
        print(f"🤖 Safe Auto-Responder Started for {self.instance_id}")
        print("="*60)

        check_count = 0
        while True:
            try:
                self.check_and_respond()
                check_count += 1

                # Status update every 30 checks
                if check_count % 30 == 0:
                    print(f"⏰ Status: Active (Checks: {check_count}, Responded: {len(self.responded_messages)})")

                time.sleep(2)  # Check every 2 seconds

            except KeyboardInterrupt:
                print("\n👋 Shutting down auto-responder...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)

def main():
    if len(sys.argv) < 3:
        print("Usage: python safe_auto_responder.py <instance_id> <role>")
        print("Example: python safe_auto_responder.py gemini 'Multi-modal AI assistant'")
        sys.exit(1)

    instance_id = sys.argv[1]
    role = ' '.join(sys.argv[2:])

    responder = SafeAutoResponder(instance_id, role)
    responder.run()

if __name__ == "__main__":
    main()