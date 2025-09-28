#!/usr/bin/env python3
"""
Windows Terminal을 4분할하여 각 인스턴스별 모니터링 실행
"""

import subprocess
import sys
import json
import time
from pathlib import Path

def create_wt_split_command():
    """Windows Terminal 4분할 명령어 생성"""

    # 각 인스턴스별 대화형 클라이언트 명령어
    claude_cmd = f'python tools/interactive_client.py claude'
    gemini_cmd = f'python tools/interactive_client.py gemini'
    codex_cmd = f'python tools/interactive_client.py codex'
    lm_cmd = f'python tools/interactive_client.py lm'

    # Windows Terminal 분할 명령어 구성
    # wt 명령어로 4개 패널 생성
    wt_command = [
        'wt',
        # 첫 번째 탭에서 4분할
        'new-tab', '--title', 'IPC Interactive',
        '--suppressApplicationTitle',
        ';',
        # Claude 패널 (왼쪽 상단)
        'split-pane', '-H', '-p', 'Claude', 'cmd', '/k', claude_cmd,
        ';',
        # Gemini 패널 (오른쪽 상단)
        'split-pane', '-V', '-p', 'Gemini', '-t', '0', 'cmd', '/k', gemini_cmd,
        ';',
        # Codex 패널 (왼쪽 하단)
        'split-pane', '-V', '-p', 'Codex', '-t', '1', 'cmd', '/k', codex_cmd,
        ';',
        # LM 패널 (오른쪽 하단)
        'split-pane', '-H', '-p', 'LM', '-t', '2', 'cmd', '/k', lm_cmd
    ]

    return wt_command

def start_split_terminal():
    """Windows Terminal 4분할 실행"""

    print("🚀 Claude IPC MCP - Windows Terminal 4분할 모니터링")
    print("="*60)

    # 데이터베이스 초기화
    print("📊 데이터베이스 초기화 중...")
    subprocess.run([sys.executable, "tools/ipc_manager.py", "init"])

    # 인스턴스 등록
    instances = ["claude", "gemini", "codex", "lm"]
    print("\n📝 인스턴스 등록 중...")
    for instance_id in instances:
        subprocess.run([sys.executable, "tools/ipc_manager.py", "register", instance_id])

    print("\n✅ 시스템 준비 완료!")
    print("\n🖥️ Windows Terminal 4분할 모니터링을 시작합니다...")
    print("   • 왼쪽 상단: Claude")
    print("   • 오른쪽 상단: Gemini")
    print("   • 왼쪽 하단: Codex")
    print("   • 오른쪽 하단: LM")
    print("\n" + "="*60)

    # Windows Terminal 실행
    try:
        # 방법 1: wt.exe 직접 실행
        wt_cmd = create_wt_split_command()
        subprocess.run(wt_cmd, shell=True)
    except FileNotFoundError:
        # 방법 2: PowerShell을 통한 실행
        print("⚠️ wt.exe를 직접 실행할 수 없습니다. PowerShell을 사용합니다...")

        ps_script = """
        wt new-tab --title 'IPC Interactive' `; `
        split-pane -H -p 'Claude' cmd /k 'python tools/interactive_client.py claude' `; `
        split-pane -V -p 'Gemini' -t 0 cmd /k 'python tools/interactive_client.py gemini' `; `
        split-pane -V -p 'Codex' -t 1 cmd /k 'python tools/interactive_client.py codex' `; `
        split-pane -H -p 'LM' -t 2 cmd /k 'python tools/interactive_client.py lm'
        """

        subprocess.run(['powershell', '-Command', ps_script])

    print("\n✅ Windows Terminal 4분할 모니터링이 시작되었습니다!")
    print("\n📌 사용법:")
    print("   • 각 패널에서 해당 인스턴스의 메시지가 실시간으로 표시됩니다")
    print("   • 다른 터미널에서 메시지 보내기:")
    print("     python tools/ipc_manager.py send [from] [to] [message]")
    print("   • 종료: 각 패널에서 Ctrl+C")

if __name__ == "__main__":
    start_split_terminal()