#!/usr/bin/env python3
"""
IPC 메시지 모니터링 전용 스크립트
더미 메시지 송신 없이 모니터링만 수행
"""

import subprocess
import sys
import time
from pathlib import Path
import threading

def monitor_messages():
    """메시지를 실시간으로 모니터링"""
    print("\n📊 실시간 메시지 모니터링 중...")
    print("="*60)

    while True:
        try:
            # 모든 메시지 표시
            result = subprocess.run(
                [sys.executable, "tools/ipc_manager.py", "show-all"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )

            if result.stdout:
                print("\033[2J\033[H")  # 화면 클리어
                print("🔍 Claude IPC MCP - 메시지 모니터링")
                print("="*60)
                print(result.stdout)
                print("="*60)
                print("📌 종료하려면 Ctrl+C를 누르세요")

            time.sleep(2)  # 2초마다 업데이트

        except KeyboardInterrupt:
            print("\n\n🔕 모니터링을 종료합니다...")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            time.sleep(5)

def start_monitoring_only():
    """모니터링 전용 모드 시작"""

    print("🚀 Claude IPC MCP - 모니터링 전용 모드")
    print("="*60)
    print("메시지 모니터링만 수행합니다 (더미 송신 없음)")
    print()

    # 1. 데이터베이스 초기화
    print("📊 데이터베이스 초기화 중...")
    subprocess.run([sys.executable, "tools/ipc_manager.py", "init"])

    # 2. 인스턴스 등록 (필요한 경우)
    instances = ["claude", "gemini", "codex", "lm"]

    print("\n📝 인스턴스 등록 중...")
    for instance_id in instances:
        subprocess.run([sys.executable, "tools/ipc_manager.py", "register", instance_id])

    print("\n✅ 모니터링 시스템이 준비되었습니다!")
    print("\n" + "="*60)
    print("📌 다른 터미널에서 메시지 보내기:")
    print("   python tools/ipc_manager.py send [from] [to] [message]")
    print()
    print("📌 예시:")
    print("   python tools/ipc_manager.py send claude gemini \"안녕하세요\"")
    print("   python tools/ipc_manager.py send gemini claude \"반갑습니다\"")
    print()
    print("📌 통계 보기 (다른 터미널에서):")
    print("   python tools/ipc_manager.py stats")
    print("="*60)

    # 모니터링 시작
    try:
        monitor_messages()
    except KeyboardInterrupt:
        print("\n\n🔕 프로그램을 종료합니다...")
        sys.exit(0)

if __name__ == "__main__":
    start_monitoring_only()