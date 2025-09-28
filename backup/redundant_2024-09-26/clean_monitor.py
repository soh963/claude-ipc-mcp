#!/usr/bin/env python
"""
Clean monitoring system - shows only unique, meaningful messages
"""
import sqlite3
import time
from pathlib import Path
import hashlib

class CleanMonitor:
    def __init__(self):
        self.db_path = Path.home() / '.claude-ipc-data' / 'messages.db'
        self.seen_hashes = set()  # Track message content hashes
        self.last_id = 0

    def get_messages(self):
        """Get recent messages from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, from_id, to_id, content, timestamp
                FROM messages
                WHERE id > ?
                ORDER BY id DESC
                LIMIT 50
            """, (self.last_id,))

            messages = cursor.fetchall()
            conn.close()
            return messages
        except:
            return []

    def is_meaningful_message(self, content):
        """Check if message is meaningful (not spam)"""
        # Filter patterns that indicate spam/loops
        spam_patterns = [
            "Hello claude! This is",
            "Hello codex! This is",
            "Hello gemini! This is",
            "Hello lm! This is",
            "I received your message",
            "Auto-Responder",
            "자동 응답",
            "👋 안녕하세요"
        ]

        for pattern in spam_patterns:
            if pattern in content:
                return False

        # Filter very short repetitive messages
        if len(content) < 10:
            return False

        return True

    def display_message(self, msg):
        """Display a message if it's unique and meaningful"""
        msg_id, from_id, to_id, content, timestamp = msg

        # Update last ID
        if msg_id > self.last_id:
            self.last_id = msg_id

        # Check if meaningful
        if not self.is_meaningful_message(content):
            return False

        # Create hash of message content to detect duplicates
        msg_hash = hashlib.md5(f"{from_id}{to_id}{content}".encode()).hexdigest()

        if msg_hash in self.seen_hashes:
            return False

        self.seen_hashes.add(msg_hash)

        # Truncate long messages
        if len(content) > 100:
            content = content[:100] + "..."

        print(f"[{timestamp[:19]}] {from_id} → {to_id}")
        print(f"  {content}")
        print()
        return True

    def run(self):
        """Run clean monitor"""
        print("🧹 Clean Message Monitor")
        print("="*60)
        print("Features:")
        print("  • Filters duplicate messages")
        print("  • Removes auto-responder spam")
        print("  • Shows only meaningful communication")
        print("="*60 + "\n")

        # Get initial position
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM messages")
            result = cursor.fetchone()
            if result and result[0]:
                self.last_id = result[0] - 100  # Start from recent messages
            conn.close()
        except:
            pass

        displayed = 0
        checks = 0

        try:
            while True:
                messages = self.get_messages()

                for msg in messages:
                    if self.display_message(msg):
                        displayed += 1

                checks += 1
                if checks % 30 == 0 and displayed > 0:
                    print(f"[Stats] Displayed: {displayed} meaningful messages")

                time.sleep(3)

        except KeyboardInterrupt:
            print(f"\n✅ Monitor stopped")
            print(f"Displayed {displayed} meaningful messages")

if __name__ == "__main__":
    monitor = CleanMonitor()
    monitor.run()