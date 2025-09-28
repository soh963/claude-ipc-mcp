#!/usr/bin/env python3
"""
Clear all messages from IPC database
IPC 데이터베이스의 모든 메시지 초기화
"""

import sqlite3
from pathlib import Path
import sys
import os
from datetime import datetime

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def clear_all_messages():
    """Clear all messages from database"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count existing messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        count_before = cursor.fetchone()[0]
        print(f"📊 현재 메시지 수: {count_before}개")

        # Clear all messages
        cursor.execute("DELETE FROM messages")
        conn.commit()

        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM messages")
        count_after = cursor.fetchone()[0]

        print(f"🗑️ 삭제된 메시지: {count_before}개")
        print(f"✅ 남은 메시지: {count_after}개")

        # Add initial message
        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, ('system', 'all', '🎉 IPC 시스템이 초기화되었습니다. 새로운 시작!'))

        conn.commit()
        conn.close()

        print("\n✨ 데이터베이스 초기화 완료!")
        print("📝 시스템 초기 메시지가 추가되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def clear_recent_messages(hours=1):
    """Clear messages from last N hours"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Delete recent messages
        cursor.execute("""
            DELETE FROM messages
            WHERE timestamp > datetime('now', ? || ' hours')
        """, (-hours,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"🗑️ 최근 {hours}시간 메시지 {deleted}개 삭제됨")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧹 IPC 메시지 데이터베이스 초기화")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "--recent":
        # Clear only recent messages
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        clear_recent_messages(hours)
    else:
        # Clear all messages
        response = input("\n⚠️ 모든 메시지를 삭제하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            clear_all_messages()
        else:
            print("❌ 취소되었습니다.")