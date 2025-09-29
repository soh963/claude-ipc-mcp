#!/usr/bin/env python3
"""
특정 인스턴스의 메시지만 실시간 모니터링
"""

import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

def clear_screen():
    """화면 클리어"""
    subprocess.run('cls' if sys.platform == 'win32' else 'clear', shell=True)

def get_instance_color(instance_id):
    """인스턴스별 색상 코드"""
    colors = {
        'claude': '\033[96m',  # Cyan
        'gemini': '\033[93m',  # Yellow
        'codex': '\033[92m',   # Green
        'lm': '\033[95m'       # Magenta
    }
    return colors.get(instance_id, '\033[97m')  # Default white

def get_instance_emoji(instance_id):
    """인스턴스별 이모지"""
    emojis = {
        'claude': '🤖',
        'gemini': '🧠',
        'codex': '💻',
        'lm': '📚'
    }
    return emojis.get(instance_id, '📧')

def monitor_instance(instance_id):
    """특정 인스턴스의 메시지 모니터링"""

    color = get_instance_color(instance_id)
    emoji = get_instance_emoji(instance_id)
    reset = '\033[0m'

    print(f"{color}{emoji} {instance_id.upper()} Instance Monitor{reset}")
    print("="*50)
    print(f"인스턴스: {instance_id}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    print()

    last_messages = []

    while True:
        try:
            # 모든 메시지 가져오기
            result = subprocess.run(
                [sys.executable, "ipc_manager.py", "show-all"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )

            if result.stdout:
                # 메시지 파싱 - 다중 라인 메시지 처리 개선
                lines = result.stdout.strip().split('\n')
                instance_messages = []

                i = 0
                while i < len(lines):
                    line = lines[i]
                    # 해당 인스턴스 관련 메시지만 필터링
                    if '→' in line and '• [' in line:
                        if f'→ {instance_id}' in line or f'{instance_id} →' in line:
                            # 타임스탬프와 메시지 추출
                            try:
                                # 타임스탬프 추출
                                timestamp_part = line.split('[')[1].split(']')[0] if '[' in line else ""

                                # 발신자와 수신자 파싱
                                parts = line.split('→', 1)
                                if len(parts) >= 2:
                                    sender_part = parts[0].split('] ')[-1].strip() if '] ' in parts[0] else parts[0].strip()
                                    receiver_part = parts[1].strip()

                                    # 다음 줄에서 실제 메시지 내용 가져오기
                                    msg_content = ""
                                    if i + 1 < len(lines):
                                        next_line = lines[i + 1]
                                        # 다음 줄이 새로운 메시지가 아니면 내용으로 처리
                                        if not (next_line.startswith('•') or '→' in next_line):
                                            msg_content = next_line.strip()
                                            i += 1  # 메시지 내용 줄 건너뛰기

                                    # 발신/수신 방향 결정
                                    if sender_part == instance_id:
                                        # 이 인스턴스가 발신자
                                        direction = "📤 송신"
                                        target = receiver_part
                                    elif receiver_part == instance_id:
                                        # 이 인스턴스가 수신자
                                        direction = "📥 수신"
                                        target = sender_part
                                    else:
                                        i += 1
                                        continue

                                    # 메시지가 없으면 receiver_part에서 추출 시도
                                    if not msg_content and ':' in receiver_part:
                                        parts = receiver_part.split(':', 1)
                                        target = parts[0].strip()
                                        msg_content = parts[1].strip() if len(parts) > 1 else ""

                                    instance_messages.append({
                                        'time': timestamp_part,
                                        'direction': direction,
                                        'sender': sender_part,
                                        'receiver': receiver_part if direction == "📤 송신" else instance_id,
                                        'target': target,
                                        'message': msg_content or "(메시지 내용 없음)"
                                    })
                            except Exception:
                                pass
                    i += 1

                # 새 메시지가 있으면 화면 업데이트
                if instance_messages != last_messages:
                    clear_screen()
                    print(f"{color}{emoji} {instance_id.upper()} Instance Monitor{reset}")
                    print("="*50)

                    # 최근 15개 메시지만 표시
                    recent_messages = instance_messages[-15:] if len(instance_messages) > 15 else instance_messages

                    for msg in recent_messages:
                        # 방향에 따른 색상
                        if msg['direction'] == "📤 송신":
                            dir_color = '\033[92m'  # Green for sent
                        else:
                            dir_color = '\033[94m'  # Blue for received

                        # 시간 포맷 (짧게)
                        time_str = msg['time'][11:16] if len(msg['time']) > 16 else msg['time']

                        print(f"{dir_color}[{time_str}] {msg['direction']}{reset}")

                        # 전체 메시지 내용 표시 (줄바꿈 포함)
                        if msg['direction'] == "📤 송신":
                            print(f"  → {msg['target']}")
                            print(f"  💬 {msg['message']}")
                        else:
                            print(f"  ← {msg['sender']}")
                            print(f"  💬 {msg['message']}")
                        print("-" * 50)

                    print("="*50)
                    print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | 📊 모니터링 중...")
                    print("🛑 종료: Ctrl+C")

                    last_messages = instance_messages

            time.sleep(1)  # 1초마다 업데이트

        except KeyboardInterrupt:
            print(f"\n\n{color}🔕 {instance_id.upper()} 모니터링을 종료합니다...{reset}")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python monitor_instance.py [instance_id]")
        print("예시: python monitor_instance.py claude")
        sys.exit(1)

    instance_id = sys.argv[1].lower()

    if instance_id not in ['claude', 'gemini', 'codex', 'lm']:
        print(f"❌ 알 수 없는 인스턴스: {instance_id}")
        print("사용 가능한 인스턴스: claude, gemini, codex, lm")
        sys.exit(1)

    monitor_instance(instance_id)