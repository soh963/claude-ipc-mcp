#!/usr/bin/env python3
"""
Test bidirectional message exchange between AI instances
각 인스턴스가 다른 인스턴스로 메시지를 보낼 수 있는지 테스트
"""

import sqlite3
import time
from pathlib import Path

def send_message(from_id: str, to_id: str, content: str):
    """메시지 전송 함수"""
    db_path = Path.home() / ".claude-ipc-data" / "messages.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 메시지 저장
        cursor.execute("""
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, (from_id, to_id, content))

        conn.commit()
        print(f"✅ 메시지 전송: {from_id} → {to_id}: '{content}'")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 메시지 전송 실패: {e}")
        return False

def test_bidirectional():
    """양방향 메시지 교환 테스트"""
    print("🔄 양방향 메시지 교환 테스트 시작")
    print("=" * 50)

    # 1. 다른 인스턴스들이 Claude에게 메시지 보내기
    print("\n📤 Step 1: 다른 인스턴스 → Claude")
    instances = ["gemini", "codex", "lm"]

    for instance in instances:
        # 각 인스턴스가 Claude에게 고유한 메시지 보내기
        message = f"안녕 Claude! 저는 {instance}입니다. 프로젝트 협업 요청드립니다."
        send_message(instance, "claude", message)
        time.sleep(0.5)  # 메시지 간 간격

    print("\n⏳ 3초 대기 (Claude 응답 시간)...")
    time.sleep(3)

    # 2. Claude가 다른 인스턴스들에게 응답하는지 확인
    print("\n📥 Step 2: Claude의 응답 확인")

    # 3. 특정 키워드로 추가 테스트
    print("\n📤 Step 3: 특정 키워드 테스트")

    # Gemini가 프로젝트 관련 메시지 보내기
    send_message("gemini", "claude", "프로젝트 상태를 공유해주세요")
    time.sleep(1)

    # Codex가 코드 관련 메시지 보내기
    send_message("codex", "claude", "코드 리뷰가 필요합니다")
    time.sleep(1)

    # LM이 분석 관련 메시지 보내기
    send_message("lm", "claude", "데이터 분석을 시작하겠습니다")

    print("\n✅ 양방향 테스트 메시지 전송 완료")
    print("=" * 50)
    print("\n💡 이제 다음을 확인하세요:")
    print("1. Claude 인스턴스가 메시지를 받고 응답하는지")
    print("2. 무한 루프 없이 적절한 응답이 오가는지")
    print("3. 빈 메시지는 무시되는지")

if __name__ == "__main__":
    test_bidirectional()