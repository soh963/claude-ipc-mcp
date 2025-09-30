#!/usr/bin/env python
"""
Monitor messages for a specific instance without causing loops
"""
import sqlite3
import time
from pathlib import Path
import argparse


class InstanceMonitor:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_check_id = 0
        self.seen_messages = set()

    def get_messages_for_instance(self):
        """Get messages for this instance only"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get messages TO this instance
            cursor.execute(
                """
                SELECT id, from_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND id > ?
                ORDER BY id
                LIMIT 20
            """,
                (self.instance_id, self.last_check_id),
            )

            incoming = cursor.fetchall()

            # Get messages FROM this instance
            cursor.execute(
                """
                SELECT id, to_id, content, timestamp
                FROM messages
                WHERE from_id = ? AND id > ?
                ORDER BY id
                LIMIT 20
            """,
                (self.instance_id, self.last_check_id),
            )

            outgoing = cursor.fetchall()
            conn.close()

            return incoming, outgoing

        except Exception as e:
            print(f"Error: {e}")
            return [], []

    def display_message(self, msg_type, msg_data):
        """Display a message with formatting"""
        if msg_type == "incoming":
            msg_id, from_id, content, timestamp = msg_data
            direction = f"{from_id} → {self.instance_id}"
        else:
            msg_id, to_id, content, timestamp = msg_data
            direction = f"{self.instance_id} → {to_id}"

        # Skip if we've seen this message
        if msg_id in self.seen_messages:
            return False

        # Filter out spam/loop messages
        if content.count("안녕하세요") > 2:
            return False
        if "Auto-Responder" in content and msg_id in self.seen_messages:
            return False

        # Truncate long content
        if len(content) > 80:
            content = content[:80] + "..."

        print(f"[{timestamp[:19]}] {direction}")
        print(f"  {content}")
        print()

        self.seen_messages.add(msg_id)
        self.last_check_id = max(self.last_check_id, msg_id)
        return True

    def run(self):
        """Run the monitor"""
        print(f"📊 Monitoring: {self.instance_id}")
        print("=" * 60)
        print("Press Ctrl+C to stop")
        print()

        # Get initial position
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM messages")
            result = cursor.fetchone()
            if result and result[0]:
                self.last_check_id = result[0]
            conn.close()
        except Exception:
            pass

        message_count = 0
        check_count = 0

        try:
            while True:
                incoming, outgoing = self.get_messages_for_instance()

                # Display incoming messages
                for msg in incoming:
                    if self.display_message("incoming", msg):
                        message_count += 1

                # Display outgoing messages
                for msg in outgoing:
                    if self.display_message("outgoing", msg):
                        message_count += 1

                check_count += 1
                if check_count % 30 == 0 and message_count > 0:
                    print(f"[Stats] Checks: {check_count}, Messages: {message_count}")

                time.sleep(2)

        except KeyboardInterrupt:
            print(f"\n✅ Stopped monitoring {self.instance_id}")
            print(f"Total messages: {message_count}")


def main():
    parser = argparse.ArgumentParser(description="Monitor IPC messages for an instance")
    parser.add_argument("instance_id", help="Instance ID to monitor")
    args = parser.parse_args()

    monitor = InstanceMonitor(args.instance_id)
    monitor.run()


if __name__ == "__main__":
    main()
