#!/usr/bin/env python3
"""직접 데이터베이스에서 메시지 확인"""
import sqlite3
from pathlib import Path
from datetime import datetime

def check_messages():
    db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n=== Claude의 받은 메시지 (최근 10개) ===")
    cursor.execute("""
        SELECT from_id, content, timestamp, read_flag
        FROM messages
        WHERE to_id = 'claude'
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    messages = cursor.fetchall()
    if messages:
        for from_id, content, timestamp, read_flag in messages:
            status = "읽음" if read_flag else "읽지 않음"
            print(f"[{timestamp}] {from_id}: {content[:100]} ({status})")
    else:
        print("받은 메시지가 없습니다.")

    print("\n=== Claude가 보낸 메시지 (최근 5개) ===")
    cursor.execute("""
        SELECT to_id, content, timestamp
        FROM messages
        WHERE from_id = 'claude'
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    messages = cursor.fetchall()
    if messages:
        for to_id, content, timestamp in messages:
            print(f"[{timestamp}] → {to_id}: {content[:100]}")
    else:
        print("보낸 메시지가 없습니다.")

    print("\n=== 현재 활성 세션 ===")
    cursor.execute("""
        SELECT instance_id, created_at, expires_at
        FROM sessions
        WHERE expires_at > datetime('now')
        ORDER BY created_at DESC
    """)

    sessions = cursor.fetchall()
    if sessions:
        for instance_id, created_at, expires_at in sessions:
            print(f"{instance_id}: 생성 {created_at}, 만료 {expires_at}")
    else:
        print("활성 세션이 없습니다.")

    conn.close()

if __name__ == "__main__":
    check_messages()