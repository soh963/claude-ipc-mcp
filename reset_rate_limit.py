#!/usr/bin/env python3
"""Rate limit 초기화 스크립트"""
import sqlite3
from pathlib import Path
from datetime import datetime

def reset_rate_limits():
    """데이터베이스에서 rate limit 정보 초기화"""
    db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # rate_limits 테이블이 있는지 확인
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='rate_limits'
    """)

    if cursor.fetchone():
        # rate_limits 테이블 비우기
        cursor.execute("DELETE FROM rate_limits")
        conn.commit()
        print("✅ Rate limits cleared from database")
    else:
        print("ℹ️ No rate_limits table found")

    # 메모리 기반 rate limit을 위해 서버 재시작 권장
    print("\n⚠️ Note: If rate limiting persists, the server may be using memory-based limits.")
    print("   Try restarting the IPC server:")
    print("   1. taskkill /F /IM python.exe")
    print("   2. python src/claude_ipc_server.py")

    conn.close()

if __name__ == "__main__":
    reset_rate_limits()