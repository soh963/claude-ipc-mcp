#!/usr/bin/env python3
"""
Real-time message notifier for Claude IPC
Enables instant message notifications and auto-responses
"""

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Optional, Callable

class RealtimeNotifier:
    """실시간 메시지 알림 및 자동 응답 시스템"""

    def __init__(self, instance_id: str, check_interval: float = 2.0):
        self.instance_id = instance_id
        self.check_interval = check_interval
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_check = time.time()
        self.running = False
        self.auto_response_handler: Optional[Callable] = None

    def set_auto_response(self, handler: Callable):
        """자동 응답 핸들러 설정"""
        self.auto_response_handler = handler

    async def start_monitoring(self):
        """실시간 메시지 모니터링 시작"""
        self.running = True
        print(f"🔔 실시간 메시지 모니터링 시작 (인스턴스: {self.instance_id})")

        while self.running:
            try:
                # 새 메시지 확인
                new_messages = await self.check_new_messages()

                if new_messages:
                    for msg in new_messages:
                        print(f"\n📨 새 메시지 도착!")
                        print(f"   발신: {msg['from_id']}")
                        print(f"   내용: {msg['content']}")
                        print(f"   시간: {msg['timestamp']}")

                        # 자동 응답 처리
                        if self.auto_response_handler:
                            response = await self.auto_response_handler(msg)
                            if response:
                                await self.send_response(msg['from_id'], response)
                                print(f"   ↪️ 자동 응답 전송: {response[:50]}...")

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")
                await asyncio.sleep(5)

    async def check_new_messages(self):
        """데이터베이스에서 새 메시지 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 마지막 확인 이후의 새 메시지 조회
            cursor.execute("""
                SELECT from_id, to_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND timestamp > datetime(?, 'unixepoch')
                ORDER BY timestamp ASC
            """, (self.instance_id, self.last_check))

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
                self.last_check = time.time()

            return messages

        except Exception as e:
            print(f"DB 조회 오류: {e}")
            return []

    async def send_response(self, to_id: str, content: str):
        """자동 응답 전송"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 메시지 저장
            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """, (self.instance_id, to_id, content))

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
    # Claude 인스턴스용 실시간 알림 설정
    notifier = RealtimeNotifier("claude", check_interval=2.0)

    # 자동 응답 핸들러 정의
    async def auto_responder(message):
        """간단한 자동 응답 로직"""
        content = message['content'].lower()
        from_id = message['from_id']

        # Gemini로부터의 메시지는 자동 응답하지 않음
        if from_id == "gemini":
            print(f"   ℹ️ Gemini 메시지 수신 확인 (자동 응답 비활성화)")
            return None

        # 키워드 기반 자동 응답 (Gemini 외 인스턴스만)
        if "안녕" in content or "hello" in content:
            return f"안녕하세요! {from_id}님. 무엇을 도와드릴까요?"
        elif "도움" in content or "help" in content:
            return "제가 도와드릴 수 있는 기능: 메시지 전송, 파일 공유, 명령 실행 등"
        elif "시간" in content or "time" in content:
            from datetime import datetime
            return f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            # 기본 응답 - 메시지를 받았다는 확인
            return f"메시지 받았습니다: '{content[:30]}...' 처리 중입니다."

    # 자동 응답 설정
    notifier.set_auto_response(auto_responder)

    # 모니터링 시작
    await notifier.start_monitoring()


if __name__ == "__main__":
    print("🚀 Claude IPC 실시간 알림 시스템")
    print("=" * 40)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n프로그램 종료...")