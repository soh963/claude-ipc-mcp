#!/usr/bin/env python3
"""
Real-time message notifier for Claude IPC - Multi-instance version
Enables instant message notifications and auto-responses for multiple instances
"""

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Optional, Callable, List

class RealtimeNotifier:
    """실시간 메시지 알림 및 자동 응답 시스템"""

    def __init__(self, instance_ids: List[str], check_interval: float = 2.0):
        self.instance_ids = instance_ids  # 여러 인스턴스 지원
        self.check_interval = check_interval
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_checks = {id: time.time() for id in instance_ids}
        self.running = False
        self.auto_response_handler: Optional[Callable] = None

    def set_auto_response(self, handler: Callable):
        """자동 응답 핸들러 설정"""
        self.auto_response_handler = handler

    async def start_monitoring(self):
        """실시간 메시지 모니터링 시작"""
        self.running = True
        print(f"🔔 실시간 메시지 모니터링 시작 (인스턴스: {', '.join(self.instance_ids)})")

        while self.running:
            try:
                # 모든 인스턴스의 새 메시지 확인
                for instance_id in self.instance_ids:
                    new_messages = await self.check_new_messages(instance_id)

                    if new_messages:
                        for msg in new_messages:
                            print(f"\n📨 새 메시지 도착! (수신: {instance_id})")
                            print(f"   발신: {msg['from_id']}")
                            print(f"   내용: {msg['content']}")
                            print(f"   시간: {msg['timestamp']}")

                            # 자동 응답 처리
                            if self.auto_response_handler:
                                response = await self.auto_response_handler(msg, instance_id)
                                if response:
                                    await self.send_response(instance_id, msg['from_id'], response)
                                    print(f"   ↪️ 자동 응답 전송 ({instance_id} → {msg['from_id']}): {response[:50]}...")

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")
                await asyncio.sleep(5)

    async def check_new_messages(self, instance_id: str):
        """데이터베이스에서 특정 인스턴스의 새 메시지 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 마지막 확인 이후의 새 메시지 조회
            cursor.execute("""
                SELECT from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND timestamp > datetime(?, 'unixepoch')
                ORDER BY timestamp ASC
            """, (instance_id, self.last_checks[instance_id]))

            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'from_id': row[0],
                    'to_id': row[1],
                    'content': row[2],
                    'timestamp': row[3]
                })

            conn.close()

            # 마지막 확인 시간 업데이트
            if messages:
                self.last_checks[instance_id] = time.time()

            return messages

        except Exception as e:
            print(f"DB 조회 오류: {e}")
            return []

    async def send_response(self, from_id: str, to_id: str, content: str):
        """자동 응답 전송"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 메시지 저장
            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """, (from_id, to_id, content))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"응답 전송 오류: {e}")
            return False

    def stop(self):
        """모니터링 중지"""
        self.running = False
        print("🔕 실시간 메시지 모니터링 중지")


# 사용 예시
async def main():
    # Claude와 Codex 인스턴스 모두 모니터링
    notifier = RealtimeNotifier(["claude", "codex"], check_interval=2.0)

    # 자동 응답 핸들러 정의
    async def auto_responder(message, receiver_id):
        """간단한 자동 응답 로직"""
        content = message['content'].lower()
        from_id = message['from_id']

        # 키워드 기반 자동 응답
        if "안녕" in content or "hello" in content:
            return f"안녕하세요! {from_id}님. 저는 {receiver_id}입니다. 무엇을 도와드릴까요?"
        elif "도움" in content or "help" in content:
            return f"[{receiver_id}] 제가 도와드릴 수 있는 기능: 메시지 전송, 파일 공유, 명령 실행 등"
        elif "시간" in content or "time" in content:
            from datetime import datetime
            return f"[{receiver_id}] 현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif "파일" in content or "file" in content:
            return f"[{receiver_id}] 파일 관련 작업을 처리할 수 있습니다. 어떤 파일을 찾고 계신가요?"
        else:
            # 기본 응답 - 메시지를 받았다는 확인
            return f"[{receiver_id}] 메시지 받았습니다: '{content[:30]}...' 처리 중입니다."

    # 자동 응답 설정
    notifier.set_auto_response(auto_responder)

    # 모니터링 시작
    await notifier.start_monitoring()


if __name__ == "__main__":
    print("🚀 Claude IPC 실시간 알림 시스템 (Multi-Instance)")
    print("=" * 40)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n프로그램 종료...")