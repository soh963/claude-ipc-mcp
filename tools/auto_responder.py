#!/usr/bin/env python3
"""
Auto-responder for IPC instances
Automatically responds to certain requests from other instances.

Usage:
    python tools/auto_responder.py               # defaults to instance_id="claude"
    python tools/auto_responder.py gemini        # respond as "gemini"

Also supports environment variable fallback:
    set IPC_INSTANCE_ID=codex
    python tools/auto_responder.py
"""

import sqlite3
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import json


class AutoResponder:
    def __init__(self, instance_id="claude"):
        self.instance_id = instance_id
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.last_message_id = 0
        self.policy = os.getenv("IPC_RESPONDER_POLICY", "simple").lower()
        # status metadata
        try:
            self.status_dir = Path(os.path.expandvars(r"%USERPROFILE%\.claude-ipc-data")) / "responders"
        except Exception:
            self.status_dir = Path.home() / ".claude-ipc-data" / "responders"
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self.status_path = self.status_dir / f"{self.instance_id}.json"
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.last_check_at = None
        self.last_response_at = None
        self.init_db()
        # write initial status
        self._write_status(last_check=True)

    def init_db(self):
        """데이터베이스 초기화 (테이블 준비 전에도 안전)"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=2.0)
            cursor = conn.cursor()
            # Best-effort pragmas to reduce contention and improve read performance
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute("PRAGMA busy_timeout=2000;")
            except Exception:
                pass

            # 마지막 메시지 ID 가져오기
            cursor.execute("SELECT MAX(id) FROM messages")
            result = cursor.fetchone()
            if result and result[0]:
                self.last_message_id = result[0]
                print(f"📊 초기화: 마지막 메시지 ID = {self.last_message_id}", flush=True)
            else:
                print("📊 초기화: 메시지 없음, ID = 0", flush=True)
            # Optional: create indexes to optimize typical queries
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_to_id ON messages(to_id, id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_from_id ON messages(from_id, id)")
                conn.commit()
            except Exception:
                pass
        except sqlite3.OperationalError as e:
            # 서버가 DB/테이블을 아직 만들지 않은 초기 상태를 고려
            print(f"⏳ DB 준비 대기 중(테이블 미생성 가능): {e}", flush=True)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def check_for_requests(self):
        """새로운 요청 메시지 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 나에게 온 새 메시지 확인
            cursor.execute(
                """
                SELECT id, from_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND id > ?
                ORDER BY id ASC
            """,
                (self.instance_id, self.last_message_id),
            )

            messages = cursor.fetchall()

            # 디버그: 확인된 메시지 수 표시
            if messages:
                print(f"\n🔍 발견된 새 메시지: {len(messages)}개", flush=True)

            import re
            for msg_id, from_id, content, timestamp in messages:
                self.last_message_id = msg_id

                # 자기 자신에게서 온 메시지는 무시
                if from_id == self.instance_id:
                    continue

                print(f"\n📥 받은 메시지 [{from_id}]: {content}", flush=True)

                # 요청 패턴 분석 및 응답
                # Extract correlation token if present to echo back
                corr = None
                try:
                    m = re.search(r"\[corr=([^\]]+)\]", content or "")
                    if m:
                        corr = m.group(1)
                except Exception:
                    corr = None

                response = self.generate_response(content, from_id)
                if response:
                    if corr and f"[corr={corr}]" not in response:
                        response = f"{response} [corr={corr}]"
                    self.send_response(from_id, response)
                    print("✅ 자동 응답 완료!", flush=True)
                else:
                    print("ℹ️ 자동 응답 패턴에 매칭되지 않음", flush=True)
        except sqlite3.OperationalError as e:
            # DB/테이블 미생성 상황에서 잠시 대기 후 재시도
            print(f"⏳ DB 준비 대기 중: {e}", flush=True)
        finally:
            try:
                conn.close()
            except Exception:
                pass
        # update last_check_at after each scan
        try:
            self.last_check_at = datetime.now().isoformat(timespec="seconds")
            self._write_status()
        except Exception:
            pass

    def generate_response(self, content, from_id):
        """요청에 대한 자동 응답 생성"""
        content_lower = content.lower()
        # Correlation token pass-through
        import re as _re
        corr_match = _re.search(r"\[corr=([^\]]+)\]", content)
        corr_suffix = f" [corr={corr_match.group(1)}]" if corr_match else ""

        # 파일 리스트 요청
        if "파일" in content and ("리스트" in content or "목록" in content):
            return self.get_file_list_response()

        # 상태 확인 요청
        elif "상태" in content or "status" in content_lower:
            return (
                f"✅ Claude 인스턴스 정상 작동 중. 자동 응답 시스템 활성화됨. 현재 시간: "
                f"{datetime.now().strftime('%H:%M:%S')}" + corr_suffix
            )

        # 도움말 요청
        elif "도움" in content or "help" in content_lower:
            return self.get_help_response()

        # 시스템 정보 요청
        elif "시스템" in content or "system" in content_lower:
            return self.get_system_info()

        # 인사말
        elif "안녕" in content or "hello" in content_lower or "hi" in content_lower:
            return (
                f"👋 안녕하세요 {from_id}님! Claude 자동 응답 시스템입니다. 무엇을 도와드릴까요?"
                + corr_suffix
            )

        # 감사 인사
        elif "감사" in content or "고마" in content or "thanks" in content_lower:
            return (
                f"😊 천만에요 {from_id}님! 언제든 도움이 필요하시면 말씀해주세요."
                + corr_suffix
            )

        # 테스트 메시지
        elif "테스트" in content or "test" in content_lower:
            return (
                f"🧪 테스트 응답: 메시지 수신 및 자동 응답 정상 작동 확인! [from: {from_id}]"
                + corr_suffix
            )

        return None

    def get_file_list_response(self):
        """파일 리스트 응답 생성"""
        try:
            files = os.listdir("D:/claude-ipc-mcp")
            main_files = [f for f in files if f.endswith((".py", ".md", ".bat", ".ps1"))][:10]
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

        cursor.execute(
            """
            INSERT INTO messages (from_id, to_id, content, timestamp)
            VALUES (?, ?, ?, ?)
        """,
            (self.instance_id, to_id, message, timestamp),
        )

        conn.commit()
        conn.close()

        print(f"📤 응답 전송 [{to_id}]: {message}")
        # update status for last response
        try:
            self.last_response_at = datetime.now().isoformat(timespec="seconds")
            self._write_status()
        except Exception:
            pass

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
                # 정책에 따라 폴링 주기 조정
                if self.policy == "smart":
                    time.sleep(0.8)
                else:
                    time.sleep(2)  # 2초마다 확인
        except KeyboardInterrupt:
            print("\n\n👋 Auto-Responder 종료", flush=True)

    def _write_status(self, last_check: bool = False):
        """Write a small JSON status file used by responder_proc for status queries."""
        payload = {
            "instance_id": self.instance_id,
            "policy": self.policy,
            "started_at": self.started_at,
            "last_check_at": self.last_check_at,
            "last_response_at": self.last_response_at,
        }
        if last_check:
            payload["last_check_at"] = datetime.now().isoformat(timespec="seconds")
            self.last_check_at = payload["last_check_at"]
        try:
            self.status_path.write_text(json.dumps(payload), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    # 인스턴스 ID 우선순위: CLI 인자 > 환경변수 > 기본값("claude")
    instance = None
    if len(sys.argv) > 1 and sys.argv[1] not in ("-h", "--help"):
        instance = sys.argv[1]
    elif os.getenv("IPC_INSTANCE_ID"):
        instance = os.getenv("IPC_INSTANCE_ID")
    else:
        instance = "claude"

    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(
            "Usage: python tools/auto_responder.py [INSTANCE_ID]\n"
            "If omitted, uses IPC_INSTANCE_ID env var or defaults to 'claude'."
        )
        sys.exit(0)

    print(f"🤖 Auto-Responder for instance: {instance}")
    responder = AutoResponder(instance_id=instance)
    print(f"🛠️ policy: {responder.policy}")
    responder.run()
