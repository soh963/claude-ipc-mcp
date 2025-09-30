#!/usr/bin/env python3
"""
Claude IPC Manager - 통합 관리 유틸리티
인스턴스 등록/삭제, 메시지 관리, 시스템 상태 확인
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime


class IPCManager:
    """IPC 통합 관리 클래스"""

    def __init__(self):
        self.db_path = Path.home() / ".claude-ipc-data" / "messages.db"
        self.instances_path = Path.home() / ".claude-ipc-data" / "instances.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        self.load_instances()

    def init_database(self):
        """데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 메시지 테이블 생성
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_id TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read INTEGER DEFAULT 0
                )
            """
            )

            # 인덱스 생성
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_to_id
                ON messages(to_id, timestamp)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_from_id
                ON messages(from_id, timestamp)
            """
            )

            conn.commit()
            conn.close()
            print("✅ 데이터베이스 초기화 완료")

        except Exception as e:
            print(f"❌ 데이터베이스 초기화 실패: {e}")
            sys.exit(1)

    def load_instances(self):
        """등록된 인스턴스 로드"""
        if self.instances_path.exists():
            with open(self.instances_path, "r", encoding="utf-8") as f:
                self.instances = json.load(f)
        else:
            self.instances = {}

    def save_instances(self):
        """인스턴스 정보 저장"""
        with open(self.instances_path, "w", encoding="utf-8") as f:
            json.dump(self.instances, f, ensure_ascii=False, indent=2)

    def register_instance(self, instance_id: str):
        """인스턴스 등록"""
        if instance_id in self.instances:
            print(f"⚠️ '{instance_id}' 인스턴스는 이미 등록되어 있습니다.")
            return False

        self.instances[instance_id] = {
            "registered_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "message_count": 0,
        }
        self.save_instances()
        print(f"✅ '{instance_id}' 인스턴스가 등록되었습니다.")
        return True

    def unregister_instance(self, instance_id: str):
        """인스턴스 삭제"""
        if instance_id not in self.instances:
            print(f"❌ '{instance_id}' 인스턴스를 찾을 수 없습니다.")
            return False

        del self.instances[instance_id]
        self.save_instances()

        # 관련 메시지도 삭제할지 확인
        response = input(f"'{instance_id}'의 모든 메시지도 삭제하시겠습니까? (y/n): ")
        if response.lower() == "y":
            self.delete_instance_messages(instance_id)

        print(f"✅ '{instance_id}' 인스턴스가 삭제되었습니다.")
        return True

    def delete_instance_messages(self, instance_id: str):
        """특정 인스턴스의 모든 메시지 삭제"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM messages
                WHERE from_id = ? OR to_id = ?
            """,
                (instance_id, instance_id),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            print(f"   📧 {deleted_count}개의 메시지가 삭제되었습니다.")

        except Exception as e:
            print(f"❌ 메시지 삭제 실패: {e}")

    def list_instances(self):
        """등록된 인스턴스 목록 표시"""
        if not self.instances:
            print("📋 등록된 인스턴스가 없습니다.")
            return

        print("\n📋 등록된 인스턴스 목록")
        print("=" * 60)

        for instance_id, info in self.instances.items():
            registered_at = datetime.fromisoformat(info["registered_at"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            print(f"  • {instance_id}")
            print(f"    등록일시: {registered_at}")
            print(f"    메시지수: {info.get('message_count', 0)}")
            print()

    def send_message(self, from_id: str, to_id: str, content: str, max_messages: int = 100):
        """메시지 전송 (메시지 제한 적용)"""
        # 빈 메시지 체크
        if not content or not content.strip():
            print("❌ 빈 메시지는 전송할 수 없습니다.")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 수신자의 현재 메시지 수 확인
            cursor.execute(
                """
                SELECT COUNT(*) FROM messages
                WHERE to_id = ?
            """,
                (to_id,),
            )

            message_count = cursor.fetchone()[0]

            # 메시지 제한 초과 시 오래된 메시지 삭제
            if message_count >= max_messages:
                # 삭제할 메시지 수 계산 (현재 개수 - 제한 + 1)
                delete_count = message_count - max_messages + 1

                # 가장 오래된 메시지들 삭제
                cursor.execute(
                    """
                    DELETE FROM messages
                    WHERE to_id = ? AND id IN (
                        SELECT id FROM messages
                        WHERE to_id = ?
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                """,
                    (to_id, to_id, delete_count),
                )

                deleted = cursor.rowcount
                if deleted > 0:
                    print(f"   🗑️ {to_id}의 오래된 메시지 {deleted}개 자동 삭제")

            # 새 메시지 삽입
            cursor.execute(
                """
                INSERT INTO messages (from_id, to_id, content, timestamp)
                VALUES (?, ?, ?, datetime('now'))
            """,
                (from_id, to_id, content),
            )

            conn.commit()
            conn.close()

            print(f"✅ 메시지 전송 완료: {from_id} → {to_id}")
            print(f"   💬 내용: {content}")

            # 인스턴스 통계 업데이트
            if from_id in self.instances:
                self.instances[from_id]["message_count"] = (
                    self.instances[from_id].get("message_count", 0) + 1
                )
                self.instances[from_id]["last_active"] = datetime.now().isoformat()
                self.save_instances()

            return True

        except Exception as e:
            print(f"❌ 메시지 전송 실패: {e}")
            return False

    def broadcast_message(self, from_id: str, content: str):
        """브로드캐스트 메시지"""
        recipients = [id for id in self.instances.keys() if id != from_id]

        if not recipients:
            print("📢 브로드캐스트할 수신자가 없습니다.")
            return

        print(f"📢 브로드캐스트 시작: {from_id} → 모든 인스턴스")

        for to_id in recipients:
            self.send_message(from_id, to_id, content)

        print(f"✅ {len(recipients)}명에게 브로드캐스트 완료")

    def check_messages(self, instance_id: str):
        """특정 인스턴스의 새 메시지 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT from_id, content, timestamp
                FROM messages
                WHERE to_id = ? AND is_read = 0
                ORDER BY timestamp ASC
            """,
                (instance_id,),
            )

            messages = cursor.fetchall()

            if not messages:
                print(f"📭 '{instance_id}'에 새 메시지가 없습니다.")
                return

            print(f"\n📬 '{instance_id}'의 새 메시지 ({len(messages)}개)")
            print("=" * 60)

            for from_id, content, timestamp in messages:
                print(f"📨 발신: {from_id}")
                print(f"   시간: {timestamp}")
                print(f"   내용: {content}")
                print()

            # 읽음 표시 업데이트
            cursor.execute(
                """
                UPDATE messages
                SET is_read = 1
                WHERE to_id = ? AND is_read = 0
            """,
                (instance_id,),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ 메시지 확인 실패: {e}")

    def show_all_messages(self):
        """모든 메시지 표시"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT from_id, to_id, content, timestamp, is_read
                FROM messages
                ORDER BY timestamp DESC
                LIMIT 50
            """
            )

            messages = cursor.fetchall()
            conn.close()

            if not messages:
                print("📭 메시지가 없습니다.")
                return

            print("\n📮 전체 메시지 (최근 50개)")
            print("=" * 60)

            for from_id, to_id, content, timestamp, is_read in messages:
                read_status = "✓" if is_read else "•"
                print(f"{read_status} [{timestamp}] {from_id} → {to_id}")
                print(f"  {content}")
                print()

        except Exception as e:
            print(f"❌ 메시지 조회 실패: {e}")

    def clear_messages(self):
        """모든 메시지 삭제"""
        response = input("⚠️ 정말 모든 메시지를 삭제하시겠습니까? (yes/no): ")

        if response.lower() != "yes":
            print("❌ 취소되었습니다.")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM messages")
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            print(f"✅ {deleted_count}개의 메시지가 삭제되었습니다.")

        except Exception as e:
            print(f"❌ 메시지 삭제 실패: {e}")

    def show_status(self):
        """시스템 상태 표시"""
        print("\n🔧 시스템 상태")
        print("=" * 60)

        # 데이터베이스 상태
        if self.db_path.exists():
            db_size = self.db_path.stat().st_size / 1024  # KB
            print(f"✅ 데이터베이스: 정상 ({db_size:.1f} KB)")
        else:
            print("❌ 데이터베이스: 없음")

        # 인스턴스 상태
        print(f"📊 등록된 인스턴스: {len(self.instances)}개")

        # 메시지 통계
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM messages WHERE is_read = 0")
            unread_messages = cursor.fetchone()[0]

            conn.close()

            print(f"📧 전체 메시지: {total_messages}개")
            print(f"📨 읽지 않은 메시지: {unread_messages}개")

        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")

    def show_stats(self):
        """상세 통계 표시"""
        print("\n📊 상세 통계")
        print("=" * 60)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 인스턴스별 발신 통계
            cursor.execute(
                """
                SELECT from_id, COUNT(*) as count
                FROM messages
                GROUP BY from_id
                ORDER BY count DESC
            """
            )

            sent_stats = cursor.fetchall()

            if sent_stats:
                print("\n📤 발신 통계")
                for instance_id, count in sent_stats:
                    print(f"  {instance_id}: {count}개")

            # 인스턴스별 수신 통계
            cursor.execute(
                """
                SELECT to_id, COUNT(*) as count
                FROM messages
                GROUP BY to_id
                ORDER BY count DESC
            """
            )

            received_stats = cursor.fetchall()

            if received_stats:
                print("\n📥 수신 통계")
                for instance_id, count in received_stats:
                    print(f"  {instance_id}: {count}개")

            # 시간대별 통계
            cursor.execute(
                """
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM messages
                GROUP BY hour
                ORDER BY hour
            """
            )

            hourly_stats = cursor.fetchall()

            if hourly_stats:
                print("\n🕐 시간대별 메시지")
                for hour, count in hourly_stats:
                    print(f"  {hour}시: {count}개")

            conn.close()

        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")

    def cleanup_messages(self, instance_id: str = None, keep_count: int = 50):
        """메시지 정리 (오래된 메시지 삭제)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if instance_id:
                # 특정 인스턴스의 메시지만 정리
                cursor.execute(
                    """
                    DELETE FROM messages
                    WHERE to_id = ? AND id NOT IN (
                        SELECT id FROM messages
                        WHERE to_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    )
                """,
                    (instance_id, instance_id, keep_count),
                )

                deleted = cursor.rowcount
                print(
                    f"✅ '{instance_id}'의 오래된 메시지 {deleted}개 삭제 (최신 {keep_count}개 유지)"
                )
            else:
                # 모든 인스턴스의 메시지 정리
                for inst_id in self.instances.keys():
                    cursor.execute(
                        """
                        DELETE FROM messages
                        WHERE to_id = ? AND id NOT IN (
                            SELECT id FROM messages
                            WHERE to_id = ?
                            ORDER BY timestamp DESC
                            LIMIT ?
                        )
                    """,
                        (inst_id, inst_id, keep_count),
                    )

                    deleted = cursor.rowcount
                    if deleted > 0:
                        print(f"  • {inst_id}: {deleted}개 삭제 (최신 {keep_count}개 유지)")

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ 메시지 정리 실패: {e}")


def print_usage():
    """사용법 출력"""
    print(
        """
Claude IPC Manager - 사용법

인스턴스 관리:
  register <instance_id>      - 인스턴스 등록
  unregister <instance_id>    - 인스턴스 삭제
  list                        - 등록된 인스턴스 목록

메시지 관리:
  send <from> <to> <message>  - 메시지 전송
  broadcast <from> <message>  - 모든 인스턴스에게 전송
  check <instance_id>         - 새 메시지 확인
  show-all                    - 모든 메시지 표시
  clear                       - 모든 메시지 삭제
  cleanup [instance_id] [count] - 오래된 메시지 정리 (기본 50개 유지)

시스템 관리:
  init                        - 데이터베이스 초기화
  status                      - 시스템 상태 확인
  stats                       - 상세 통계 표시

예시:
  python ipc_manager.py register claude
  python ipc_manager.py send claude gemini "안녕하세요!"
  python ipc_manager.py check gemini
"""
    )


def main():
    """메인 실행 함수"""
    if len(sys.argv) < 2:
        print_usage()
        return

    manager = IPCManager()
    command = sys.argv[1].lower()

    try:
        if command == "init":
            manager.init_database()

        elif command == "register" and len(sys.argv) >= 3:
            manager.register_instance(sys.argv[2])

        elif command == "unregister" and len(sys.argv) >= 3:
            manager.unregister_instance(sys.argv[2])

        elif command == "list":
            manager.list_instances()

        elif command == "send" and len(sys.argv) >= 5:
            from_id = sys.argv[2]
            to_id = sys.argv[3]
            content = " ".join(sys.argv[4:])
            manager.send_message(from_id, to_id, content)

        elif command == "broadcast" and len(sys.argv) >= 4:
            from_id = sys.argv[2]
            content = " ".join(sys.argv[3:])
            manager.broadcast_message(from_id, content)

        elif command == "check" and len(sys.argv) >= 3:
            manager.check_messages(sys.argv[2])

        elif command == "show-all":
            manager.show_all_messages()

        elif command == "clear":
            manager.clear_messages()

        elif command == "status":
            manager.show_status()

        elif command == "stats":
            manager.show_stats()

        elif command == "cleanup":
            if len(sys.argv) >= 4:
                # cleanup <instance_id> <keep_count>
                manager.cleanup_messages(sys.argv[2], int(sys.argv[3]))
            elif len(sys.argv) >= 3:
                # cleanup <instance_id>
                manager.cleanup_messages(sys.argv[2])
            else:
                # cleanup all
                manager.cleanup_messages()

        else:
            print(f"❌ 잘못된 명령어: {command}")
            print_usage()

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
