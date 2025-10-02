#!/usr/bin/env python3
"""
IPC 시스템 자동 복구 도구
모든 문제를 자동으로 감지하고 복구하는 통합 솔루션
"""

import sys
import socket
import sqlite3
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
import subprocess
import json

# 시스템 경로에 tools 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

# 내부 모듈 임포트
try:
    from db_compat import DBCompat
    from schema_validator import SchemaValidator
except ImportError:
    print("⚠️ Warning: Some repair modules not available")
    DBCompat = None
    SchemaValidator = None


class IPCAutoRepair:
    """IPC 시스템 자동 복구 클래스"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.repair_log = []
        self.issues_found = []
        self.fixes_applied = []

        # IPC 시스템 경로
        self.ipc_home = Path.home() / ".claude-ipc-data"
        self.db_path = self.ipc_home / "messages.db"
        self.session_dir = Path.home()

        # 브로커 설정
        self.broker_host = "localhost"
        self.broker_port = 9876

        # 결과 통계
        self.stats = {
            "checks_performed": 0,
            "issues_found": 0,
            "fixes_applied": 0,
            "fixes_failed": 0,
        }

    def log(self, message: str, level: str = "INFO"):
        """로그 메시지 기록"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.repair_log.append(log_entry)

        if self.verbose or level in ["ERROR", "WARNING", "SUCCESS"]:
            prefix = {
                "ERROR": "❌",
                "WARNING": "⚠️",
                "SUCCESS": "✅",
                "INFO": "ℹ️",
                "DEBUG": "🔍",
            }.get(level, "")
            print(f"{prefix} {message}")

    def check_broker_running(self) -> bool:
        """브로커 실행 상태 확인"""
        self.stats["checks_performed"] += 1
        self.log("Checking broker status...", "DEBUG")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.broker_host, self.broker_port))
            sock.close()

            if result == 0:
                self.log(f"Broker is running on {self.broker_host}:{self.broker_port}", "SUCCESS")
                return True
            else:
                self.log(f"Broker is not responding on port {self.broker_port}", "WARNING")
                self.issues_found.append("Broker not running")
                self.stats["issues_found"] += 1
                return False

        except Exception as e:
            self.log(f"Error checking broker: {e}", "ERROR")
            self.issues_found.append(f"Broker check failed: {e}")
            self.stats["issues_found"] += 1
            return False

    def start_broker(self) -> bool:
        """브로커 시작 시도"""
        self.log("Attempting to start broker...", "INFO")

        try:
            # 여러 방법으로 브로커 시작 시도
            start_commands = [
                ["python", "src/claude_ipc_server.py"],
                ["python", "tools/start_broker.py"],
                ["python", "START_STABLE_SYSTEM.py"],
            ]

            for cmd in start_commands:
                try:
                    # 백그라운드로 프로세스 시작
                    if sys.platform == "win32":
                        subprocess.Popen(
                            cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                    else:
                        # Use os.devnull to prevent 'nul' file creation
                        with open(os.devnull, 'w') as devnull:
                            subprocess.Popen(
                                cmd, shell=False, stdout=devnull, stderr=devnull
                            )

                    # 시작 대기
                    time.sleep(3)

                    # 확인
                    if self.check_broker_running():
                        self.log("Broker started successfully", "SUCCESS")
                        self.fixes_applied.append("Started broker")
                        self.stats["fixes_applied"] += 1
                        return True

                except Exception as e:
                    self.log(f"Failed to start broker with {cmd}: {e}", "DEBUG")

            self.log("Failed to start broker", "ERROR")
            self.stats["fixes_failed"] += 1
            return False

        except Exception as e:
            self.log(f"Error starting broker: {e}", "ERROR")
            self.stats["fixes_failed"] += 1
            return False

    def check_database(self) -> bool:
        """데이터베이스 상태 확인"""
        self.stats["checks_performed"] += 1
        self.log("Checking database...", "DEBUG")

        if not self.db_path.exists():
            self.log("Database file not found", "WARNING")
            self.issues_found.append("Database missing")
            self.stats["issues_found"] += 1
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 테이블 존재 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # sqlite_sequence는 자동 생성되는 테이블이므로 제외
            required_tables = ["instances", "sessions", "messages", "name_history"]
            missing_tables = set(required_tables) - set(tables)

            if missing_tables:
                self.log(f"Missing tables: {missing_tables}", "WARNING")
                self.issues_found.append(f"Missing tables: {missing_tables}")
                self.stats["issues_found"] += 1
                conn.close()
                return False

            conn.close()
            self.log("Database structure is intact", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Database error: {e}", "ERROR")
            self.issues_found.append(f"Database error: {e}")
            self.stats["issues_found"] += 1
            return False

    def validate_schema(self) -> bool:
        """스키마 검증"""
        self.stats["checks_performed"] += 1
        self.log("Validating database schema...", "DEBUG")

        if SchemaValidator:
            try:
                validator = SchemaValidator(str(self.db_path))
                is_valid = validator.validate()

                if not is_valid:
                    self.log("Schema validation failed", "WARNING")
                    self.issues_found.extend(validator.issues)
                    self.stats["issues_found"] += len(validator.issues)
                    return False

                self.log("Schema validation passed", "SUCCESS")
                return True

            except Exception as e:
                self.log(f"Schema validation error: {e}", "ERROR")
                return False
        else:
            self.log("Schema validator not available", "WARNING")
            return True

    def clean_expired_sessions(self) -> int:
        """만료된 세션 정리"""
        self.stats["checks_performed"] += 1
        self.log("Cleaning expired sessions...", "DEBUG")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 24시간 이상 된 세션 삭제
            cutoff_time = datetime.now() - timedelta(hours=24)
            cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")

            if DBCompat:
                DBCompat.safe_execute(
                    cursor, "DELETE FROM sessions WHERE expires_at < ?", (cutoff_str,)
                )
            else:
                cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (cutoff_str,))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted > 0:
                self.log(f"Cleaned {deleted} expired sessions", "SUCCESS")
                self.fixes_applied.append(f"Cleaned {deleted} expired sessions")
                self.stats["fixes_applied"] += 1

            return deleted

        except Exception as e:
            self.log(f"Error cleaning sessions: {e}", "ERROR")
            self.stats["fixes_failed"] += 1
            return 0

    def clean_old_messages(self) -> int:
        """오래된 메시지 정리"""
        self.stats["checks_performed"] += 1
        self.log("Cleaning old messages...", "DEBUG")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 7일 이상 된 읽은 메시지 삭제
            cutoff_time = datetime.now() - timedelta(days=7)
            cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                "DELETE FROM messages WHERE read_flag = 1 AND timestamp < ?", (cutoff_str,)
            )

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted > 0:
                self.log(f"Cleaned {deleted} old messages", "SUCCESS")
                self.fixes_applied.append(f"Cleaned {deleted} old messages")
                self.stats["fixes_applied"] += 1

            return deleted

        except Exception as e:
            self.log(f"Error cleaning messages: {e}", "ERROR")
            self.stats["fixes_failed"] += 1
            return 0

    def clean_session_files(self) -> int:
        """세션 파일 정리"""
        self.stats["checks_performed"] += 1
        self.log("Cleaning session files...", "DEBUG")

        cleaned = 0
        try:
            # ~/.ipc-session* 파일들 찾기
            session_files = list(self.session_dir.glob(".ipc-session*"))

            for session_file in session_files:
                try:
                    # 24시간 이상 된 파일 삭제
                    file_age = time.time() - session_file.stat().st_mtime
                    if file_age > 86400:  # 24시간
                        session_file.unlink()
                        cleaned += 1
                        self.log(f"Removed old session file: {session_file.name}", "DEBUG")
                except Exception as e:
                    self.log(f"Error removing {session_file}: {e}", "DEBUG")

            if cleaned > 0:
                self.log(f"Cleaned {cleaned} old session files", "SUCCESS")
                self.fixes_applied.append(f"Cleaned {cleaned} session files")
                self.stats["fixes_applied"] += 1

            return cleaned

        except Exception as e:
            self.log(f"Error cleaning session files: {e}", "ERROR")
            return 0

    def test_ipc_communication(self) -> bool:
        """IPC 통신 테스트"""
        self.stats["checks_performed"] += 1
        self.log("Testing IPC communication...", "DEBUG")

        try:
            # 테스트 인스턴스 등록
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.broker_host, self.broker_port))

            # 테스트 인스턴스 등록
            test_id = f"repair_test_{int(time.time())}"
            request = json.dumps({"action": "register", "instance_id": test_id})
            sock.send(request.encode())

            response = sock.recv(4096).decode()
            sock.close()

            if response:
                result = json.loads(response)
                # register는 session_token을 반환하면 성공
                if "session_token" in result:
                    self.log(f"IPC communication test passed (registered as {test_id})", "SUCCESS")
                    return True
                elif result.get("status") == "success":
                    self.log("IPC communication test passed", "SUCCESS")
                    return True

            self.log("IPC communication test failed", "WARNING")
            self.issues_found.append("IPC communication failed")
            self.stats["issues_found"] += 1
            return False

        except Exception as e:
            self.log(f"IPC test error: {e}", "ERROR")
            self.issues_found.append(f"IPC test failed: {e}")
            self.stats["issues_found"] += 1
            return False

    def run_full_repair(self) -> Dict:
        """전체 복구 프로세스 실행"""
        print("🔧 IPC Auto-Repair System")
        print("=" * 60)
        print("Starting comprehensive system check and repair...")
        print()

        start_time = time.time()

        # 1. 브로커 확인 및 시작
        print("Step 1: Checking message broker...")
        if not self.check_broker_running():
            self.start_broker()

        # 2. 데이터베이스 확인
        print("\nStep 2: Checking database...")
        self.check_database()

        # 3. 스키마 검증
        print("\nStep 3: Validating schema...")
        self.validate_schema()

        # 4. 세션 정리
        print("\nStep 4: Cleaning expired sessions...")
        self.clean_expired_sessions()

        # 5. 메시지 정리
        print("\nStep 5: Cleaning old messages...")
        self.clean_old_messages()

        # 6. 세션 파일 정리
        print("\nStep 6: Cleaning session files...")
        self.clean_session_files()

        # 7. 통신 테스트
        print("\nStep 7: Testing IPC communication...")
        self.test_ipc_communication()

        elapsed_time = time.time() - start_time

        # 결과 리포트 생성
        report = self.generate_report(elapsed_time)
        self.print_report(report)

        return report

    def generate_report(self, elapsed_time: float) -> Dict:
        """복구 리포트 생성"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_time": f"{elapsed_time:.2f} seconds",
            "statistics": self.stats,
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "status": "SUCCESS" if self.stats["issues_found"] == 0 else "PARTIAL",
            "log": self.repair_log if self.verbose else [],
        }

        return report

    def print_report(self, report: Dict):
        """리포트 출력"""
        print("\n" + "=" * 60)
        print("📊 REPAIR REPORT")
        print("=" * 60)

        print(f"Time: {report['elapsed_time']}")
        print(f"Status: {report['status']}")
        print()

        print("Statistics:")
        for key, value in report["statistics"].items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")

        if report["issues_found"]:
            print("\n⚠️ Issues Found:")
            for issue in report["issues_found"]:
                print(f"  • {issue}")

        if report["fixes_applied"]:
            print("\n✅ Fixes Applied:")
            for fix in report["fixes_applied"]:
                print(f"  • {fix}")

        print("\n" + "=" * 60)

        if report["status"] == "SUCCESS":
            print("✨ IPC system is healthy and operational!")
        else:
            print("⚠️ Some issues remain. Manual intervention may be required.")

    def save_report(self, report: Dict, filename: Optional[str] = None) -> str:
        """리포트를 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ipc_repair_report_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Report saved to: {filename}")
        return filename


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="IPC System Auto-Repair Tool")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--save-report", "-s", type=str, help="Save report to file")
    parser.add_argument(
        "--quick", "-q", action="store_true", help="Quick repair (skip deep checks)"
    )

    args = parser.parse_args()

    # 복구 도구 실행
    repairer = IPCAutoRepair(verbose=args.verbose)
    report = repairer.run_full_repair()

    # 리포트 저장
    if args.save_report:
        repairer.save_report(report, args.save_report)

    # 종료 코드
    sys.exit(0 if report["status"] == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
