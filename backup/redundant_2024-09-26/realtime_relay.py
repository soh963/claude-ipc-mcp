#!/usr/bin/env python3
"""
실시간 메시지 릴레이 시스템
모든 인스턴스 간 메시지를 즉각 중계하고 모니터링
"""

import sqlite3
import time
import threading
from datetime import datetime
from pathlib import Path
import json

class RealtimeRelay:
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'ipc_messages.db'
        self.instances = ['claude', 'gemini', 'codex', 'lm']
        self.running = True
        self.last_message_id = 0

    def init_database(self):
        """데이터베이스 연결 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 메시지 테이블이 없으면 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                from_instance TEXT,
                to_instance TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                relay_count INTEGER DEFAULT 0
            )
        ''')

        # 릴레이 로그 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relay_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                timestamp TEXT,
                action TEXT,
                details TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def check_new_messages(self):
        """새로운 메시지 확인 및 릴레이"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 새 메시지 조회
        cursor.execute('''
            SELECT id, from_instance, to_instance, content, timestamp
            FROM messages
            WHERE id > ? AND status = 'pending'
            ORDER BY id ASC
        ''', (self.last_message_id,))

        new_messages = cursor.fetchall()

        for msg in new_messages:
            msg_id, from_inst, to_inst, content, timestamp = msg

            # 브로드캐스트 메시지인 경우
            if to_inst == 'all':
                self.relay_broadcast(msg_id, from_inst, content, timestamp, cursor)
            else:
                # 일반 메시지 릴레이 확인
                self.ensure_delivery(msg_id, from_inst, to_inst, content, timestamp, cursor)

            self.last_message_id = msg_id

        conn.commit()
        conn.close()

    def relay_broadcast(self, msg_id, from_inst, content, timestamp, cursor):
        """브로드캐스트 메시지를 모든 인스턴스에게 릴레이"""
        for instance in self.instances:
            if instance != from_inst:
                # 각 인스턴스에게 개별 메시지 생성
                cursor.execute('''
                    INSERT INTO messages (timestamp, from_instance, to_instance, content, status)
                    VALUES (?, ?, ?, ?, 'relayed')
                ''', (timestamp, from_inst, instance, content))

                print(f"📡 Relay: {from_inst} → {instance}: {content[:50]}...")

        # 원본 메시지 상태 업데이트
        cursor.execute('''
            UPDATE messages SET status = 'delivered', relay_count = ?
            WHERE id = ?
        ''', (len(self.instances) - 1, msg_id))

        # 릴레이 로그 기록
        self.log_relay(msg_id, 'broadcast', f"Relayed to {len(self.instances)-1} instances", cursor)

    def ensure_delivery(self, msg_id, from_inst, to_inst, content, timestamp, cursor):
        """메시지 전달 보장"""
        # 메시지 상태 확인
        cursor.execute('''
            SELECT COUNT(*) FROM instances WHERE id = ? AND last_check > datetime('now', '-30 seconds')
        ''', (to_inst,))

        result = cursor.fetchone()
        is_online = result[0] > 0 if result else False

        if is_online:
            # 온라인 상태면 즉시 전달 마크
            cursor.execute('''
                UPDATE messages SET status = 'delivered' WHERE id = ?
            ''', (msg_id,))
            print(f"✅ Delivered: {from_inst} → {to_inst}: {content[:50]}...")
        else:
            # 오프라인이면 대기 상태로
            cursor.execute('''
                UPDATE messages SET status = 'queued' WHERE id = ?
            ''', (msg_id,))
            print(f"⏳ Queued: {from_inst} → {to_inst} (offline)")

        # 릴레이 로그 기록
        status = 'delivered' if is_online else 'queued'
        self.log_relay(msg_id, status, f"{to_inst} {'online' if is_online else 'offline'}", cursor)

    def log_relay(self, msg_id, action, details, cursor):
        """릴레이 작업 로그 기록"""
        cursor.execute('''
            INSERT INTO relay_log (message_id, timestamp, action, details)
            VALUES (?, datetime('now'), ?, ?)
        ''', (msg_id, action, details))

    def monitor_loop(self):
        """메인 모니터링 루프"""
        print("🚀 Realtime Relay System Started")
        print("=" * 50)

        while self.running:
            try:
                self.check_new_messages()
                time.sleep(0.5)  # 500ms 간격으로 체크
            except KeyboardInterrupt:
                self.running = False
                print("\n🛑 Relay System Stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(2)

    def get_statistics(self):
        """릴레이 통계 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 전체 메시지 수
        cursor.execute("SELECT COUNT(*) FROM messages")
        total = cursor.fetchone()[0]

        # 상태별 메시지 수
        cursor.execute('''
            SELECT status, COUNT(*) FROM messages
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())

        # 인스턴스별 송신/수신 수
        cursor.execute('''
            SELECT from_instance, COUNT(*) FROM messages
            GROUP BY from_instance
        ''')
        sent_counts = dict(cursor.fetchall())

        cursor.execute('''
            SELECT to_instance, COUNT(*) FROM messages
            WHERE to_instance != 'all'
            GROUP BY to_instance
        ''')
        received_counts = dict(cursor.fetchall())

        conn.close()

        return {
            'total': total,
            'by_status': status_counts,
            'sent': sent_counts,
            'received': received_counts
        }

    def display_stats(self):
        """통계 표시"""
        stats = self.get_statistics()

        print("\n📊 Relay Statistics")
        print("=" * 50)
        print(f"Total Messages: {stats['total']}")

        print("\nBy Status:")
        for status, count in stats['by_status'].items():
            print(f"  {status}: {count}")

        print("\nMessages Sent:")
        for inst, count in stats['sent'].items():
            print(f"  {inst}: {count}")

        print("\nMessages Received:")
        for inst, count in stats['received'].items():
            print(f"  {inst}: {count}")
        print("=" * 50)

if __name__ == "__main__":
    relay = RealtimeRelay()
    relay.init_database()

    # 통계 표시 스레드
    def show_stats():
        while relay.running:
            time.sleep(30)  # 30초마다 통계 표시
            relay.display_stats()

    stats_thread = threading.Thread(target=show_stats, daemon=True)
    stats_thread.start()

    # 메인 릴레이 루프 실행
    relay.monitor_loop()