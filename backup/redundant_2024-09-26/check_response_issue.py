#!/usr/bin/env python3
"""
Check why instances are not responding
인스턴스가 응답하지 않는 이유 확인
"""

import sqlite3
from pathlib import Path
import sys
import os
from datetime import datetime, timedelta

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def check_response_issue():
    """Check message status and response patterns"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 메시지 응답 문제 진단")
    print("=" * 60)

    # 1. Check recent messages
    print("\n1️⃣ 최근 10개 메시지:")
    print("-" * 60)
    cursor.execute("""
        SELECT from_id, to_id, content, timestamp
        FROM messages
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    messages = cursor.fetchall()
    for msg in messages:
        print(f"[{msg[3]}]")
        print(f"  {msg[0]} → {msg[1]}: {msg[2][:60]}...")

        # Check if there's a response
        cursor.execute("""
            SELECT COUNT(*) FROM messages
            WHERE from_id = ? AND to_id = ?
            AND timestamp > ?
        """, (msg[1], msg[0], msg[3]))

        response_count = cursor.fetchone()[0]
        if response_count > 0:
            print(f"  ✅ 응답 있음 ({response_count}개)")
        else:
            print(f"  ❌ 응답 없음")

    # 2. Check if instances are sending messages at all
    print("\n2️⃣ 인스턴스별 송신 메시지 수 (최근 1시간):")
    print("-" * 60)

    instances = ['claude', 'gemini', 'codex', 'lm']
    for instance in instances:
        cursor.execute("""
            SELECT COUNT(*) FROM messages
            WHERE from_id = ?
            AND timestamp > datetime('now', '-1 hour')
        """, (instance,))

        count = cursor.fetchone()[0]
        print(f"  {instance}: {count}개 메시지 송신")

    # 3. Check message patterns
    print("\n3️⃣ 메시지 패턴 분석:")
    print("-" * 60)

    # Check for auto-response patterns
    cursor.execute("""
        SELECT content FROM messages
        WHERE content LIKE '%received%'
        OR content LIKE '%processing%'
        OR content LIKE '%ready%'
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    auto_responses = cursor.fetchall()
    if auto_responses:
        print("  자동 응답 패턴 발견:")
        for resp in auto_responses:
            print(f"    - {resp[0][:60]}...")
    else:
        print("  ❌ 자동 응답 패턴이 없음")

    # 4. Check for system messages
    print("\n4️⃣ 시스템 메시지 확인:")
    print("-" * 60)
    cursor.execute("""
        SELECT from_id, content FROM messages
        WHERE from_id = 'system'
        OR from_id = 'test_client'
        OR from_id = 'test_instance'
    """)

    system_msgs = cursor.fetchall()
    if system_msgs:
        print(f"  시스템 메시지 {len(system_msgs)}개 발견")
        for msg in system_msgs:
            print(f"    {msg[0]}: {msg[1][:50]}...")
    else:
        print("  시스템 메시지 없음")

    conn.close()

    print("\n" + "=" * 60)
    print("📋 진단 결과:")
    print("-" * 60)
    print("가능한 원인:")
    print("1. Auto-responder가 실행되지 않음")
    print("2. 메시지 패턴이 응답 조건과 일치하지 않음")
    print("3. Instance ID가 정확하지 않음")
    print("4. 데이터베이스 연결 문제")
    print("\n권장 조치:")
    print("1. python start_all_auto_responders.py 실행")
    print("2. python optimized_auto_responder.py 실행")
    print("3. 각 인스턴스의 AI CLI에서 초기화 확인")

if __name__ == "__main__":
    check_response_issue()