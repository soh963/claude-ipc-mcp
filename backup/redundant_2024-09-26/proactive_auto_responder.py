#!/usr/bin/env python3
"""
Proactive Auto-Responder for Claude IPC
각 인스턴스가 자동으로 메시지를 보내고 받는 시스템
"""

import asyncio
import json
import sqlite3
import time
import hashlib
import random
from pathlib import Path
from typing import Optional, Dict, Set, List
from datetime import datetime, timedelta

class ProactiveAutoResponder:
    """능동적 자동 응답 시스템 - 자동으로 메시지를 보내고 받음"""

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

        # 능동적 메시지 전송을 위한 설정
        self.last_proactive_message = {}  # 마지막 능동 메시지 시간 (수신자별)
        self.proactive_interval = 30.0  # 30초마다 능동적으로 메시지 전송
        self.proactive_cooldown = 60.0  # 각 인스턴스에게 최소 60초 간격

        # 인스턴스별 역할 정의
        self.instance_roles = {
            'claude': 'AI 어시스턴트 & 코디네이터',
            'gemini': '프로젝트 매니저 & 분석가',
            'codex': '코드 리뷰어 & 개발자',
            'lm': '언어 모델 & 문서화 전문가'
        }

        # 인스턴스별 능동적 메시지 템플릿
        self.proactive_templates = {
            'claude': [
                "프로젝트 진행 상황은 어떠신가요?",
                "도움이 필요한 작업이 있으신가요?",
                "현재 작업 중인 내용을 공유해주시겠어요?"
            ],
            'gemini': [
                "새로운 분석 결과가 있습니다. 확인하시겠습니까?",
                "프로젝트 일정을 업데이트했습니다.",
                "리소스 할당에 대한 제안이 있습니다."
            ],
            'codex': [
                "코드 리뷰가 필요한 부분이 있습니다.",
                "최신 커밋을 확인해주세요.",
                "리팩토링 제안사항이 있습니다."
            ],
            'lm': [
                "문서 업데이트가 필요합니다.",
                "새로운 가이드라인을 작성했습니다.",
                "번역이 필요한 내용이 있습니다."
            ]
        }

    async def start_monitoring(self):
        """실시간 메시지 모니터링 및 능동적 메시지 전송 시작"""
        self.running = True
        print(f"\n{'='*60}")
        print(f"🚀 [{self.instance_id.upper()}] 능동적 자동 응답 시스템 시작")
        print(f"{'='*60}")
        print(f"   ✅ 인스턴스 ID: {self.instance_id}")
        print(f"   ✅ 역할: {self.instance_roles.get(self.instance_id, '알 수 없음')}")
        print(f"   ✅ 무한 루프 방지: 활성화")
        print(f"   ✅ 능동적 메시지: 활성화 (간격: {self.proactive_interval}초)")
        print(f"   ✅ 양방향 통신: 활성화")
        print(f"   ⏱️ 체크 간격: {self.check_interval}초")
        print(f"{'='*60}\n")

        # 비동기 태스크 생성
        tasks = [
            asyncio.create_task(self.message_monitoring_loop()),
            asyncio.create_task(self.proactive_messaging_loop())
        ]

        # 모든 태스크 실행
        await asyncio.gather(*tasks)

    async def message_monitoring_loop(self):
        """메시지 모니터링 루프 - 받은 메시지 처리"""
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
                print(f"❌ [{self.instance_id}] 모니터링 오류: {e}")
                await asyncio.sleep(5)

    async def proactive_messaging_loop(self):
        """능동적 메시지 전송 루프 - 자동으로 다른 인스턴스에게 메시지 전송"""
        await asyncio.sleep(10)  # 시작 후 10초 대기

        while self.running:
            try:
                # 다른 모든 인스턴스 목록 가져오기
                other_instances = await self.get_other_instances()

                for target_id in other_instances:
                    # 능동적 메시지를 보낼 시간인지 확인
                    if await self.should_send_proactive_message(target_id):
                        await self.send_proactive_message(target_id)

                # 능동적 메시지 간격만큼 대기
                await asyncio.sleep(self.proactive_interval)

            except Exception as e:
                print(f"❌ [{self.instance_id}] 능동적 메시지 오류: {e}")
                await asyncio.sleep(10)

    async def get_other_instances(self) -> List[str]:
        """다른 인스턴스 목록 가져오기"""
        all_instances = ['claude', 'gemini', 'codex', 'lm']
        return [inst for inst in all_instances if inst != self.instance_id]

    async def should_send_proactive_message(self, target_id: str) -> bool:
        """능동적 메시지를 보낼지 결정"""
        current_time = time.time()

        # 마지막 능동 메시지 시간 확인
        if target_id in self.last_proactive_message:
            time_since_last = current_time - self.last_proactive_message[target_id]
            if time_since_last < self.proactive_cooldown:
                return False

        # 30% 확률로 메시지 전송 (너무 많은 메시지 방지)
        return random.random() < 0.3

    async def send_proactive_message(self, target_id: str):
        """능동적으로 메시지 전송"""
        # 템플릿에서 랜덤 메시지 선택
        templates = self.proactive_templates.get(self.instance_id, [])
        if not templates:
            return

        message = random.choice(templates)

        # 시간 정보나 컨텍스트 추가
        current_time = datetime.now().strftime('%H:%M')
        enhanced_message = f"[{current_time}] {message}"

        # 메시지 전송
        success = await self.send_message(target_id, enhanced_message)
        if success:
            print(f"\n💬 [{self.instance_id.upper()}] 능동적 메시지 전송")
            print(f"   📥 수신자: {target_id}")
            print(f"   💭 메시지: {enhanced_message}")
            print(f"   ⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─'*60}\n")

            # 마지막 능동 메시지 시간 업데이트
            self.last_proactive_message[target_id] = time.time()

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

        # 3. 무의미한 반복 패턴 감지 (따옴표 반복, 메시지 받았습니다 반복 등)
        import re
        meaningless_patterns = [
            r"^['\"\s]+$",  # 따옴표와 공백만
            r"^(메시지 받았습니다[:：]\s*)+",  # "메시지 받았습니다" 반복
            r"^['\"]*메시지 받.*메시지 받",  # 중첩된 "메시지 받았습니다"
            r"^요청을 확인했습니다.*요청을 확인했습니다",  # 중첩된 응답
            r"^처리 중입니다.*처리 중입니다",  # 중첩된 처리 메시지
            r"^\.\.\.",  # 점만 있는 경우
            r"^['\"]+(.*요청을 확인했습니다|.*처리 중입니다)",  # 따옴표로 시작하는 자동응답
            r".*\.\.\.\' 요청을 확인했습니다",  # 잘린 메시지
        ]

        for pattern in meaningless_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # 무의미한 메시지는 조용히 무시
                return False

        # 3. 메시지 해시를 생성하여 중복 확인
        msg_hash = self.get_message_hash(msg)
        if msg_hash in self.processed_messages:
            return False

        # 4. 너무 빈번한 메시지 체크 (스팸 방지)
        from_id = msg['from_id']
        if from_id in self.message_cooldown:
            if time.time() - self.message_cooldown[from_id] < 1.0:  # 1초 쿨다운
                return False

        # 5. 동일한 내용 반복 체크 (핑퐁 방지)
        if self.is_ping_pong_message(msg):
            return False

        return True

    async def process_message(self, msg: dict):
        """메시지 처리 및 응답"""
        from_id = msg['from_id']
        content = msg['content']

        # 메시지 표시
        print(f"\n📨 [{self.instance_id.upper()}] 메시지 수신!")
        print(f"   📤 발신자: {from_id}")
        print(f"   💬 메시지: {content}")
        print(f"   🕐 시간: {msg['timestamp']}")

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
                    return

            # 응답 전송
            success = await self.send_message(from_id, response)
            if success:
                print(f"   ↪️ 응답: {response}")
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
            "확인했습니다",
            "알겠습니다"
        ]

        # 자동 응답 메시지는 다시 응답하지 않음
        if any(pattern in content for pattern in auto_response_patterns):
            return None

        # 길이 체크 - 너무 짧거나 너무 긴 메시지는 무시
        if len(content) < 3 or len(content) > 500:
            return None

        # 반복 문자 체크 (따옴표, 점 등 반복)
        if content.count("'") > 10 or content.count('"') > 10 or content.count('.') > 10:
            return None

        # 역할 기반 응답 생성
        my_role = self.instance_roles.get(self.instance_id, '')
        their_role = self.instance_roles.get(from_id, '')

        # 인스턴스별 맞춤 응답
        if self.instance_id == 'claude':
            if "프로젝트" in content or "project" in content:
                return f"프로젝트 관련 지원을 제공하겠습니다. ({my_role})"
            elif "도움" in content or "help" in content:
                return f"도움이 필요하신 부분을 자세히 알려주세요. ({my_role})"

        elif self.instance_id == 'gemini':
            if "분석" in content or "analysis" in content:
                return f"데이터 분석을 시작하겠습니다. ({my_role})"
            elif "일정" in content or "schedule" in content:
                return f"프로젝트 일정을 검토하겠습니다. ({my_role})"

        elif self.instance_id == 'codex':
            if "코드" in content or "code" in content:
                return f"코드 리뷰를 진행하겠습니다. ({my_role})"
            elif "리팩토링" in content or "refactor" in content:
                return f"리팩토링 제안을 준비하겠습니다. ({my_role})"

        elif self.instance_id == 'lm':
            if "문서" in content or "document" in content:
                return f"문서화 작업을 시작하겠습니다. ({my_role})"
            elif "번역" in content or "translate" in content:
                return f"번역 작업을 진행하겠습니다. ({my_role})"

        # 특정 키워드에 대한 일반 응답
        if "안녕" in content or "hello" in content:
            # 인사는 한 번만 응답
            if from_id in self.response_history:
                recent_responses = [r for r in self.response_history[from_id]
                                  if time.time() - r['timestamp'] < 300]  # 5분 이내
                if any("안녕" in r['content'] for r in recent_responses):
                    return None
            return f"안녕하세요 {from_id}님! {self.instance_id}입니다. 무엇을 도와드릴까요?"

        elif "상태" in content or "status" in content:
            return f"[{self.instance_id}] 정상 작동 중. 역할: {my_role}"

        elif "?" in content:
            # 질문에 대한 응답
            return f"[{self.instance_id}] 질문을 받았습니다. 검토 후 답변드리겠습니다."

        # 대부분의 일반 메시지는 응답하지 않음 (무한 루프 방지)
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

    async def send_message(self, to_id: str, content: str) -> bool:
        """메시지 전송"""
        # 빈 메시지 안정 장치
        if not content or not content.strip():
            # 빈 메시지는 조용히 무시
            return False

        # 무의미한 메시지 차단
        import re
        blocked_patterns = [
            r"^['\"\s\.]+$",  # 특수문자만 있는 경우
            r".*메시지 받았습니다.*메시지 받았습니다",  # 중첩된 자동응답
            r".*요청을 확인했습니다.*요청을 확인했습니다",  # 중첩된 자동응답
            r"^['\"]+(.*\.\.\.)$",  # 따옴표와 점만 있는 경우
        ]

        for pattern in blocked_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # 무의미한 메시지는 전송하지 않음
                return False

        # 메시지 길이 체크
        if len(content) < 3 or len(content) > 500:
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
            print(f"메시지 전송 오류: {e}")
            return False

    def stop(self):
        """모니터링 중지"""
        self.running = False
        print(f"🔕 [{self.instance_id}] 능동적 자동 응답 시스템 중지")


async def main():
    """메인 실행 함수"""
    import sys

    # 인스턴스 ID 설정 (명령줄 인자 또는 기본값)
    instance_id = sys.argv[1] if len(sys.argv) > 1 else "claude"

    # 능동적 자동 응답기 시작
    responder = ProactiveAutoResponder(instance_id, check_interval=2.0)
    await responder.start_monitoring()


if __name__ == "__main__":
    print("🚀 Proactive Claude IPC Auto-Responder")
    print("   능동적 메시지 전송 | 양방향 통신 | 무한 루프 방지")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n프로그램 종료...")