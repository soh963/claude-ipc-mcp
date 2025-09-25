#!/usr/bin/env python3
"""
대화형 IPC 클라이언트 - 자연스러운 명령어 지원
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import threading
import queue

class InteractiveClient:
    def __init__(self):
        self.instance_id = None
        self.message_queue = queue.Queue()
        self.running = True

    def clear_screen(self):
        """화면 클리어"""
        subprocess.run('cls' if sys.platform == 'win32' else 'clear', shell=True)

    def get_color(self, instance_id=None):
        """인스턴스별 색상"""
        colors = {
            'claude': '\033[96m',  # Cyan
            'gemini': '\033[93m',  # Yellow
            'codex': '\033[92m',   # Green
            'lm': '\033[95m'       # Magenta
        }
        return colors.get(instance_id or self.instance_id, '\033[97m')

    def register(self, name):
        """인스턴스 등록"""
        # 유효한 인스턴스 이름인지 확인
        valid_names = ['claude', 'gemini', 'codex', 'lm']
        if name.lower() not in valid_names:
            print(f"❌ Invalid instance name: '{name}'")
            print(f"   Valid names are: {', '.join(valid_names)}")
            return False

        self.instance_id = name.lower()
        result = subprocess.run(
            [sys.executable, "ipc_manager.py", "register", self.instance_id],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        # 등록 결과 확인
        if "등록되어 있습니다" in result.stdout:
            print(f"✅ Already registered as '{self.instance_id}'")
            return True
        elif "등록 완료" in result.stdout or "✅" in result.stdout:
            print(f"✅ Successfully registered as '{self.instance_id}'")
            return True
        else:
            print(f"❌ Failed to register as '{self.instance_id}'")
            self.instance_id = None
            return False

    def send_message(self, target, message):
        """메시지 전송"""
        if not self.instance_id:
            print("❌ Please register first! Use: Register this instance as [name]")
            return

        result = subprocess.run(
            [sys.executable, "ipc_manager.py", "send", self.instance_id, target, message],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        if "전송 완료" in result.stdout:
            print(f"✅ Message sent to {target}: {message}")
        else:
            print(f"❌ Failed to send message")

    def check_messages(self):
        """메시지 확인"""
        if not self.instance_id:
            print("❌ Please register first!")
            return

        result = subprocess.run(
            [sys.executable, "ipc_manager.py", "show-all"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        # 메시지 파싱
        lines = result.stdout.strip().split('\n')
        new_messages = []

        for line in lines:
            if '→' in line and self.instance_id in line:
                if f'→ {self.instance_id}' in line:
                    # 받은 메시지
                    try:
                        sender = line.split('→')[0].split('] ')[-1].strip()
                        msg_parts = line.split('\n')
                        if len(msg_parts) > 1:
                            message = msg_parts[1].strip()
                            new_messages.append(f"📥 From {sender}: {message}")
                    except:
                        pass

        if new_messages:
            print("\n📬 New messages:")
            for msg in new_messages:
                print(f"  {msg}")
        else:
            print("📭 No new messages")

    def list_instances(self):
        """인스턴스 목록"""
        result = subprocess.run(
            [sys.executable, "ipc_manager.py", "list"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        # 인스턴스 파싱
        lines = result.stdout.strip().split('\n')
        instances = []

        for line in lines:
            if '• ' in line:
                # 인스턴스 이름 추출
                try:
                    instance_name = line.split('• ')[1].strip().split('\n')[0].split()[0]
                    instances.append(instance_name)
                except:
                    pass

        if instances:
            print("\n👥 Online instances:")
            for inst in instances:
                status = "🟢" if inst != self.instance_id else "🔵 (You)"
                print(f"  {status} {inst}")
        else:
            print("❌ No instances online")

    def show_help(self):
        """도움말 표시"""
        color = self.get_color()
        reset = '\033[0m'

        print(f"\n{color}📖 Available Commands:{reset}")
        print("-" * 50)
        print("📝 Registration:")
        print("  Register this instance as [name]    - Set your name")
        print("  Example: Register this instance as claude")
        print()
        print("💬 Messaging:")
        print("  Send message to [name]: [message]   - Send a message")
        print("  Example: Send message to gemini: Hello!")
        print()
        print("📥 Inbox:")
        print("  Check messages                      - Check your inbox")
        print("  Check                               - Short version")
        print()
        print("👥 Status:")
        print("  List instances                      - See who's online")
        print("  List                               - Short version")
        print("  Who                                - Alternative")
        print()
        print("🔧 System:")
        print("  Help                               - Show this help")
        print("  Clear                              - Clear screen")
        print("  Exit/Quit                          - Exit the client")
        print("-" * 50)

    def parse_command(self, command):
        """명령어 파싱"""
        cmd = command.strip().lower()

        # Registration
        if cmd.startswith("register this instance as "):
            name = command[26:].strip()
            self.register(name)

        # Send message
        elif cmd.startswith("send message to "):
            parts = command[16:].split(':', 1)
            if len(parts) == 2:
                target = parts[0].strip()
                message = parts[1].strip()
                self.send_message(target, message)
            else:
                print("❌ Invalid format. Use: Send message to [name]: [message]")

        # Check messages
        elif cmd in ["check messages", "check", "inbox"]:
            self.check_messages()

        # List instances
        elif cmd in ["list instances", "list", "who", "who's online"]:
            self.list_instances()

        # Help
        elif cmd in ["help", "?", "h"]:
            self.show_help()

        # Clear
        elif cmd in ["clear", "cls"]:
            self.clear_screen()

        # Exit
        elif cmd in ["exit", "quit", "bye", "q"]:
            return False

        else:
            print(f"❌ Unknown command: {command}")
            print("💡 Type 'help' for available commands")

        return True

    def run(self):
        """메인 실행 루프"""
        self.clear_screen()

        # 헤더
        print("=" * 60)
        print("🚀 Claude IPC Interactive Client")
        print("=" * 60)
        print()

        # 자동 등록 (파라미터가 있을 경우)
        if len(sys.argv) > 1:
            suggested_name = sys.argv[1]
            print(f"💡 Auto-registering as '{suggested_name}'...")
            if self.register(suggested_name):
                print(f"✅ Successfully registered as '{suggested_name}'")
            else:
                print(f"⚠️ Using existing registration for '{suggested_name}'")
            print()
        else:
            print("Welcome! Please register your instance first.")
            print("Type 'help' for available commands.")
            print()

        # 명령어 루프
        while self.running:
            try:
                # 프롬프트
                if self.instance_id:
                    color = self.get_color()
                    reset = '\033[0m'
                    prompt = f"{color}[{self.instance_id}]{reset} > "
                else:
                    prompt = "[unregistered] > "

                # 입력 받기
                command = input(prompt)

                # 명령어 처리
                if not self.parse_command(command):
                    break

            except KeyboardInterrupt:
                print("\n\n🔕 Exiting...")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        print("Goodbye! 👋")

if __name__ == "__main__":
    client = InteractiveClient()
    client.run()