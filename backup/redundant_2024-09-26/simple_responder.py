#!/usr/bin/env python3
"""
Simple auto-responder for testing
간단한 자동 응답기 테스트
"""

import sqlite3
import time
from pathlib import Path

def simple_responder(instance_id):
    """Simple responder for one instance"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"
    last_check = time.time()

    print(f"🚀 Starting responder for {instance_id}")

    while True:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check for new messages
            cursor.execute("""
                SELECT from_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND timestamp > datetime(?, 'unixepoch')
                ORDER BY timestamp ASC
            """, (instance_id, last_check))

            messages = cursor.fetchall()

            if messages:
                print(f"📨 {instance_id} received {len(messages)} messages")
                last_check = time.time()

                for msg in messages:
                    from_id = msg[0]
                    content = msg[1]

                    # Skip own messages
                    if from_id == instance_id:
                        continue

                    print(f"  From {from_id}: {content[:50]}...")

                    # Send simple response
                    response = f"Hello {from_id}! This is {instance_id}. I received your message."

                    cursor.execute("""
                        INSERT INTO messages (from_id, to_id, content, timestamp)
                        VALUES (?, ?, ?, datetime('now'))
                    """, (instance_id, from_id, response))

                    conn.commit()
                    print(f"  ↩️ Sent response to {from_id}")

            conn.close()
            time.sleep(1)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    import sys
    instance = sys.argv[1] if len(sys.argv) > 1 else "gemini"
    simple_responder(instance)