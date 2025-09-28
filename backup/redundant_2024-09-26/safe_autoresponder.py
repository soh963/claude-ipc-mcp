#!/usr/bin/env python3
"""
안전한 자동응답 시스템 - 무한루프 방지 및 중복 처리 방지
"""

import asyncio
import sqlite3
import time
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set, Dict, List, Optional

class SafeAutoResponder:
    """안전한 자동응답 시스템"""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.running = False

        # 중복 방지를 위한 추적
        self.processed_message_ids = set()  # 처리한 메시지 ID들
        self.last_response_to = {}  # 마지막으로 응답한 내용 추적
        self.response_cooldown = {}  # 응답 쿨다운 (같은 사람에게 5초 간격)

        # 자동응답 감지 패턴 (이런 패턴이 있으면 응답하지 않음)
        self.auto_response_patterns = [
            "자동 응답",
            "auto-responder",
            "responding!",
            "ready for",
            "here!",
            "mode activated",
            "시스템입니다",
            "I received your",
            "Processing",
            "👋 안녕하세요",
            "[claude]",
            "[gemini]",
            "[codex]",
            "[lm]",
        ]

    async def start(self):
        """자동응답 시작"""
        self.running = True
        print(f"\n{'='*60}")
        print(f"🛡️ SAFE Auto-Responder for [{self.instance_id}]")
        print(f"{'='*60}")
        print(f"✅ Instance: {self.instance_id}")
        print(f"✅ Infinite loop prevention: ENABLED")
        print(f"✅ Duplicate prevention: ENABLED")
        print(f"✅ Cooldown: 5 seconds per sender")
        print(f"{'='*60}\n")

        # 시작시 모든 기존 메시지를 읽음 처리
        self.mark_all_as_read()

        while self.running:
            try:
                # 새 메시지 확인 (read_flag = 0인 것만)
                new_messages = await self.check_new_messages()

                if new_messages:
                    print(f"\n🔍 Found {len(new_messages)} new messages")

                for msg in new_messages:
                    if self.should_respond(msg):
                        await self.process_message(msg)
                    else:
                        # 응답하지 않더라도 읽음 처리
                        self.mark_as_read(msg['id'])

                await asyncio.sleep(3)  # 3초마다 확인

            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(5)

    def mark_all_as_read(self):
        """시작시 모든 메시지를 읽음 처리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE messages
                SET read_flag = 1
                WHERE to_id = ?
            """, (self.instance_id,))

            conn.commit()
            conn.close()

            print(f"✅ Marked all existing messages as read")

        except Exception as e:
            print(f"⚠️ Could not mark messages as read: {e}")

    async def check_new_messages(self):
        """새 메시지 확인 (read_flag = 0)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # ROWID를 포함해서 가져오기 (고유 ID로 사용)
            cursor.execute("""
                SELECT rowid, from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND read_flag = 0
                ORDER BY timestamp ASC
                LIMIT 10
            """, (self.instance_id,))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row[0],  # rowid
                    'from_id': row[1],
                    'to_id': row[2],
                    'content': row[3],
                    'timestamp': row[4]
                })

            conn.close()
            return messages

        except Exception as e:
            print(f"DB Error: {e}")
            return []

    def should_respond(self, msg):
        """응답 여부 결정"""
        # 자기 자신의 메시지는 무시
        if msg['from_id'] == self.instance_id:
            self.mark_as_read(msg['id'])
            return False

        # 이미 처리한 메시지는 무시
        if msg['id'] in self.processed_message_ids:
            return False

        # 자동응답 패턴이 포함된 메시지는 무시
        content_lower = msg['content'].lower()
        for pattern in self.auto_response_patterns:
            if pattern.lower() in content_lower:
                print(f"   ⏭️ Skipping auto-response pattern from {msg['from_id']}")
                return False

        # 같은 사람에게 5초 이내 응답했으면 무시
        if msg['from_id'] in self.response_cooldown:
            if time.time() - self.response_cooldown[msg['from_id']] < 5:
                print(f"   ⏳ Cooldown active for {msg['from_id']}")
                return False

        # 빈 메시지는 무시
        if not msg['content'].strip():
            return False

        return True

    def mark_as_read(self, message_id):
        """메시지를 읽음 처리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE messages
                SET read_flag = 1
                WHERE rowid = ?
            """, (message_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Failed to mark as read: {e}")

    async def process_message(self, msg):
        """메시지 처리"""
        # 처리 기록
        self.processed_message_ids.add(msg['id'])

        # 읽음 처리
        self.mark_as_read(msg['id'])

        from_id = msg['from_id']
        content = msg['content'][:100]  # 처음 100자만 표시

        print(f"📨 [{self.instance_id}] From {from_id}: {content}...")

        # 응답 생성
        response = self.generate_simple_response(from_id, content)

        if response:
            # 응답 전송
            if await self.send_response(from_id, response):
                print(f"   ↩️ Sent response to {from_id}")
                # 쿨다운 기록
                self.response_cooldown[from_id] = time.time()
                self.last_response_to[from_id] = response

    def generate_simple_response(self, from_id, content):
        """간단한 응답 생성"""
        # 기본 인사 패턴
        if any(word in content.lower() for word in ['안녕', 'hello', 'hi']):
            return f"Hello {from_id}! This is {self.instance_id}. How can I help you?"

        # 질문인 경우
        if '?' in content:
            return f"{self.instance_id} received your question. Processing..."

        # 도움 요청
        if any(word in content.lower() for word in ['help', '도움', '도와']):
            return f"{self.instance_id} here to help! What do you need?"

        # 긴 메시지는 확인 응답
        if len(content) > 50:
            return f"{self.instance_id} received your message. Thank you!"

        # 기본적으로는 응답하지 않음 (스팸 방지)
        return None

    async def send_response(self, to_id, content):
        """응답 전송"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # read_flag를 0으로 설정해서 상대방이 읽을 수 있게 함
            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp, read_flag)
                VALUES (?, ?, ?, datetime('now'), 0)
            """, (self.instance_id, to_id, content))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Send error: {e}")
            return False

    def stop(self):
        """중지"""
        self.running = False
        print(f"🛑 [{self.instance_id}] Auto-responder stopped")


async def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python safe_autoresponder.py <instance_id>")
        print("Example: python safe_autoresponder.py claude")
        sys.exit(1)

    instance_id = sys.argv[1]
    responder = SafeAutoResponder(instance_id)

    try:
        await responder.start()
    except KeyboardInterrupt:
        print("\n✋ Stopped by user")
        responder.stop()


if __name__ == "__main__":
    asyncio.run(main())