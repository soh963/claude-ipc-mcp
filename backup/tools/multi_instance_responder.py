#!/usr/bin/env python3
"""
Multi-Instance Smart Auto-Responder
여러 인스턴스를 동시에 모니터링하고 자동 응답
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from smart_auto_responder import SmartAutoResponder


class MultiInstanceResponder:
    """여러 인스턴스를 관리하는 메인 컨트롤러"""

    def __init__(self):
        self.responders = {}
        self.running = False

    async def add_instance(self, instance_id: str, check_interval: float = 2.0):
        """인스턴스 추가"""
        if instance_id not in self.responders:
            responder = SmartAutoResponder(instance_id, check_interval)
            self.responders[instance_id] = responder
            print(f"✅ 인스턴스 추가: {instance_id}")
            return responder
        else:
            print(f"⚠️ 이미 존재하는 인스턴스: {instance_id}")
            return self.responders[instance_id]

    async def start_all(self):
        """모든 인스턴스 모니터링 시작"""
        self.running = True
        tasks = []

        print(f"\n🚀 멀티 인스턴스 모니터링 시작")
        print(f"   활성 인스턴스: {list(self.responders.keys())}")
        print("=" * 50)

        # 각 인스턴스별로 비동기 태스크 생성
        for instance_id, responder in self.responders.items():
            task = asyncio.create_task(responder.start_monitoring())
            tasks.append(task)

        # 모든 태스크 실행
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"❌ 멀티 인스턴스 오류: {e}")

    def stop_all(self):
        """모든 인스턴스 중지"""
        for responder in self.responders.values():
            responder.stop()
        self.running = False
        print("🔕 모든 인스턴스 모니터링 중지")


async def main():
    """메인 실행 함수"""

    # 활성화할 인스턴스 목록
    ACTIVE_INSTANCES = [
        "claude",   # Claude AI
        "gemini",   # Gemini AI
        "codex",    # Codex
        "lm"        # Language Model
    ]

    # 멀티 인스턴스 매니저 생성
    manager = MultiInstanceResponder()

    # 각 인스턴스 추가
    for instance_id in ACTIVE_INSTANCES:
        await manager.add_instance(instance_id, check_interval=2.0)

    # 모든 인스턴스 시작
    await manager.start_all()


if __name__ == "__main__":
    print("🎯 Multi-Instance Smart Auto-Responder")
    print("   무한 루프 방지 | 중복 필터링 | 스마트 응답")
    print("   여러 AI 인스턴스 동시 모니터링")
    print("=" * 50)

    # 명령줄 인자로 인스턴스 지정 가능
    if len(sys.argv) > 1:
        ACTIVE_INSTANCES = sys.argv[1:]
        print(f"커스텀 인스턴스: {ACTIVE_INSTANCES}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n모든 인스턴스 종료...")