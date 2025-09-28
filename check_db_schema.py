#!/usr/bin/env python3
"""
데이터베이스 스키마 확인 스크립트
"""
import sqlite3
from pathlib import Path

db_path = Path.home() / '.claude-ipc-data' / 'messages.db'

if not db_path.exists():
    print(f"❌ 데이터베이스 파일 없음: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 테이블 목록
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("📋 테이블 목록:")
    for table in tables:
        print(f"  - {table[0]}")

    # instances 테이블 스키마
    print("\n🔍 instances 테이블 스키마:")
    cursor.execute("PRAGMA table_info(instances)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # 실제 데이터 확인
    print("\n📊 instances 테이블 데이터 (최대 5개):")
    try:
        cursor.execute("SELECT * FROM instances LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row}")
    except Exception as e:
        print(f"  오류: {e}")

    conn.close()