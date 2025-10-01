#!/usr/bin/env python3
"""
Claude IPC Manager - Redirect to Global Command
이 스크립트는 레거시 호환성을 위해 유지되며, 모든 명령을 ipc_global_command.py로 리디렉션합니다.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """ipc_global_command.py로 명령 리디렉션"""

    # 현재 스크립트 경로에서 ipc_global_command.py 찾기
    current_dir = Path(__file__).parent
    global_command = current_dir / "ipc_global_command.py"

    if not global_command.exists():
        print(f"❌ Error: ipc_global_command.py not found at {global_command}")
        sys.exit(1)

    # 명령어 변환 매핑
    command_mapping = {
        "list": ["instances", "list", "--full"],
        "register": ["register"],
        "unregister": ["instances", "unregister"],
        "send": ["chat", "--to"],
        "broadcast": ["broadcast"],
        "check": ["messages", "check"],
        "show-all": ["messages", "list"],
        "clear": ["messages", "clear"],
        "status": ["status"],
        "stats": ["instances", "list", "--full"],
        "cleanup": ["messages", "cleanup"],
        "init": ["init"],
    }

    # --json 플래그 확인 및 제거
    json_output = "--json" in sys.argv
    if json_output:
        sys.argv.remove("--json")

    if len(sys.argv) < 2:
        print("⚠️  ipc_manager.py는 레거시 도구입니다.")
        print("📌 새로운 통합 명령어를 사용하세요:")
        print()
        print("   uv run python tools/ipc_global_command.py --help")
        print()
        print("또는 PATH에 등록된 경우:")
        print()
        print("   ipc --help")
        print()
        sys.exit(1)

    command = sys.argv[1].lower()

    # 명령어 변환
    if command in command_mapping:
        new_args = command_mapping[command]

        # 추가 인자 처리
        if command == "list":
            # list 명령은 추가 인자 불필요
            args = [sys.executable, str(global_command)] + new_args
        elif command == "register" and len(sys.argv) >= 3:
            args = [sys.executable, str(global_command)] + new_args + [sys.argv[2]]
        elif command == "send" and len(sys.argv) >= 5:
            # send <from> <to> <message> -> chat --to <to> <message>
            to_instance = sys.argv[3]
            message = " ".join(sys.argv[4:])
            args = [sys.executable, str(global_command), "chat", "--to", to_instance, message]
        elif command == "check" and len(sys.argv) >= 3:
            # check <instance> -> messages check (자동으로 현재 인스턴스 사용)
            print("⚠️  'check' 명령은 현재 등록된 인스턴스의 메시지를 확인합니다.")
            print("📌 먼저 'ipc register <instance_name>'으로 등록하세요.")
            args = [sys.executable, str(global_command)] + new_args
        elif command == "status":
            args = [sys.executable, str(global_command)] + new_args
        else:
            # 기타 명령은 그대로 전달
            args = [sys.executable, str(global_command)] + new_args + sys.argv[2:]

        # 경고 메시지 출력 (json 모드가 아닐 때만)
        if not json_output:
            print(f"⚠️  레거시 명령어 '{command}'가 새 명령어로 변환됩니다:")
            print(f"📌 {' '.join(args[2:])}")
            print()

        # 새 명령 실행
        try:
            result = subprocess.run(args, check=False)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ 명령 실행 실패: {e}")
            sys.exit(1)
    else:
        print(f"❌ 지원하지 않는 명령어: {command}")
        print()
        print("📌 새로운 통합 명령어를 사용하세요:")
        print(f"   uv run python {global_command} --help")
        sys.exit(1)

if __name__ == "__main__":
    main()
