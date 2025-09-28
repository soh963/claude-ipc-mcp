#!/usr/bin/env python3
"""
인터랙티브 테스트 - 모든 인스턴스가 서로 메시지 교환
각 인스턴스가 다른 인스턴스에게 자동으로 메시지를 보내는 시뮬레이션
"""

import sqlite3
import time
import random
from pathlib import Path
from datetime import datetime

class InteractiveTest:
    """인터랙티브 테스트 클래스"""

    def __init__(self):
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.instances = ["claude", "gemini", "codex", "lm"]

        # 각 인스턴스별 메시지 패턴
        self.message_patterns = {
            "claude": [
                "안녕하세요! {to}님, 오늘 어떤 작업을 진행하시나요?",
                "{to}님, 프로젝트 진행 상황을 공유해주세요.",
                "좋은 아이디어가 있어요, {to}님!",
            ],
            "gemini": [
                "{to}님, 데이터 분석 결과를 확인해보세요.",
                "새로운 기능 제안이 있습니다, {to}님.",
                "{to}님과 협업하고 싶어요!",
            ],
            "codex": [
                "{to}님, 코드 리뷰 요청드립니다.",
                "버그를 발견했어요, {to}님 확인해주세요.",
                "{to}님, 최적화 방법에 대해 논의하고 싶어요.",
            ],
            "lm": [
                "{to}님, 문서 업데이트가 필요합니다.",
                "테스트 결과를 공유합니다, {to}님.",
                "{to}님, 배포 준비가 완료되었습니다.",
            ]
        }

    def send_message(self, from_id: str, to_id: str, content: str):
        """메시지 전송"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (from_id, to_id, content, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """, (from_id, to_id, content))

            conn.commit()
            conn.close()

            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] {from_id} → {to_id}: {content}")
            return True

        except Exception as e:
            print(f"❌ 메시지 전송 실패: {e}")
            return False

    def run_interactive_test(self, duration_seconds: int = 60):
        """인터랙티브 테스트 실행"""
        print(f"\n🚀 인터랙티브 테스트 시작 ({duration_seconds}초 동안)")
        print("=" * 60)
        print("각 인스턴스가 랜덤하게 다른 인스턴스에게 메시지를 보냅니다.")
        print("=" * 60 + "\n")

        start_time = time.time()
        message_count = 0

        while time.time() - start_time < duration_seconds:
            # 랜덤하게 발신자 선택
            from_id = random.choice(self.instances)

            # 수신자 선택 (자기 자신 제외)
            possible_recipients = [i for i in self.instances if i != from_id]
            to_id = random.choice(possible_recipients)

            # 메시지 선택
            message_template = random.choice(self.message_patterns[from_id])
            message = message_template.format(to=to_id)

            # 메시지 전송
            if self.send_message(from_id, to_id, message):
                message_count += 1

            # 3-10초 사이 랜덤 대기
            wait_time = random.uniform(3, 10)
            time.sleep(wait_time)

        print(f"\n✅ 테스트 완료!")
        print(f"   전송된 메시지: {message_count}개")
        print(f"   테스트 시간: {duration_seconds}초")

    def run_sequential_test(self):
        """순차적 테스트 - 각 인스턴스가 모든 다른 인스턴스에게 메시지"""
        print("\n🔄 순차적 테스트 시작")
        print("=" * 60)
        print("각 인스턴스가 다른 모든 인스턴스에게 메시지를 보냅니다.")
        print("=" * 60 + "\n")

        message_count = 0

        for from_id in self.instances:
            print(f"\n📤 {from_id}가 메시지를 보냅니다:")

            for to_id in self.instances:
                if from_id != to_id:
                    # 메시지 생성
                    message = f"안녕하세요 {to_id}님! {from_id}입니다. 테스트 메시지입니다."

                    # 메시지 전송
                    if self.send_message(from_id, to_id, message):
                        message_count += 1

                    # 1초 대기 (루프 방지)
                    time.sleep(1)

        print(f"\n✅ 순차적 테스트 완료!")
        print(f"   전송된 메시지: {message_count}개")

    def test_specific_interaction(self, from_id: str, to_id: str, message: str):
        """특정 인스턴스 간 상호작용 테스트"""
        print(f"\n🎯 특정 상호작용 테스트: {from_id} → {to_id}")
        print("=" * 60)

        if self.send_message(from_id, to_id, message):
            print("✅ 메시지 전송 성공!")
            print("\n💡 이제 자동 응답기가 이 메시지를 처리하고 응답할 것입니다.")
        else:
            print("❌ 메시지 전송 실패!")

def main():
    """메인 실행 함수"""
    import sys

    test = InteractiveTest()

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "interactive":
            # 인터랙티브 모드 (기본 60초)
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            test.run_interactive_test(duration)

        elif mode == "sequential":
            # 순차 테스트
            test.run_sequential_test()

        elif mode == "specific" and len(sys.argv) >= 5:
            # 특정 메시지
            from_id = sys.argv[2]
            to_id = sys.argv[3]
            message = " ".join(sys.argv[4:])
            test.test_specific_interaction(from_id, to_id, message)

        else:
            print("❌ 잘못된 명령어입니다.")
            print_usage()
    else:
        # 기본: 순차 테스트 실행
        test.run_sequential_test()

def print_usage():
    """사용법 출력"""
    print("""
사용법:
  python interactive_test.py [mode] [options]

모드:
  interactive [seconds]  - 랜덤 인터랙티브 테스트 (기본 60초)
  sequential            - 순차적 테스트 (모든 인스턴스가 서로에게)
  specific <from> <to> <message> - 특정 메시지 전송

예시:
  python interactive_test.py interactive 120  # 120초 동안 랜덤 테스트
  python interactive_test.py sequential       # 순차적 테스트
  python interactive_test.py specific gemini codex "협업 요청"
""")

if __name__ == "__main__":
    main()