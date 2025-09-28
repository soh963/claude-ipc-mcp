#!/usr/bin/env python3
"""
Fresh start test - Send initial greeting
새로운 시작 테스트
"""

import sqlite3
from pathlib import Path
import sys
import os
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def send_fresh_greeting():
    """Send fresh greeting to all instances"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    instances = ['claude', 'gemini', 'codex', 'lm']

    print("🌟 새로운 시작!")
    print("=" * 50)

    # Send greeting from claude to all
    for target in instances:
        if target != 'claude':
            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """, ('claude', target, f'🎉 안녕하세요 {target}님! 시스템이 초기화되고 새롭게 시작합니다. 성능이 4배 향상되었습니다!'))

            print(f"📤 Claude → {target}: 인사 메시지 전송")

    conn.commit()

    # Check current message count
    cursor.execute("SELECT COUNT(*) FROM messages")
    total = cursor.fetchone()[0]

    print("=" * 50)
    print(f"✅ 총 {total}개 메시지 (깨끗한 상태)")

    # Show all messages
    cursor.execute("""
        SELECT from_id, to_id, content, timestamp
        FROM messages
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    print("\n📊 현재 메시지:")
    print("-" * 50)
    for row in cursor.fetchall():
        print(f"{row[0]} → {row[1]}: {row[2][:50]}...")
        print(f"   시간: {row[3]}")

    conn.close()

if __name__ == "__main__":
    send_fresh_greeting()