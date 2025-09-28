#!/usr/bin/env python3
"""
Fixed monitor that uses correct database path
"""
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

def monitor_messages(instance_id):
    """Monitor messages for specific instance"""
    # Use the correct database path
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    print(f"🚀 {instance_id.upper()} Monitor")
    print(f"📁 Database: {db_path}")
    print("="*60)

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("Creating database...")
        db_path.parent.mkdir(parents=True, exist_ok=True)

    last_id = 0
    message_count = 0

    while True:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check for new messages
            cursor.execute('''
                SELECT id, timestamp, from_id, to_id, content
                FROM messages
                WHERE (to_id = ? OR from_id = ? OR to_id = 'all')
                AND id > ?
                ORDER BY id ASC
            ''', (instance_id, instance_id, last_id))

            new_messages = cursor.fetchall()

            if new_messages:
                for msg in new_messages:
                    msg_id, timestamp, from_id, to_id, content = msg
                    message_count += 1

                    # Clear screen for new messages
                    print("\033[2J\033[H", end="")  # Clear screen
                    print(f"🚀 {instance_id.upper()} Monitor")
                    print("="*60)

                    # Determine message direction
                    if from_id == instance_id:
                        print(f"📤 SENT TO: {to_id}")
                    elif to_id == instance_id:
                        print(f"📥 RECEIVED FROM: {from_id}")
                    elif to_id == 'all':
                        print(f"📢 BROADCAST FROM: {from_id}")

                    print(f"⏰ Time: {timestamp}")
                    print("-"*60)
                    print(f"💬 Message:")
                    print(f"   {content}")
                    print("="*60)
                    print(f"📊 Total messages: {message_count}")

                    last_id = msg_id
            else:
                # Show waiting status
                print(f"\r⏳ Waiting for messages... (Total: {message_count}) [{datetime.now().strftime('%H:%M:%S')}]", end="", flush=True)

            conn.close()
            time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n🔕 Monitor stopped")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fixed_monitor.py [instance_id]")
        print("Example: python fixed_monitor.py claude")
        sys.exit(1)

    instance_id = sys.argv[1].lower()
    monitor_messages(instance_id)