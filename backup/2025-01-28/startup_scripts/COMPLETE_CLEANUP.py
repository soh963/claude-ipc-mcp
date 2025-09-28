#!/usr/bin/env python3
"""
완전한 IPC 시스템 정리 및 초기화 스크립트
- 모든 백그라운드 프로세스 종료
- 데이터베이스 초기화
- 인스턴스 및 메시지 삭제
- 세션 파일 정리
"""

import os
import sys
import subprocess
import time
import sqlite3
from pathlib import Path
import psutil
import signal
import shutil

class CompleteCleanup:
    def __init__(self):
        self.home = Path.home()
        self.ipc_data_dir = self.home / '.claude-ipc-data'
        self.db_path = self.ipc_data_dir / 'messages.db'
        self.session_file = self.home / '.ipc-session'
        self.killed_count = 0

    def step(self, message):
        """단계별 진행 상황 표시"""
        print(f"\n{'='*60}")
        print(f"[STEP] {message}")
        print('='*60)

    def kill_all_python_processes(self):
        """모든 IPC 관련 Python 프로세스 종료"""
        self.step("모든 IPC 관련 Python 프로세스 종료 중...")

        keywords = [
            'ipc', 'auto_responder', 'monitor', 'broker',
            'START_FRESH', 'start_integrated', 'simple_auto',
            'claude_ipc', 'start_safe', 'start_split'
        ]

        try:
            # psutil 사용하여 프로세스 종료
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Python 프로세스 확인
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info.get('cmdline', [])).lower()

                        # IPC 관련 프로세스 확인
                        for keyword in keywords:
                            if keyword.lower() in cmdline:
                                print(f"  종료: PID {proc.info['pid']} - {cmdline[:80]}")
                                proc.terminate()
                                self.killed_count += 1
                                time.sleep(0.1)

                                # 종료되지 않으면 강제 종료
                                if proc.is_running():
                                    proc.kill()
                                break

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    continue

        except Exception as e:
            print(f"  psutil 사용 실패, Windows taskkill 사용: {e}")

            # Windows taskkill 백업 방법
            if sys.platform == 'win32':
                for keyword in keywords:
                    try:
                        cmd = f'taskkill /F /IM python.exe /FI "WINDOWTITLE eq *{keyword}*"'
                        subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                    except:
                        pass

        print(f"  총 {self.killed_count}개 프로세스 종료됨")

    def kill_tcp_connection(self):
        """포트 9876 TCP 연결 종료"""
        self.step("TCP 포트 9876 연결 종료 중...")

        try:
            # 포트 9876 사용 프로세스 찾기
            for conn in psutil.net_connections():
                if conn.laddr.port == 9876:
                    try:
                        proc = psutil.Process(conn.pid)
                        print(f"  종료: PID {conn.pid} - 포트 9876 사용")
                        proc.terminate()
                        time.sleep(0.5)
                        if proc.is_running():
                            proc.kill()
                    except:
                        pass

        except Exception as e:
            print(f"  포트 종료 실패: {e}")

            # Windows netstat/taskkill 백업
            if sys.platform == 'win32':
                try:
                    result = subprocess.run(
                        'netstat -ano | findstr :9876',
                        shell=True, capture_output=True, text=True
                    )
                    for line in result.stdout.splitlines():
                        parts = line.split()
                        if len(parts) > 4 and parts[-1].isdigit():
                            pid = parts[-1]
                            subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                except:
                    pass

    def clean_database(self):
        """데이터베이스 완전 초기화"""
        self.step("데이터베이스 초기화 중...")

        if not self.db_path.exists():
            print(f"  데이터베이스가 없습니다: {self.db_path}")
            return

        try:
            # 데이터베이스 백업
            backup_path = self.db_path.with_suffix('.db.backup')
            shutil.copy2(self.db_path, backup_path)
            print(f"  백업 생성: {backup_path}")

            # 데이터베이스 연결 및 초기화
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 모든 데이터 삭제
            tables = [
                ('messages', '메시지'),
                ('instances', '인스턴스'),
                ('sessions', '세션'),
                ('name_history', '이름 기록')
            ]

            for table, desc in tables:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    count = cursor.rowcount
                    print(f"  {desc} 테이블 초기화: {count}개 레코드 삭제")
                except sqlite3.OperationalError:
                    print(f"  {desc} 테이블 없음")

            conn.commit()

            # VACUUM으로 데이터베이스 최적화
            cursor.execute("VACUUM")
            print("  데이터베이스 최적화 완료")

            conn.close()

        except Exception as e:
            print(f"  데이터베이스 초기화 실패: {e}")

            # 실패 시 데이터베이스 파일 삭제
            try:
                self.db_path.unlink()
                print(f"  데이터베이스 파일 삭제: {self.db_path}")
            except:
                pass

    def clean_session_files(self):
        """세션 파일 및 임시 파일 정리"""
        self.step("세션 및 임시 파일 정리 중...")

        files_to_clean = [
            self.session_file,
            self.home / '.ipc-session.json',
            Path('instances.json'),
            Path('messages.json'),
            Path('server_log.txt'),
            Path('ipc_messages.db'),
            Path('nul')  # Windows null device 파일
        ]

        for file_path in files_to_clean:
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"  삭제: {file_path}")
                except Exception as e:
                    print(f"  삭제 실패: {file_path} - {e}")

        # 임시 디렉토리 정리
        temp_dirs = [
            Path('__pycache__'),
            Path('tools/__pycache__'),
            Path('src/__pycache__')
        ]

        for dir_path in temp_dirs:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"  디렉토리 삭제: {dir_path}")
                except:
                    pass

    def verify_cleanup(self):
        """정리 완료 확인"""
        self.step("정리 완료 확인 중...")

        # 프로세스 확인
        python_count = 0
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info.get('cmdline', [])).lower()
                    if any(k in cmdline for k in ['ipc', 'auto_responder', 'monitor']):
                        python_count += 1
            except:
                pass

        print(f"  남은 IPC 프로세스: {python_count}개")

        # 포트 확인
        port_used = False
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == 9876:
                    port_used = True
                    break
        except:
            pass

        print(f"  포트 9876 상태: {'사용 중' if port_used else '사용 가능'}")

        # 데이터베이스 확인
        if self.db_path.exists():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM messages")
                msg_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM instances")
                inst_count = cursor.fetchone()[0]

                print(f"  남은 메시지: {msg_count}개")
                print(f"  남은 인스턴스: {inst_count}개")

                conn.close()
            except:
                print("  데이터베이스 확인 실패")
        else:
            print("  데이터베이스 없음 (새로 시작 가능)")

    def run(self):
        """전체 정리 프로세스 실행"""
        print("\n" + "="*60)
        print(" IPC 시스템 완전 정리 및 초기화")
        print("="*60)

        # 1. 모든 프로세스 종료
        self.kill_all_python_processes()
        time.sleep(2)

        # 2. TCP 연결 종료
        self.kill_tcp_connection()
        time.sleep(1)

        # 3. 데이터베이스 초기화
        self.clean_database()

        # 4. 세션 파일 정리
        self.clean_session_files()

        # 5. 정리 확인
        self.verify_cleanup()

        print("\n" + "="*60)
        print(" 정리 완료!")
        print(" 이제 깨끗한 상태에서 IPC 시스템을 시작할 수 있습니다.")
        print("="*60)
        print("\n다음 명령으로 시작하세요:")
        print("  python START_FRESH_SYSTEM.py")
        print("  또는")
        print("  python start_integrated_system.py")


if __name__ == "__main__":
    try:
        cleaner = CompleteCleanup()
        cleaner.run()
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n오류 발생: {e}")
        import traceback
        traceback.print_exc()