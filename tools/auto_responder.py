#!/usr/bin/env python3
"""
Auto-responder for Claude instance
Automatically responds to certain requests from other instances
"""

import sqlite3
import time
import os
from pathlib import Path
from datetime import datetime

class AutoResponder:
    def __init__(self, instance_id="claude"):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_message_id = 0
        self.init_db()

    def init_db(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 마지막 메시지 ID 가져오기
        cursor.execute("SELECT MAX(id) FROM messages")
        result = cursor.fetchone()
        if result and result[0]:
            self.last_message_id = result[0]
            print(f"📊 초기화: 마지막 메시지 ID = {self.last_message_id}", flush=True)
        else:
            print("📊 초기화: 메시지 없음, ID = 0", flush=True)

        conn.close()

    def check_for_requests(self):
        """새로운 요청 메시지 확인"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Claude에게 온 새 메시지 확인
        cursor.execute('''
            SELECT id, from_id, content, timestamp
            FROM messages
            WHERE to_id = ? AND id > ?
            ORDER BY id ASC
        ''', (self.instance_id, self.last_message_id))

        messages = cursor.fetchall()

        # 디버그: 확인된 메시지 수 표시
        if messages:
            print(f"\n🔍 발견된 새 메시지: {len(messages)}개", flush=True)

        for msg_id, from_id, content, timestamp in messages:
            self.last_message_id = msg_id

            # 자기 자신에게서 온 메시지는 무시
            if from_id == self.instance_id:
                continue

            print(f"\n📥 받은 메시지 [{from_id}]: {content}", flush=True)

            # 요청 패턴 분석 및 응답
            response = self.generate_response(content, from_id)
            if response:
                self.send_response(from_id, response)
                print("✅ 자동 응답 완료!", flush=True)
            else:
                print("ℹ️ 자동 응답 패턴에 매칭되지 않음", flush=True)

        conn.close()

    def generate_response(self, content, from_id):
        """요청에 대한 자동 응답 생성"""
        content_lower = content.lower()

        # 파일 리스트 요청
        if "파일" in content and ("리스트" in content or "목록" in content):
            return self.get_file_list_response()

        # 상태 확인 요청
        elif "상태" in content or "status" in content_lower:
            return f"✅ Claude 인스턴스 정상 작동 중. 자동 응답 시스템 활성화됨. 현재 시간: {datetime.now().strftime('%H:%M:%S')}"

        # 도움말 요청
        elif "도움" in content or "help" in content_lower:
            return self.get_help_response()

        # 시스템 정보 요청
        elif "시스템" in content or "system" in content_lower:
            return self.get_system_info()

        # 인사말
        elif "안녕" in content or "hello" in content_lower or "hi" in content_lower:
            return f"👋 안녕하세요 {from_id}님! Claude 자동 응답 시스템입니다. 무엇을 도와드릴까요?"

        # 감사 인사
        elif "감사" in content or "고마" in content or "thanks" in content_lower:
            return f"😊 천만에요 {from_id}님! 언제든 도움이 필요하시면 말씀해주세요."

        # 테스트 메시지
        elif "테스트" in content or "test" in content_lower:
            return f"🧪 테스트 응답: 메시지 수신 및 자동 응답 정상 작동 확인! [from: {from_id}]"

        return None

    def get_file_list_response(self):
        """파일 리스트 응답 생성"""
        try:
            files = os.listdir("D:/claude-ipc-mcp")
            main_files = [f for f in files if f.endswith(('.py', '.md', '.bat', '.ps1'))][:10]
            return "📁 프로젝트 주요 파일:\n" + "\n".join([f"- {f}" for f in main_files])
        except OSError:
            return "📁 파일 리스트를 가져올 수 없습니다."

    def get_help_response(self):
        """도움말 응답"""
        return """📚 사용 가능한 명령:
- '파일 리스트' : 프로젝트 파일 목록
- '상태' 또는 'status' : 시스템 상태 확인
- '시스템 정보' : 시스템 정보
- '테스트' : 응답 테스트
- '도움말' 또는 'help' : 이 메시지"""

    def get_system_info(self):
        """시스템 정보 응답"""
        return f"""💻 시스템 정보:
- Instance: {self.instance_id}
- DB Path: {self.db_path}
- Auto-responder: Active
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

    def send_response(self, to_id, message):
        """응답 메시지 전송"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (self.instance_id, to_id, message, timestamp))

        conn.commit()
        conn.close()

        print(f"📤 응답 전송 [{to_id}]: {message}")

    def run(self):
        """자동 응답 시스템 실행"""
        print("🤖 Claude Auto-Responder 시작", flush=True)
        print(f"📁 Database: {self.db_path}", flush=True)
        print("=" * 60, flush=True)
        print("자동 응답 모드로 실행 중... (Ctrl+C로 종료)", flush=True)
        print("=" * 60, flush=True)

        try:
            check_count = 0
            while True:
                check_count += 1
                if check_count % 30 == 0:  # 1분마다 상태 표시
                    print(f"⏰ 상태: 실행 중... (확인 횟수: {check_count})", flush=True)
                self.check_for_requests()
                time.sleep(2)  # 2초마다 확인
        except KeyboardInterrupt:
            print("\n\n👋 Auto-Responder 종료", flush=True)

if __name__ == "__main__":
    responder = AutoResponder()
    responder.run()