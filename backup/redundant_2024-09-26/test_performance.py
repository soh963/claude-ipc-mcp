#!/usr/bin/env python3
"""
Performance test for optimized auto-responder
성능 최적화 테스트
"""

import time
import sqlite3
from pathlib import Path
import sys
import os

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def test_response_time():
    """Test message response time"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🧪 Performance Test Starting...")
    print("-"*50)

    # Send test message to each instance
    test_instances = ['claude', 'gemini', 'codex', 'lm']

    for target in test_instances:
        # Send message
        timestamp = time.time()
        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, ('test_client', target, f'Performance test message to {target}'))
        conn.commit()

        print(f"📤 Sent to {target}")

        # Wait for response (max 3 seconds)
        start_time = time.time()
        response_found = False

        while time.time() - start_time < 3:
            cursor.execute("""
                SELECT content FROM messages
                WHERE from_id = ? AND to_id = 'test_client'
                AND timestamp > datetime(?, 'unixepoch')
                ORDER BY timestamp DESC LIMIT 1
            """, (target, timestamp))

            result = cursor.fetchone()
            if result:
                response_time = time.time() - start_time
                print(f"   ✅ {target} responded in {response_time:.2f}s")
                response_found = True
                break

            time.sleep(0.1)

        if not response_found:
            print(f"   ⚠️ {target} - No response in 3s")

    print("-"*50)
    print("✨ Performance test completed!")

    # Check if all instances are registered
    cursor.execute("SELECT DISTINCT from_id FROM messages WHERE timestamp > datetime('now', '-1 hour')")
    active_instances = [row[0] for row in cursor.fetchall()]

    print(f"\n📊 Active instances in last hour: {', '.join(active_instances)}")

    # Count messages per instance
    for instance in test_instances:
        cursor.execute("""
            SELECT COUNT(*) FROM messages
            WHERE (from_id = ? OR to_id = ?)
            AND timestamp > datetime('now', '-1 hour')
        """, (instance, instance))
        count = cursor.fetchone()[0]
        print(f"   {instance}: {count} messages")

    conn.close()

if __name__ == "__main__":
    test_response_time()