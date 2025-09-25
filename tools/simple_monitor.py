#!/usr/bin/env python3
"""
간단한 모니터 테스트 - 데이터베이스를 직접 읽어서 출력
"""
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

def monitor_simple(instance_id):
    """직접 데이터베이스를 읽어서 메시지 표시"""
    db_path = Path(__file__).parent.parent / 'ipc_messages.db'

    print(f"🚀 {instance_id.upper()} Monitor Started")
    print(f"📁 DB Path: {db_path}")
    print("="*50)

    last_id = 0

    while True:
        try:
            # 데이터베이스 직접 연결
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 새 메시지 조회
            cursor.execute('''
                SELECT id, timestamp, from_instance, to_instance, content
                FROM messages
                WHERE (to_instance = ? OR from_instance = ? OR to_instance = 'all')
                AND id > ?
                ORDER BY id ASC
            ''', (instance_id, instance_id, last_id))

            new_messages = cursor.fetchall()

            if new_messages:
                print(f"\n📬 새 메시지 {len(new_messages)}개:")
                for msg in new_messages:
                    msg_id, timestamp, from_inst, to_inst, content = msg

                    # 방향 결정
                    if from_inst == instance_id:
                        direction = f"📤 [{instance_id} → {to_inst}]"
                    elif to_inst == instance_id:
                        direction = f"📥 [{from_inst} → {instance_id}]"
                    else:
                        direction = f"📢 [Broadcast from {from_inst}]"

                    print(f"\n{direction}")
                    print(f"⏰ {timestamp}")
                    print(f"💬 {content}")
                    print("-"*50)

                    last_id = msg_id

            # 상태 표시
            cursor.execute('SELECT COUNT(*) FROM messages')
            total = cursor.fetchone()[0]

            print(f"\r💾 Total: {total} | ⏰ {datetime.now().strftime('%H:%M:%S')} | 👀 Watching...", end='', flush=True)

            conn.close()
            time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n🔕 모니터링 종료")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_monitor.py [instance_id]")
        sys.exit(1)

    instance_id = sys.argv[1].lower()
    monitor_simple(instance_id)