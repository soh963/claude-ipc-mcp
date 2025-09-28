#!/usr/bin/env python3
"""
Smart Auto-Responder for Claude IPC
무한 루프 방지와 지능적인 메시지 처리
"""

import asyncio
import json
import sqlite3
import time
import hashlib
from pathlib import Path
from typing import Optional, Callable, Dict, Set
from datetime import datetime, timedelta

class SmartAutoResponder:
    """스마트 자동 응답 시스템 - 무한 루프 방지 및 지능적 처리"""

    def __init__(self, instance_id: str, check_interval: float = 2.0):
        self.instance_id = instance_id
        self.check_interval = check_interval
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_check = time.time()
        self.running = False

        # 무한 루프 방지를 위한 추적 시스템
        self.processed_messages = set()  # 처리된 메시지 해시
        self.response_history = {}  # 응답 히스토리 (발신자별)
        self.last_sent_messages = {}  # 마지막 전송 메시지 (수신자별)
        self.message_cooldown = {}  # 메시지 쿨다운 (발신자별)

    async def start_monitoring(self):
        """실시간 메시지 모니터링 시작"""
        self.running = True
        print(f"\n{'='*60}")
        print(f"🔔 [{self.instance_id.upper()}] 스마트 실시간 모니터링 시작")
        print(f"{'='*60}")
        print(f"   ✅ 인스턴스 ID: {self.instance_id}")
        print(f"   ✅ 무한 루프 방지: 활성화")
        print(f"   ✅ 중복 메시지 필터링: 활성화")
        print(f"   ✅ 스마트 응답 시스템: 활성화")
        print(f"   ⏱️ 체크 간격: {self.check_interval}초")
        print(f"{'='*60}\n")

        while self.running:
            try:
                # 새 메시지 확인
                new_messages = await self.check_new_messages()

                if new_messages:
                    for msg in new_messages:
                        # 메시지 처리 여부 확인
                        if await self.should_process_message(msg):
                            await self.process_message(msg)

                await asyncio.sleep(self.check_interval)

                # 주기적으로 오래된 기록 정리 (메모리 관리)
                await self.cleanup_old_records()

            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")
                await asyncio.sleep(5)

    async def should_process_message(self, msg: dict) -> bool:
        """메시지를 처리해야 하는지 판단"""

        # 1. 자기 자신에게 보낸 메시지는 무시
        if msg['from_id'] == self.instance_id:
            return False

        # 2. 빈 메시지나 공백만 있는 메시지 무시 (조용히)
        content = msg['content'].strip()
        if not content:
            # 빈 메시지는 조용히 무시 (출력하지 않음)
            return False

        # 3. 메시지 해시를 생성하여 중복 확인
        msg_hash = self.get_message_hash(msg)
        if msg_hash in self.processed_messages:
            print(f"   ⚠️ 중복 메시지 무시 (발신: {msg['from_id']})")
            return False

        # 4. 너무 빈번한 메시지 체크 (스팸 방지)
        from_id = msg['from_id']
        if from_id in self.message_cooldown:
            if time.time() - self.message_cooldown[from_id] < 1.0:  # 1초 쿨다운
                print(f"   ⚠️ 너무 빈번한 메시지 (발신: {from_id})")
                return False

        # 5. 동일한 내용 반복 체크 (핑퐁 방지)
        if self.is_ping_pong_message(msg):
            print(f"   ⚠️ 핑퐁 패턴 감지 (발신: {from_id})")
            return False

        return True

    async def process_message(self, msg: dict):
        """메시지 처리 및 응답"""
        from_id = msg['from_id']
        content = msg['content']

        # 메시지 표시 (더 명확한 포맷)
        print(f"\n{'='*60}")
        print(f"📨 [{self.instance_id.upper()}] 새 메시지 수신!")
        print(f"{'='*60}")
        print(f"   📤 발신자: {from_id}")
        print(f"   💬 메시지: {content}")
        print(f"   🕐 시간: {msg['timestamp']}")
        print(f"{'─'*60}")

        # 메시지를 처리된 것으로 표시
        msg_hash = self.get_message_hash(msg)
        self.processed_messages.add(msg_hash)
        self.message_cooldown[from_id] = time.time()

        # 자동 응답 생성
        response = await self.generate_smart_response(msg)

        if response:
            # 응답이 마지막 전송과 동일한지 확인 (무한 루프 방지)
            if from_id in self.last_sent_messages:
                if self.last_sent_messages[from_id] == response:
                    print(f"   ⚠️ 동일한 응답 반복 방지")
                    return

            # 응답 전송
            success = await self.send_response(from_id, response)
            if success:
                print(f"\n📤 [{self.instance_id.upper()}] 응답 전송")
                print(f"   📥 수신자: {from_id}")
                print(f"   💬 응답: {response}")
                print(f"{'='*60}\n")
                self.last_sent_messages[from_id] = response

                # 응답 히스토리 업데이트
                if from_id not in self.response_history:
                    self.response_history[from_id] = []
                self.response_history[from_id].append({
                    'content': response,
                    'timestamp': time.time()
                })

    async def generate_smart_response(self, msg: dict) -> Optional[str]:
        """스마트한 자동 응답 생성"""
        from_id = msg['from_id']
        content = msg['content'].lower()

        # 자동 응답 메시지 패턴 감지 - 무한 루프 방지
        auto_response_patterns = [
            "요청을 확인했습니다",
            "처리 중입니다",
            "메시지 받았습니다",
            "'메시지 받았습니다",
            "질문을 받았습니다"
        ]

        # 자동 응답 메시지는 다시 응답하지 않음
        if any(pattern in content for pattern in auto_response_patterns):
            print(f"   🚫 자동 응답 메시지 감지 - 응답 안 함")
            return None

        # 특정 인스턴스별 처리
        if from_id == "gemini":
            # Gemini와는 협업 모드
            if "프로젝트" in content or "project" in content:
                return "프로젝트 관련 정보를 공유하겠습니다. 어떤 부분이 필요하신가요?"
            elif "파일" in content or "file" in content:
                return "파일 목록을 확인하고 필요한 파일을 공유할 수 있습니다."
            else:
                # 일반 Gemini 메시지는 확인만
                print(f"   ℹ️ Gemini 메시지 수신 확인")
                return None

        elif from_id == "codex":
            # Codex와는 코드 관련 협업
            if "코드" in content or "code" in content:
                return "코드 리뷰나 수정이 필요하신가요? 구체적인 요청을 알려주세요."
            elif "디렉토리" in content or "directory" in content:
                return "디렉토리 구조 정보를 받았습니다. 추가 분석이 필요하면 알려주세요."
            else:
                # Codex의 일반 메시지도 확인만
                print(f"   ℹ️ Codex 메시지 수신 확인")
                return None

        elif from_id == "lm":
            # LM과는 언어 모델 협업
            if "분석" in content or "analyze" in content:
                return "분석 작업을 도와드리겠습니다. 어떤 데이터를 분석하시겠습니까?"
            else:
                # LM의 일반 메시지도 확인만
                print(f"   ℹ️ LM 메시지 수신 확인")
                return None

        # 일반적인 키워드 기반 응답 - 최초 1회만
        if "안녕" in content or "hello" in content or "hi" in content:
            # 인사는 한 번만 응답
            if from_id in self.response_history:
                recent_responses = [r for r in self.response_history[from_id]
                                  if time.time() - r['timestamp'] < 300]  # 5분 이내
                if any("안녕" in r['content'] for r in recent_responses):
                    return None  # 이미 인사했으면 무시
            return f"안녕하세요 {from_id}님! 무엇을 도와드릴까요?"

        elif "도움" in content or "help" in content:
            return "다음을 도와드릴 수 있습니다: 메시지 전송, 파일 공유, 코드 분석, 프로젝트 협업"

        elif "시간" in content or "time" in content:
            from datetime import datetime
            return f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        elif "상태" in content or "status" in content:
            return f"Claude IPC 시스템 정상 작동 중. 인스턴스 {self.instance_id} 활성화."

        # 모든 다른 메시지는 응답하지 않음 (무한 루프 방지)
        print(f"   ✅ 메시지 확인 (자동 응답 필요 없음)")
        return None

    def get_message_hash(self, msg: dict) -> str:
        """메시지 고유 해시 생성"""
        unique_str = f"{msg['from_id']}:{msg['content']}:{msg['timestamp']}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def is_ping_pong_message(self, msg: dict) -> bool:
        """핑퐁 패턴 감지"""
        from_id = msg['from_id']
        content = msg['content']

        # 마지막으로 이 사용자에게 보낸 메시지와 비슷한지 확인
        if from_id in self.last_sent_messages:
            last_sent = self.last_sent_messages[from_id]
            # 내용이 너무 비슷하면 핑퐁으로 판단
            if self.similarity_check(content, last_sent) > 0.8:
                return True

        return False

    def similarity_check(self, str1: str, str2: str) -> float:
        """두 문자열의 유사도 체크 (0.0 ~ 1.0)"""
        str1_lower = str1.lower()
        str2_lower = str2.lower()

        # 완전히 같으면 1.0
        if str1_lower == str2_lower:
            return 1.0

        # 한쪽이 다른 쪽을 포함하면 0.8
        if str1_lower in str2_lower or str2_lower in str1_lower:
            return 0.8

        # 공통 단어 비율로 계산
        words1 = set(str1_lower.split())
        words2 = set(str2_lower.split())

        if not words1 or not words2:
            return 0.0

        common_words = words1.intersection(words2)
        total_words = words1.union(words2)

        return len(common_words) / len(total_words) if total_words else 0.0

    async def cleanup_old_records(self):
        """오래된 기록 정리 (메모리 관리)"""
        current_time = time.time()

        # 1시간 이상 된 처리 메시지 해시 제거
        if len(self.processed_messages) > 1000:
            self.processed_messages.clear()

        # 오래된 응답 히스토리 정리
        for from_id in list(self.response_history.keys()):
            self.response_history[from_id] = [
                r for r in self.response_history[from_id]
                if current_time - r['timestamp'] < 3600  # 1시간 이내만 유지
            ]
            if not self.response_history[from_id]:
                del self.response_history[from_id]

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

    async def send_response(self, to_id: str, content: str) -> bool:
        """자동 응답 전송"""
        # 빈 메시지 안정 장치
        if not content or not content.strip():
            # 빈 메시지는 조용히 무시
            return False

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
        print("🔕 스마트 실시간 모니터링 중지")


async def main():
    """메인 실행 함수"""
    import sys

    # 인스턴스 ID 설정 (명령줄 인자 또는 기본값)
    instance_id = sys.argv[1] if len(sys.argv) > 1 else "claude"

    # 스마트 자동 응답기 시작
    responder = SmartAutoResponder(instance_id, check_interval=2.0)
    await responder.start_monitoring()


if __name__ == "__main__":
    print("🚀 Smart Claude IPC Auto-Responder")
    print("   무한 루프 방지 | 중복 필터링 | 스마트 응답")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n프로그램 종료...")