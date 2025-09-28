#!/usr/bin/env python3
"""Rate limit 우회하여 직접 메시지 전송"""
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

def send_message_directly(from_id, to_id, message):
    """데이터베이스에 직접 메시지 삽입"""
    db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 메시지 테이블 구조 확인
    cursor.execute("PRAGMA table_info(messages)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print(f"Message table columns: {column_names}")

    # 메시지 삽입
    timestamp = datetime.now().isoformat()

    try:
        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp, read_flag)
            VALUES (?, ?, ?, ?, 0)
        """, (from_id, to_id, message, timestamp))

        conn.commit()
        print(f"✅ Message sent from {from_id} to {to_id}")
        print(f"   Content: {message[:100]}...")

        # 확인
        cursor.execute("""
            SELECT * FROM messages
            WHERE from_id = ? AND to_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (from_id, to_id))

        result = cursor.fetchone()
        if result:
            print(f"   Verified in database: {result}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python direct_send.py <from_id> <to_id> <message>")
        sys.exit(1)

    from_id = sys.argv[1]
    to_id = sys.argv[2]
    message = " ".join(sys.argv[3:])

    send_message_directly(from_id, to_id, message)