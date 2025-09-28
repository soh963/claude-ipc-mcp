#!/usr/bin/env python
"""
Safe monitoring tool that prevents infinite loops and duplicate messages
"""
import sqlite3
import time
from pathlib import Path
from datetime import datetime
import sys

class SafeMonitor:
    def __init__(self):
        self.db_path = Path.home() / '.claude-ipc-data' / 'messages.db'
        self.last_message_id = 0
        self.displayed_messages = set()  # Track displayed message IDs

    def get_new_messages(self):
        """Get only new messages that haven't been displayed yet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get messages newer than our last check
            cursor.execute("""
                SELECT id, from_id, to_id, content, timestamp
                FROM messages
                WHERE id > ?
                ORDER BY id DESC
                LIMIT 100
            """, (self.last_message_id,))

            messages = cursor.fetchall()
            conn.close()

            new_messages = []
            for msg in messages:
                msg_id = msg[0]
                if msg_id not in self.displayed_messages:
                    new_messages.append(msg)
                    self.displayed_messages.add(msg_id)
                    self.last_message_id = max(self.last_message_id, msg_id)

            return new_messages
        except Exception as e:
            print(f"Error reading database: {e}")
            return []

    def format_message(self, msg):
        """Format message for display"""
        msg_id, from_id, to_id, content, timestamp = msg

        # Truncate long or repetitive content
        if len(content) > 100:
            content = content[:100] + "..."

        # Skip auto-responder spam messages
        if "자동 응답" in content or "Auto-Responder" in content:
            return None
        if "👋 안녕하세요" in content and content.count("안녕하세요") > 1:
            return None  # Skip duplicate greeting messages

        return f"[{timestamp[:19]}] {from_id} → {to_id}: {content}"

    def run(self):
        """Run the monitoring loop"""
        print("🔍 Safe Message Monitor")
        print("="*60)
        print("Monitoring messages (Ctrl+C to stop)")
        print("Duplicate prevention: ENABLED")
        print("Auto-responder filtering: ENABLED")
        print("="*60 + "\n")

        # Get initial message count
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM messages")
            result = cursor.fetchone()
            if result and result[0]:
                self.last_message_id = result[0]
                print(f"📊 Starting from message ID: {self.last_message_id}\n")
            conn.close()
        except:
            pass

        check_count = 0
        try:
            while True:
                new_messages = self.get_new_messages()

                if new_messages:
                    for msg in new_messages:
                        formatted = self.format_message(msg)
                        if formatted:  # Only display if not filtered
                            print(formatted)

                check_count += 1
                if check_count % 30 == 0:
                    print(f"⏰ [Status] Checks: {check_count}, Displayed: {len(self.displayed_messages)}")

                time.sleep(2)

        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped")
            print(f"Total messages displayed: {len(self.displayed_messages)}")

def main():
    monitor = SafeMonitor()
    monitor.run()

if __name__ == "__main__":
    main()