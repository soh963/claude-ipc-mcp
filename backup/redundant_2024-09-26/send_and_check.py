#!/usr/bin/env python3
"""
Send messages to all instances and check responses
모든 인스턴스에게 메시지 보내고 응답 확인
"""

import sqlite3
import time
from pathlib import Path
from datetime import datetime
import sys
import os

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

def send_and_check():
    """Send messages to all instances and check responses"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # All target instances
    instances = ['gemini', 'codex', 'lm', 'claude']
    sender = 'claude'

    print("=" * 70)
    print("🚀 모든 인스턴스에게 메시지 전송 및 응답 확인")
    print("=" * 70)
    print(f"발신자: {sender}")
    print(f"수신자: {', '.join(instances)}")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)

    # Track sent times
    sent_times = {}

    # 1. Send messages to all instances
    print("\n📤 메시지 전송:")
    for target in instances:
        if target == sender:  # Skip self
            continue

        message = f"안녕하세요 {target}님! 시스템 테스트입니다. 현재 시간: {datetime.now().strftime('%H:%M:%S')}. 응답 부탁드립니다."

        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, (sender, target, message))

        sent_times[target] = time.time()
        print(f"  ✉️ {sender} → {target}: 메시지 전송 완료")

    conn.commit()

    # 2. Wait for responses
    print("\n⏳ 응답 대기중... (5초)")
    for i in range(5, 0, -1):
        print(f"  {i}초...", end="\r")
        time.sleep(1)
    print("                    ")

    # 3. Check responses
    print("\n📊 응답 확인 결과:")
    print("-" * 70)

    response_summary = {
        "responded": [],
        "no_response": [],
        "total_sent": len(sent_times)
    }

    for instance in sent_times.keys():
        # Check for response from this instance
        cursor.execute("""
            SELECT content, timestamp FROM messages
            WHERE from_id = ? AND to_id = ?
            AND timestamp > datetime(?, 'unixepoch')
            ORDER BY timestamp DESC LIMIT 1
        """, (instance, sender, sent_times[instance]))

        result = cursor.fetchone()

        if result:
            response_time = time.time() - sent_times[instance]
            print(f"✅ {instance}:")
            print(f"   응답: {result[0][:60]}...")
            print(f"   응답 시간: {response_time:.2f}초")
            print(f"   타임스탬프: {result[1]}")
            response_summary["responded"].append(instance)
        else:
            print(f"❌ {instance}:")
            print(f"   응답 없음 (5초 대기)")
            response_summary["no_response"].append(instance)

    # 4. Show summary
    print("\n" + "=" * 70)
    print("📈 요약:")
    print("-" * 70)
    print(f"총 전송: {response_summary['total_sent']}개")
    print(f"응답 받음: {len(response_summary['responded'])}개 ({', '.join(response_summary['responded']) if response_summary['responded'] else '없음'})")
    print(f"응답 없음: {len(response_summary['no_response'])}개 ({', '.join(response_summary['no_response']) if response_summary['no_response'] else '없음'})")

    # 5. Check if auto-responders are running
    print("\n🔍 추가 진단:")
    print("-" * 70)

    # Check message activity in last hour
    for instance in instances:
        if instance == sender:
            continue

        cursor.execute("""
            SELECT COUNT(*) FROM messages
            WHERE from_id = ?
            AND timestamp > datetime('now', '-1 hour')
        """, (instance,))

        count = cursor.fetchone()[0]

        if count > 0:
            print(f"📊 {instance}: 최근 1시간 내 {count}개 메시지 송신 (활동 중)")
        else:
            print(f"⚠️ {instance}: 최근 1시간 내 송신 없음 (비활동)")

    # 6. Check all messages in database
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    print(f"\n💾 데이터베이스 총 메시지 수: {total_messages}개")

    conn.close()

    print("\n" + "=" * 70)
    if len(response_summary["responded"]) == response_summary["total_sent"]:
        print("✅ 모든 인스턴스가 정상적으로 응답했습니다!")
    else:
        print("⚠️ 일부 인스턴스가 응답하지 않았습니다.")
        print("해결 방법:")
        print("1. 각 인스턴스에서 auto-responder 실행 확인")
        print("2. python optimized_auto_responder.py 실행")
        print("3. start_simple_responders.bat 실행")

if __name__ == "__main__":
    send_and_check()