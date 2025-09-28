#!/usr/bin/env python3
"""
개별 인스턴스 모니터링 프로그램
각 인스턴스의 메시지만 실시간으로 표시
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import os

class InstanceMonitor:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.messages = []
        self.max_messages = 20  # 화면에 표시할 최대 메시지 수

        # 인스턴스별 색상 설정
        self.colors = {
            'claude': '\033[92m',  # Green
            'gemini': '\033[96m',  # Cyan
            'codex': '\033[91m',   # Red
            'lm': '\033[93m'       # Yellow
        }
        self.reset_color = '\033[0m'

    def clear_screen(self):
        """화면 클리어"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_header_emoji(self):
        """인스턴스별 이모지 반환"""
        emojis = {
            'claude': '🤖',
            'gemini': '🧠',
            'codex': '💻',
            'lm': '📚'
        }
        return emojis.get(self.instance_id, '📡')

    def fetch_messages(self):
        """해당 인스턴스의 메시지 가져오기"""
        try:
            # 받은 메시지 가져오기
            result = subprocess.run(
                [sys.executable, "tools/ipc_manager.py", "check", self.instance_id],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            if result.stdout:
                lines = result.stdout.strip().split('\n')
                new_messages = []

                for i, line in enumerate(lines):
                    if '•' in line and '[' in line:
                        # 메시지 파싱
                        try:
                            # 타임스탬프와 발신자 추출
                            if '] ' in line:
                                timestamp_part = line.split('[')[1].split(']')[0]
                                time_str = timestamp_part[11:16] if len(timestamp_part) > 16 else "00:00"

                                # 발신자 추출
                                sender = line.split('] ')[-1].strip()
                                sender = sender.replace('• ', '').strip()

                                # 다음 줄에서 메시지 내용 가져오기
                                message = ""
                                if i + 1 < len(lines):
                                    next_line = lines[i + 1].strip()
                                    if next_line and not next_line.startswith('•'):
                                        message = next_line

                                if message:
                                    formatted_msg = f"[{time_str}] {sender}: {message}"
                                    new_messages.append(formatted_msg)
                        except:
                            pass

                # 메시지 업데이트 (최신 메시지만 유지)
                if new_messages:
                    self.messages = new_messages[-self.max_messages:]

        except Exception as e:
            pass

    def display(self):
        """메시지 표시"""
        self.clear_screen()

        # 헤더
        color = self.colors.get(self.instance_id, '')
        emoji = self.get_header_emoji()
        print(f"{color}{'='*60}{self.reset_color}")
        print(f"{color}{emoji} {self.instance_id.upper()} INSTANCE MONITOR{self.reset_color}")
        print(f"{color}{'='*60}{self.reset_color}")

        # 메시지 표시
        if self.messages:
            for msg in self.messages:
                # 메시지를 화면 너비에 맞게 자르기
                if len(msg) > 58:
                    print(f"{msg[:58]}...")
                else:
                    print(msg)
        else:
            print(f"\n📭 No messages for {self.instance_id}")

        # 하단 정보
        print(f"\n{color}{'='*60}{self.reset_color}")
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"⏰ {current_time} | 📊 Monitoring {self.instance_id} | 🛑 Ctrl+C to exit")
        print(f"{color}{'='*60}{self.reset_color}")

    def start(self):
        """모니터링 시작"""
        print(f"Starting monitor for {self.instance_id}...")

        # 데이터베이스 초기화
        subprocess.run([sys.executable, "tools/ipc_manager.py", "init"],
                      cwd=Path(__file__).parent.parent,
                      capture_output=True)

        # 인스턴스 등록
        subprocess.run([sys.executable, "tools/ipc_manager.py", "register", self.instance_id],
                      cwd=Path(__file__).parent.parent,
                      capture_output=True)

        # 모니터링 루프
        try:
            while True:
                self.fetch_messages()
                self.display()
                time.sleep(2)  # 2초마다 업데이트
        except KeyboardInterrupt:
            print(f"\n\nStopping monitor for {self.instance_id}...")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python monitor_instance.py <instance_id>")
        print("Example: python monitor_instance.py claude")
        sys.exit(1)

    instance_id = sys.argv[1]
    if instance_id not in ['claude', 'gemini', 'codex', 'lm']:
        print(f"Invalid instance ID: {instance_id}")
        print("Valid IDs: claude, gemini, codex, lm")
        sys.exit(1)

    monitor = InstanceMonitor(instance_id)
    monitor.start()
