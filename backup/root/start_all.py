#!/usr/bin/env python3
"""
모든 인스턴스 자동 시작 스크립트
4개 AI 인스턴스 (claude, gemini, codex, lm)를 한 번에 시작합니다.
"""

import subprocess
import sys
import time
from pathlib import Path

def start_all_instances():
    """모든 인스턴스 자동 응답 시작"""

    print("🚀 Claude IPC MCP 시스템 시작")
    print("=" * 60)

    # 1. 데이터베이스 초기화 확인
    print("📊 데이터베이스 초기화 중...")
    subprocess.run([sys.executable, "tools/ipc_manager.py", "init"])

    # 2. 인스턴스 등록
    instances = ["claude", "gemini", "codex", "lm"]

    print("\n📝 인스턴스 등록 중...")
    for instance_id in instances:
        subprocess.run([sys.executable, "tools/ipc_manager.py", "register", instance_id])

    # 3. 다중 인스턴스 응답기 시작
    print("\n🔄 자동 응답 시스템 시작 중...")
    print("   • 무한 루프 방지: 활성화")
    print("   • 중복 메시지 필터링: 활성화")
    print("   • 스마트 응답: 활성화")
    print()

    try:
        # multi_instance_responder.py 실행
        process = subprocess.Popen(
            [sys.executable, "tools/multi_instance_responder.py"],
            cwd=Path(__file__).parent
        )

        print("✅ 시스템이 성공적으로 시작되었습니다!")
        print("\n📌 사용법:")
        print("   1. 메시지 보내기: python tools/ipc_manager.py send [from] [to] [message]")
        print("   2. 메시지 확인: python tools/ipc_manager.py check [instance_id]")
        print("   3. 모든 메시지 보기: python tools/ipc_manager.py show-all")
        print("   4. 종료: Ctrl+C")
        print()
        print("💡 예시: python tools/ipc_manager.py send claude gemini '안녕하세요!'")
        print()

        # 프로세스 대기
        process.wait()

    except KeyboardInterrupt:
        print("\n\n🔕 시스템을 종료합니다...")
        process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    start_all_instances()