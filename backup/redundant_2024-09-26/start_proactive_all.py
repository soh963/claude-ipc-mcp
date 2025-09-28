#!/usr/bin/env python3
"""
모든 인스턴스를 능동적 모드로 시작
각 인스턴스가 자동으로 메시지를 보내고 받음
"""

import subprocess
import sys
import time
from pathlib import Path

def start_proactive_instances():
    """모든 인스턴스를 능동적 자동 응답 모드로 시작"""

    print("🚀 Claude IPC MCP - 능동적 자동 통신 시스템 시작")
    print("="*60)
    print("각 인스턴스가 자동으로 메시지를 보내고 받을 수 있게 설정합니다.")
    print()

    # 1. 데이터베이스 초기화
    print("📊 데이터베이스 초기화 중...")
    subprocess.run([sys.executable, "tools/ipc_manager.py", "init"])

    # 2. 모든 인스턴스 등록
    instances = ["claude", "gemini", "codex", "lm"]

    print("\n📝 인스턴스 등록 중...")
    for instance_id in instances:
        subprocess.run([sys.executable, "tools/ipc_manager.py", "register", instance_id])

    # 3. 각 인스턴스를 별도의 창에서 실행 (Windows)
    print("\n🔄 각 인스턴스 자동 응답 시스템 시작 중...")
    print("   • 각 인스턴스는 별도의 창에서 실행됩니다")
    print("   • 모든 인스턴스가 자동으로 메시지를 보내고 받습니다")
    print("   • 무한 루프 방지 기능이 활성화되어 있습니다")
    print()

    processes = []

    # Windows에서 각 인스턴스를 새 창에서 실행
    for instance_id in instances:
        print(f"🟢 {instance_id.upper()} 인스턴스 시작...")

        # Windows의 경우 start 명령어 사용
        cmd = f'start "{instance_id.upper()} Instance" cmd /k python tools/proactive_auto_responder.py {instance_id}'

        # Git Bash를 사용하는 경우
        if sys.platform != 'win32':
            process = subprocess.Popen(
                [sys.executable, "tools/proactive_auto_responder.py", instance_id],
                cwd=Path(__file__).parent
            )
            processes.append(process)
        else:
            # Windows CMD 사용
            subprocess.Popen(cmd, shell=True, cwd=Path(__file__).parent)

        time.sleep(1)  # 각 인스턴스 시작 사이 잠시 대기

    print("\n✅ 시스템이 성공적으로 시작되었습니다!")
    print("\n" + "="*60)
    print("📌 사용법:")
    print("   1. 각 인스턴스는 자동으로 메시지를 보내고 받습니다")
    print("   2. 수동으로 메시지 보내기:")
    print("      python tools/ipc_manager.py send [from] [to] [message]")
    print("   3. 메시지 확인:")
    print("      python tools/ipc_manager.py show-all")
    print("   4. 통계 보기:")
    print("      python tools/ipc_manager.py stats")
    print("   5. 종료: 각 창에서 Ctrl+C")
    print()
    print("💡 팁: 약 30초 후부터 인스턴스들이 서로 능동적으로 대화를 시작합니다.")
    print("="*60)
    print()

    # 프로세스가 실행 중인 경우 대기
    if processes:
        try:
            # Unix/Linux 시스템에서 프로세스 대기
            for process in processes:
                process.wait()
        except KeyboardInterrupt:
            print("\n\n🔕 시스템을 종료합니다...")
            for process in processes:
                process.terminate()
            sys.exit(0)
    else:
        # Windows에서는 수동으로 관찰
        print("⚠️ 각 CMD 창에서 인스턴스가 실행 중입니다.")
        print("   메인 창은 Enter를 누르면 종료됩니다.")
        input()

if __name__ == "__main__":
    start_proactive_instances()