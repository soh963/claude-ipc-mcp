#!/usr/bin/env python3
"""
Global IPC Command Interface

한 번 설치 후 모든 프로젝트에서 사용할 수 있는 글로벌 IPC 명령어 시스템
"""

import os
import sys
import argparse
import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

# IPC 베이스 경로 (환경 변수 또는 기본값)
IPC_BASE = os.environ.get('IPC_BASE', 'D:\\claude-ipc-mcp')

# IPC 베이스를 Python 경로에 추가
sys.path.insert(0, IPC_BASE)

from tools.project_utils import get_project_id, get_project_port
from tools.config_loader import load_project_config, save_project_config, create_default_config


class GlobalIPCCommand:
    """글로벌 IPC 명령어 인터페이스"""

    def __init__(self):
        self.ipc_base = Path(IPC_BASE)
        self.current_dir = Path.cwd()
        self.config_file = self.current_dir / '.ipc_project.yml'

    def init_project(self, minimal: bool = False) -> bool:
        """현재 프로젝트에 IPC 초기화"""
        print(f"\n🚀 IPC 초기화: {self.current_dir}")
        print(f"   IPC 베이스: {self.ipc_base}")

        # 1. 설정 파일 생성
        if not self.config_file.exists():
            print("\n📝 프로젝트 설정 생성 중...")
            config = create_default_config()
            save_project_config(config)

            project_id = get_project_id()
            project_port = get_project_port()

            print(f"   프로젝트 ID: {project_id}")
            print(f"   프로젝트 포트: {project_port}")
            print(f"   ✅ .ipc_project.yml 생성 완료")
        else:
            print("   ℹ️  설정 파일이 이미 존재합니다")

        if minimal:
            print("\n✅ 최소 설정 완료!")
            print("   이제 'ipc start'로 서버를 시작할 수 있습니다")
            return True

        # 2. 심볼릭 링크 생성 (선택사항)
        print("\n🔗 심볼릭 링크 생성 중...")

        # tools 링크
        tools_link = self.current_dir / 'tools'
        if not tools_link.exists():
            try:
                if os.name == 'nt':  # Windows
                    # Windows에서는 mklink 명령 사용
                    subprocess.run(
                        ['mklink', '/D', str(tools_link), str(self.ipc_base / 'tools')],
                        shell=True, check=True
                    )
                else:  # Unix/Mac
                    tools_link.symlink_to(self.ipc_base / 'tools')
                print(f"   ✅ tools/ 링크 생성")
            except Exception as e:
                print(f"   ⚠️  tools/ 링크 실패: {e}")
                print(f"      대신 다음 경로를 직접 사용하세요: {self.ipc_base / 'tools'}")

        # src 링크
        src_link = self.current_dir / 'src'
        if not src_link.exists():
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(
                        ['mklink', '/D', str(src_link), str(self.ipc_base / 'src')],
                        shell=True, check=True
                    )
                else:  # Unix/Mac
                    src_link.symlink_to(self.ipc_base / 'src')
                print(f"   ✅ src/ 링크 생성")
            except Exception as e:
                print(f"   ⚠️  src/ 링크 실패: {e}")

        print("\n✅ IPC 초기화 완료!")
        print("\n📝 다음 단계:")
        print("   1. ipc start        # IPC 서버 시작")
        print("   2. ipc register [ai_name]  # AI 등록")
        print("   3. ipc send [from] [to] 'message'  # 메시지 전송")

        return True

    def start_server(self) -> subprocess.Popen:
        """IPC 서버 시작"""
        if not self.config_file.exists():
            print("❌ 프로젝트가 초기화되지 않았습니다")
            print("   먼저 'ipc init'를 실행하세요")
            return None

        print(f"\n🚀 IPC 서버 시작 중...")

        # 현재 디렉토리에서 서버 실행 (프로젝트 ID 자동 감지)
        server_script = self.ipc_base / 'src' / 'claude_ipc_server.py'

        try:
            process = subprocess.Popen(
                [sys.executable, str(server_script)],
                cwd=str(self.current_dir)
            )
            print(f"✅ IPC 서버 시작됨 (PID: {process.pid})")
            print(f"   프로젝트: {self.current_dir}")
            print(f"   포트: {get_project_port()}")
            return process
        except Exception as e:
            print(f"❌ 서버 시작 실패: {e}")
            return None

    def stop_server(self) -> bool:
        """IPC 서버 중지"""
        print("\n🛑 IPC 서버 중지 중...")

        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'claude_ipc_server.py'],
                         capture_output=True)
        else:  # Unix/Mac
            subprocess.run(['pkill', '-f', 'claude_ipc_server'],
                         capture_output=True)

        print("✅ IPC 서버 중지됨")
        return True

    def register_ai(self, ai_name: str) -> bool:
        """AI 인스턴스 등록"""
        if not self.config_file.exists():
            print("❌ 프로젝트가 초기화되지 않았습니다")
            return False

        print(f"\n📝 {ai_name} 등록 중...")

        register_script = self.ipc_base / 'tools' / 'ipc_register.py'

        try:
            result = subprocess.run(
                [sys.executable, str(register_script), ai_name],
                cwd=str(self.current_dir),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ {ai_name} 등록 완료")
                return True
            else:
                print(f"❌ {ai_name} 등록 실패")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ 등록 실패: {e}")
            return False

    def send_message(self, from_ai: str, to_ai: str, message: str) -> bool:
        """메시지 전송"""
        if not self.config_file.exists():
            print("❌ 프로젝트가 초기화되지 않았습니다")
            return False

        send_script = self.ipc_base / 'tools' / 'ipc_send.py'

        try:
            result = subprocess.run(
                [sys.executable, str(send_script), from_ai, to_ai, message],
                cwd=str(self.current_dir),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ 메시지 전송 완료: {from_ai} → {to_ai}")
                return True
            else:
                print(f"❌ 메시지 전송 실패")
                return False
        except Exception as e:
            print(f"❌ 전송 실패: {e}")
            return False

    def check_messages(self, ai_name: str) -> bool:
        """메시지 확인"""
        if not self.config_file.exists():
            print("❌ 프로젝트가 초기화되지 않았습니다")
            return False

        check_script = self.ipc_base / 'tools' / 'ipc_check.py'

        try:
            subprocess.run(
                [sys.executable, str(check_script), ai_name],
                cwd=str(self.current_dir)
            )
            return True
        except Exception as e:
            print(f"❌ 메시지 확인 실패: {e}")
            return False

    def list_instances(self) -> bool:
        """인스턴스 목록"""
        if not self.config_file.exists():
            print("❌ 프로젝트가 초기화되지 않았습니다")
            return False

        list_script = self.ipc_base / 'tools' / 'ipc_list.py'

        try:
            subprocess.run(
                [sys.executable, str(list_script)],
                cwd=str(self.current_dir)
            )
            return True
        except Exception as e:
            print(f"❌ 목록 조회 실패: {e}")
            return False

    def health_check(self) -> bool:
        """상태 점검"""
        if not self.config_file.exists():
            print("❌ 프로젝트가 초기화되지 않았습니다")
            return False

        health_script = self.ipc_base / 'tools' / 'ipc_health_check.py'

        try:
            subprocess.run(
                [sys.executable, str(health_script)],
                cwd=str(self.current_dir)
            )
            return True
        except Exception as e:
            print(f"❌ 상태 점검 실패: {e}")
            return False

    def auto_register_all(self) -> bool:
        """모든 AI 자동 등록"""
        if not self.config_file.exists():
            print("❌ 프로젝트가 초기화되지 않았습니다")
            return False

        print("\n🤖 모든 AI 인스턴스 등록 중...")

        auto_register_script = self.ipc_base / 'tools' / 'auto_register_all.py'

        try:
            subprocess.run(
                [sys.executable, str(auto_register_script)],
                cwd=str(self.current_dir)
            )
            return True
        except Exception as e:
            print(f"❌ 자동 등록 실패: {e}")
            return False


def main():
    """메인 진입점"""
    parser = argparse.ArgumentParser(
        description="글로벌 IPC 명령어 인터페이스 - 어디서든 IPC 사용",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  ipc init              # 현재 프로젝트 IPC 초기화
  ipc init --minimal    # 최소 설정만 (설정 파일만 생성)
  ipc start             # IPC 서버 시작
  ipc stop              # IPC 서버 중지
  ipc register claude   # Claude 인스턴스 등록
  ipc register-all      # 모든 AI 자동 등록
  ipc send claude gemini "Hello"  # 메시지 전송
  ipc check claude      # 메시지 확인
  ipc list              # 활성 인스턴스 목록
  ipc health            # 시스템 상태 점검
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')

    # init 명령
    init_parser = subparsers.add_parser('init', help='현재 프로젝트 IPC 초기화')
    init_parser.add_argument('--minimal', action='store_true',
                            help='최소 설정만 (설정 파일만 생성)')

    # start 명령
    subparsers.add_parser('start', help='IPC 서버 시작')

    # stop 명령
    subparsers.add_parser('stop', help='IPC 서버 중지')

    # register 명령
    register_parser = subparsers.add_parser('register', help='AI 인스턴스 등록')
    register_parser.add_argument('ai_name', help='AI 인스턴스 이름')

    # register-all 명령
    subparsers.add_parser('register-all', help='모든 AI 자동 등록')

    # send 명령
    send_parser = subparsers.add_parser('send', help='메시지 전송')
    send_parser.add_argument('from_ai', help='발신 AI')
    send_parser.add_argument('to_ai', help='수신 AI')
    send_parser.add_argument('message', help='메시지 내용')

    # check 명령
    check_parser = subparsers.add_parser('check', help='메시지 확인')
    check_parser.add_argument('ai_name', help='AI 인스턴스 이름')

    # list 명령
    subparsers.add_parser('list', help='활성 인스턴스 목록')

    # health 명령
    subparsers.add_parser('health', help='시스템 상태 점검')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 글로벌 IPC 명령어 실행
    ipc = GlobalIPCCommand()

    try:
        if args.command == 'init':
            ipc.init_project(minimal=args.minimal)
        elif args.command == 'start':
            ipc.start_server()
        elif args.command == 'stop':
            ipc.stop_server()
        elif args.command == 'register':
            ipc.register_ai(args.ai_name)
        elif args.command == 'register-all':
            ipc.auto_register_all()
        elif args.command == 'send':
            ipc.send_message(args.from_ai, args.to_ai, args.message)
        elif args.command == 'check':
            ipc.check_messages(args.ai_name)
        elif args.command == 'list':
            ipc.list_instances()
        elif args.command == 'health':
            ipc.health_check()
        else:
            print(f"❌ 알 수 없는 명령어: {args.command}")
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⚠️  작업이 사용자에 의해 중단되었습니다")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()