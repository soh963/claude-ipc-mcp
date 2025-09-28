#!/usr/bin/env python3
"""Check messages for AI instances (codex and lm)"""
import sqlite3
from pathlib import Path
from datetime import datetime

def check_messages():
    """Check messages for codex and lm instances"""
    db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n=== Unread messages for codex ===")
    cursor.execute("""
        SELECT from_id, content, timestamp, read_flag
        FROM messages
        WHERE to_id = 'codex' AND read_flag = 0
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    codex_msgs = cursor.fetchall()
    if codex_msgs:
        for msg in codex_msgs:
            print(f"From: {msg[0]}")
            print(f"Content: {msg[1][:100]}")
            print(f"Time: {msg[2]}")
            print(f"Read: {'Yes' if msg[3] else 'No'}")
            print("-" * 40)
    else:
        print("No unread messages for codex")

    print("\n=== Unread messages for lm ===")
    cursor.execute("""
        SELECT from_id, content, timestamp, read_flag
        FROM messages
        WHERE to_id = 'lm' AND read_flag = 0
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    lm_msgs = cursor.fetchall()
    if lm_msgs:
        for msg in lm_msgs:
            print(f"From: {msg[0]}")
            print(f"Content: {msg[1][:100]}")
            print(f"Time: {msg[2]}")
            print(f"Read: {'Yes' if msg[3] else 'No'}")
            print("-" * 40)
    else:
        print("No unread messages for lm")

    # Check for any responses FROM codex or lm
    print("\n=== Messages FROM codex ===")
    cursor.execute("""
        SELECT to_id, content, timestamp
        FROM messages
        WHERE from_id = 'codex'
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    from_codex = cursor.fetchall()
    if from_codex:
        for msg in from_codex:
            print(f"To: {msg[0]}")
            print(f"Content: {msg[1][:100]}")
            print(f"Time: {msg[2]}")
            print("-" * 40)
    else:
        print("No messages from codex")

    print("\n=== Messages FROM lm ===")
    cursor.execute("""
        SELECT to_id, content, timestamp
        FROM messages
        WHERE from_id = 'lm'
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    from_lm = cursor.fetchall()
    if from_lm:
        for msg in from_lm:
            print(f"To: {msg[0]}")
            print(f"Content: {msg[1][:100]}")
            print(f"Time: {msg[2]}")
            print("-" * 40)
    else:
        print("No messages from lm")

    conn.close()

if __name__ == "__main__":
    check_messages()