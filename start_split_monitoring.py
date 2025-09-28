#!/usr/bin/env python3
"""
단일 터미널에서 화면 분할로 모든 인스턴스를 모니터링
"""

import subprocess
import sys
import time
from pathlib import Path
import threading
import queue
from datetime import datetime

class SplitMonitor:
    def __init__(self):
        self.instances = ["claude", "gemini", "codex", "lm"]
        self.message_queues = {instance: queue.Queue(maxsize=10) for instance in self.instances}
        self.message_storage = {instance: [] for instance in self.instances}  # 메시지 저장소
        self.running = True

    def clear_screen(self):
        """화면 클리어"""
        print("\033[2J\033[H", end="")

    def draw_border(self, width=60):
        """경계선 그리기"""
        return "=" * width

    def format_message(self, msg, max_width=55):
        """메시지 포맷팅"""
        if len(msg) > max_width:
            return msg[:max_width-3] + "..."
        return msg.ljust(max_width)

    def fetch_messages(self):
        """메시지 가져오기 스레드"""
        while self.running:
            try:
                # 모든 메시지 가져오기
                result = subprocess.run(
                    [sys.executable, "tools/ipc_manager.py", "show-all"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent
                )

                if result.stdout:
                    lines = result.stdout.strip().split('\n')

                    # 각 인스턴스별로 메시지 분류
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        if '→' in line and '• [' in line:
                            # 메시지 파싱
                            try:
                                parts = line.split('→', 1)
                                if len(parts) == 2:
                                    from_part = parts[0].split('] ')[-1].strip()
                                    to_part = parts[1].strip()

                                    # 다음 줄에서 메시지 내용 가져오기
                                    message_content = ""
                                    if i + 1 < len(lines):
                                        next_line = lines[i + 1]
                                        if not next_line.startswith('•'):
                                            message_content = next_line.strip()
                                            i += 1  # 메시지 내용 줄을 건너뛰기

                                    # 타임스탬프 추출
                                    timestamp = line.split('[')[1].split(']')[0][11:16] if '[' in line else ""

                                    # 메시지 포맷팅
                                    formatted_msg = f"[{timestamp}] {from_part} → {to_part}: {message_content}"

                                    # 각 인스턴스의 저장소에 메시지 추가
                                    for instance in self.instances:
                                        if to_part == instance:  # 수신자 기준으로 메시지 분류
                                            # 최대 10개만 유지 (오래된 것 제거)
                                            self.message_storage[instance].append(formatted_msg)
                                            if len(self.message_storage[instance]) > 10:
                                                self.message_storage[instance] = self.message_storage[instance][-10:]
                                            break
                            except:
                                pass
                        i += 1

                time.sleep(1)  # 1초마다 업데이트

            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                time.sleep(2)

    def display_split_screen(self):
        """4분할 화면 표시"""
        while self.running:
            try:
                self.clear_screen()

                # 헤더
                print("╔" + "═" * 118 + "╗")
                print("║" + " " * 45 + "Claude IPC MCP - Split Monitor" + " " * 43 + "║")
                print("╠" + "═" * 58 + "╦" + "═" * 59 + "╣")

                # 상단 두 패널 (claude, gemini)
                # 저장된 메시지 가져오기 (최근 8개)
                claude_msgs = self.message_storage["claude"][-8:] if self.message_storage["claude"] else []
                gemini_msgs = self.message_storage["gemini"][-8:] if self.message_storage["gemini"] else []

                # Claude 패널 | Gemini 패널
                print("║ 🤖 CLAUDE" + " " * 48 + "║ 🧠 GEMINI" + " " * 49 + "║")
                print("╠" + "─" * 58 + "╬" + "─" * 59 + "╣")

                for i in range(8):
                    claude_line = ""
                    gemini_line = ""

                    if i < len(claude_msgs):
                        msg = claude_msgs[i]
                        # 메시지가 이미 포맷팅된 형태로 저장되어 있음
                        # [시간] 발신자 → 수신자: 메시지내용
                        if len(msg) > 58:
                            claude_line = " " + msg[:57]
                        else:
                            claude_line = " " + msg

                    if i < len(gemini_msgs):
                        msg = gemini_msgs[i]
                        if len(msg) > 58:
                            gemini_line = " " + msg[:57]
                        else:
                            gemini_line = " " + msg

                    print("║" + self.format_message(claude_line, 58) + "║" +
                          self.format_message(gemini_line, 59) + "║")

                # 중간 구분선
                print("╠" + "═" * 58 + "╬" + "═" * 59 + "╣")

                # 하단 두 패널 (codex, lm)
                # 저장된 메시지 가져오기 (최근 8개)
                codex_msgs = self.message_storage["codex"][-8:] if self.message_storage["codex"] else []
                lm_msgs = self.message_storage["lm"][-8:] if self.message_storage["lm"] else []

                # Codex 패널 | LM 패널
                print("║ 💻 CODEX" + " " * 49 + "║ 📚 LM" + " " * 53 + "║")
                print("╠" + "─" * 58 + "╬" + "─" * 59 + "╣")

                for i in range(8):
                    codex_line = ""
                    lm_line = ""

                    if i < len(codex_msgs):
                        msg = codex_msgs[i]
                        if len(msg) > 58:
                            codex_line = " " + msg[:57]
                        else:
                            codex_line = " " + msg

                    if i < len(lm_msgs):
                        msg = lm_msgs[i]
                        if len(msg) > 58:
                            lm_line = " " + msg[:57]
                        else:
                            lm_line = " " + msg

                    print("║" + self.format_message(codex_line, 58) + "║" +
                          self.format_message(lm_line, 59) + "║")

                # 하단 정보
                print("╠" + "═" * 118 + "╣")
                current_time = datetime.now().strftime("%H:%M:%S")
                status_msg = f"⏰ {current_time} | 📊 모니터링 중... | 🛑 종료: Ctrl+C"
                padding = (118 - len(status_msg)) // 2
                print("║" + " " * padding + status_msg + " " * (118 - padding - len(status_msg)) + "║")
                print("╚" + "═" * 118 + "╝")

                # 명령어 가이드
                print("\n📌 다른 터미널에서 메시지 보내기: python tools/ipc_manager.py send [from] [to] [message]")

                time.sleep(2)  # 2초마다 화면 업데이트

            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(2)

    def start(self):
        """모니터링 시작"""
        print("🚀 Claude IPC MCP - Split Screen Monitor")
        print("=" * 60)
        print("초기화 중...")

        # 데이터베이스 초기화
        subprocess.run([sys.executable, "tools/ipc_manager.py", "init"])

        # 인스턴스 등록
        for instance_id in self.instances:
            subprocess.run([sys.executable, "tools/ipc_manager.py", "register", instance_id])

        print("✅ 시스템 준비 완료!")
        time.sleep(2)

        # 메시지 가져오기 스레드 시작
        fetch_thread = threading.Thread(target=self.fetch_messages)
        fetch_thread.daemon = True
        fetch_thread.start()

        # 화면 표시 시작
        try:
            self.display_split_screen()
        except KeyboardInterrupt:
            self.running = False
            print("\n\n🔕 모니터링을 종료합니다...")

if __name__ == "__main__":
    monitor = SplitMonitor()
    monitor.start()