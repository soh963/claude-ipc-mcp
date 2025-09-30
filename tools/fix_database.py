#!/usr/bin/env python3
"""
데이터베이스 스키마 수정 스크립트
is_read 컬럼 추가
"""

import sqlite3
from pathlib import Path


def fix_database():
    """데이터베이스 스키마 수정"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 현재 스키마 확인
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # is_read 컬럼이 없으면 추가
        if "is_read" not in column_names:
            print("📊 is_read 컬럼 추가 중...")
            cursor.execute(
                """
                ALTER TABLE messages
                ADD COLUMN is_read INTEGER DEFAULT 0
            """
            )
            conn.commit()
            print("✅ is_read 컬럼이 추가되었습니다.")
        else:
            print("✅ is_read 컬럼이 이미 존재합니다.")

        conn.close()

    except Exception as e:
        print(f"❌ 데이터베이스 수정 실패: {e}")


if __name__ == "__main__":
    fix_database()
