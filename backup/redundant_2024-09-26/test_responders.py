#!/usr/bin/env python3
"""
Test if responders are working
응답기 작동 테스트
"""

import sqlite3
import time
from pathlib import Path

def test_responders():
    """Test auto-responders"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    instances = ['gemini', 'codex', 'lm']

    print("🧪 Auto-Responder 테스트")
    print("=" * 50)

    # Send test messages
    for target in instances:
        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, ('claude', target, f'테스트: 응답해주세요 {target}님!'))
        print(f"📤 Claude → {target}: 테스트 메시지 전송")

    conn.commit()

    # Wait for responses
    print("\n⏳ 응답 대기 중... (3초)")
    time.sleep(3)

    # Check responses
    print("\n📊 응답 확인:")
    print("-" * 50)

    for instance in instances:
        cursor.execute("""
            SELECT content, timestamp FROM messages
            WHERE from_id = ? AND to_id = 'claude'
            AND timestamp > datetime('now', '-10 seconds')
            ORDER BY timestamp DESC LIMIT 1
        """, (instance,))

        result = cursor.fetchone()
        if result:
            print(f"✅ {instance}: {result[0][:50]}...")
        else:
            print(f"❌ {instance}: 응답 없음")

    conn.close()

if __name__ == "__main__":
    test_responders()