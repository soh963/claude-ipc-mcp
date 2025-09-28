#!/usr/bin/env python3
"""
Simple auto-responder for testing real-time messaging
"""

import sqlite3
import time
import sys
from pathlib import Path

def check_and_respond(instance_id="claude"):
    """Check for new messages and send auto-response"""

    db_path = Path.home() / ".claude-ipc-data" / "messages.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get unread messages (last 10 seconds)
    cursor.execute("""
        SELECT from_id, content, timestamp
        FROM messages
        WHERE to_id = ?
        AND timestamp > datetime('now', '-10 seconds')
        ORDER BY timestamp DESC
        LIMIT 1
    """, (instance_id,))

    result = cursor.fetchone()

    if result:
        from_id, content, timestamp = result
        print(f"📨 New message from {from_id}: {content}")

        # Send auto-response
        response = f"[Auto-Reply] Message received at {timestamp}: '{content[:30]}...' Processing..."

        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, (instance_id, from_id, response))

        conn.commit()
        print(f"✅ Auto-response sent to {from_id}")
    else:
        print("No new messages")

    conn.close()

if __name__ == "__main__":
    instance_id = sys.argv[1] if len(sys.argv) > 1 else "claude"
    print(f"Checking messages for {instance_id}...")
    check_and_respond(instance_id)